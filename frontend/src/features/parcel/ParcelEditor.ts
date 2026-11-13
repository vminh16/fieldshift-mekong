import maplibregl, { type GeoJSONSource, type Map as MlMap, type MapMouseEvent, type Marker } from 'maplibre-gl'
import { formatHa, ringAreaM2, ringCentroid, wouldSelfIntersect } from '../../shared/geo/area'

export type LngLat = [number, number]
export type DrawMode = 'polygon' | 'point'

export interface EditorState {
  mode: DrawMode
  ring: LngLat[]
  closed: boolean
  point: LngLat | null
}

/** Below this zoom one screen pixel is several metres — too coarse to trace a paddy edge. */
export const MIN_DRAW_ZOOM = 15
/** Area the planning API accepts (POST /v1/fields: lat 8–11.5, lon 104–107.5). */
export const inServiceArea = ([lng, lat]: LngLat) => lat >= 8 && lat <= 11.5 && lng >= 104 && lng <= 107.5
export const OUTSIDE_MSG = 'Mô hình hiện chỉ hỗ trợ Đồng bằng sông Cửu Long (vĩ độ 8–11,5° B, kinh độ 104–107,5° Đ).'

const EMPTY: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] }
const fc = (features: GeoJSON.Feature[]): GeoJSON.FeatureCollection => ({ type: 'FeatureCollection', features })

function shape(ring: LngLat[], closed: boolean): GeoJSON.FeatureCollection {
  if (closed && ring.length >= 3) return fc([{ type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [[...ring, ring[0]]] } }])
  if (ring.length >= 2) return fc([{ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: ring } }])
  return EMPTY
}

/** Do any two non-adjacent edges cross? `closed` adds the last→first edge. */
export function selfCrosses(ring: LngLat[], closed: boolean): boolean {
  const n = ring.length
  if (n < 4) return false
  const edges = closed ? n : n - 1
  const o = (p: LngLat, q: LngLat, r: LngLat) => Math.sign((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))
  for (let i = 0; i < edges; i++) {
    const a = ring[i]
    const b = ring[(i + 1) % n]
    for (let j = i + 2; j < edges; j++) {
      if (closed && i === 0 && j === n - 1) continue
      const c = ring[j]
      const d = ring[(j + 1) % n]
      if (o(a, b, c) * o(a, b, d) < 0 && o(c, d, a) * o(c, d, b) < 0) return true
    }
  }
  return false
}

function handle(className: string, label: string): HTMLButtonElement {
  const el = document.createElement('button')
  el.type = 'button'
  el.className = className
  el.setAttribute('aria-label', label)
  return el
}

const PIN_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-6.5-6.2-6.5-11a6.5 6.5 0 0 1 13 0c0 4.8-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.4"/></svg>'

/**
 * Draws and edits one parcel on an existing MapLibre map. Imperative on purpose (like EarthRenderer):
 * handles live as DOM markers and drag updates go straight to the map, so React only re-renders the panel.
 * Call `attach()` after the map's 'load' event.
 */
export class ParcelEditor {
  private state: EditorState = { mode: 'polygon', ring: [], closed: false, point: null }
  private markers: Marker[] = []
  private active = false
  private locked = false

  constructor(
    private map: MlMap,
    private cb: { onChange: (s: EditorState) => void; onNotice: (msg: string) => void },
  ) {}

  attach() {
    const map = this.map
    map.addSource('edit-shape', { type: 'geojson', data: EMPTY })
    map.addSource('edit-draft', { type: 'geojson', data: EMPTY })
    map.addLayer({ id: 'edit-fill', type: 'fill', source: 'edit-shape', filter: ['==', '$type', 'Polygon'], paint: { 'fill-color': '#a6d388', 'fill-opacity': 0.16 } })
    map.addLayer({ id: 'edit-casing', type: 'line', source: 'edit-shape', paint: { 'line-color': '#0d0f0e', 'line-width': 4, 'line-opacity': 0.5 } })
    map.addLayer({ id: 'edit-line', type: 'line', source: 'edit-shape', paint: { 'line-color': '#c2e3a8', 'line-width': 2 } })
    map.addLayer({ id: 'edit-draft', type: 'line', source: 'edit-draft', paint: { 'line-color': '#c2e3a8', 'line-width': 1.5, 'line-dasharray': [2, 2] } })
    map.on('click', this.onClick)
    map.on('mousemove', this.onMove)
  }

  get snapshot(): EditorState {
    return this.state
  }

  get areaHa(): number {
    return this.state.closed ? ringAreaM2(this.state.ring) / 10_000 : 0
  }

  get isActive() {
    return this.active
  }

  start(initial?: Partial<EditorState>) {
    this.active = true
    this.locked = false
    this.state = { mode: 'polygon', ring: [], closed: false, point: null, ...initial }
    this.map.getCanvas().style.cursor = 'crosshair'
    this.render()
  }

  stop() {
    this.active = false
    this.state = { mode: 'polygon', ring: [], closed: false, point: null }
    this.map.getCanvas().style.cursor = ''
    this.render()
  }

  /** Freeze handles while the user names the parcel. */
  lock(locked: boolean) {
    this.locked = locked
    this.map.getCanvas().style.cursor = locked ? '' : 'crosshair'
    this.render()
  }

  setMode(mode: DrawMode) {
    if (mode === this.state.mode) return
    this.state = { mode, ring: [], closed: false, point: null }
    this.render()
  }

  undo() {
    const s = this.state
    if (s.mode === 'point') this.state = { ...s, point: null }
    else if (s.closed) this.state = { ...s, closed: false }
    else this.state = { ...s, ring: s.ring.slice(0, -1) }
    this.render()
  }

  clear() {
    this.state = { ...this.state, ring: [], closed: false, point: null }
    this.render()
  }

  close() {
    const r = this.state.ring
    if (r.length < 3) return this.cb.onNotice('Cần ít nhất 3 góc để thành một thửa.')
    if (selfCrosses(r, true)) return this.cb.onNotice('Không thể đóng: cạnh cuối sẽ cắt qua đường viền.')
    this.state = { ...this.state, closed: true }
    this.render()
  }

  destroy() {
    this.map.off('click', this.onClick)
    this.map.off('mousemove', this.onMove)
    this.markers.forEach((m) => m.remove())
  }

  // ---------- events ----------
  private onClick = (e: MapMouseEvent) => {
    if (!this.active || this.locked) return
    if (this.map.getZoom() < MIN_DRAW_ZOOM) return this.cb.onNotice('Phóng to tới đúng thửa ruộng (thấy rõ bờ) rồi mới bắt đầu chấm.')
    this.placeAt([e.lngLat.lng, e.lngLat.lat])
  }

  /** Add a corner (outline mode) or set the pin (point mode) — from a map click or a GPS fix. Returns true if accepted. */
  placeAt(p: LngLat): boolean {
    const s = this.state
    if (!this.active || this.locked) return false
    if (!inServiceArea(p)) {
      this.cb.onNotice(OUTSIDE_MSG)
      return false
    }
    if (s.mode === 'point') {
      this.state = { ...s, point: p }
      this.render()
      return true
    }
    if (s.closed) {
      this.cb.onNotice('Vùng đã đóng. Bấm Hoàn tác để mở lại nếu muốn thêm góc.')
      return false
    }
    if (wouldSelfIntersect(s.ring, p)) {
      this.cb.onNotice('Đường viền không được tự cắt nhau. Chấm điểm khác.')
      return false
    }
    this.state = { ...s, ring: [...s.ring, p] }
    this.render()
    return true
  }

  private onMove = (e: MapMouseEvent) => {
    const s = this.state
    const src = this.map.getSource('edit-draft') as GeoJSONSource | undefined
    if (!src) return
    if (!this.active || this.locked || s.mode !== 'polygon' || s.closed || s.ring.length === 0) return src.setData(EMPTY)
    const last = s.ring[s.ring.length - 1]
    src.setData(fc([{ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: [last, [e.lngLat.lng, e.lngLat.lat]] } }]))
  }

  // ---------- drawing ----------
  private setShape(data: GeoJSON.FeatureCollection) {
    ;(this.map.getSource('edit-shape') as GeoJSONSource | undefined)?.setData(data)
  }

  private render() {
    const { map } = this
    const s = this.state
    this.setShape(this.active && s.mode === 'polygon' ? shape(s.ring, s.closed) : EMPTY)
    if (!this.active || s.closed || s.mode === 'point' || this.locked) (map.getSource('edit-draft') as GeoJSONSource | undefined)?.setData(EMPTY)

    this.markers.forEach((m) => m.remove())
    this.markers = []
    if (this.active) {
      const editable = !this.locked
      if (s.mode === 'point' && s.point) this.addPin(s.point, editable)
      if (s.mode === 'polygon') {
        s.ring.forEach((v, i) => this.addVertex(v, i, editable))
        if (s.closed && editable) s.ring.forEach((a, i) => this.addMidpoint(a, s.ring[(i + 1) % s.ring.length], i))
        if (s.closed) this.addAreaTag()
      }
    }
    this.cb.onChange(this.state)
  }

  private addPin(point: LngLat, draggable: boolean) {
    const el = handle('edit-pin', 'Vị trí thửa — kéo để chỉnh')
    el.innerHTML = PIN_SVG
    const m = new maplibregl.Marker({ element: el, anchor: 'bottom', draggable }).setLngLat(point).addTo(this.map)
    m.on('dragend', () => {
      const ll = m.getLngLat()
      const p: LngLat = [ll.lng, ll.lat]
      if (inServiceArea(p)) this.state = { ...this.state, point: p }
      else this.cb.onNotice(OUTSIDE_MSG)
      this.render()
    })
    this.markers.push(m)
  }

  private addVertex(v: LngLat, i: number, draggable: boolean) {
    const s = this.state
    const closer = i === 0 && !s.closed && s.ring.length >= 3
    const el = handle(`edit-vertex${closer ? ' edit-vertex--closer' : ''}`, closer ? 'Đóng vùng tại góc đầu' : `Góc ${i + 1} — kéo để chỉnh`)
    const m = new maplibregl.Marker({ element: el, draggable }).setLngLat(v).addTo(this.map)
    el.addEventListener('click', (e) => {
      e.stopPropagation()
      if (closer && !this.locked) this.close()
    })
    // While dragging, write straight to the source; commit on release.
    m.on('drag', () => {
      const ll = m.getLngLat()
      this.setShape(shape(this.state.ring.map((p, j) => (j === i ? [ll.lng, ll.lat] : p)), this.state.closed))
    })
    m.on('dragend', () => {
      const ll = m.getLngLat()
      const moved: LngLat = [ll.lng, ll.lat]
      const next = this.state.ring.map((p, j) => (j === i ? moved : p))
      if (!inServiceArea(moved)) this.cb.onNotice(OUTSIDE_MSG)
      else if (selfCrosses(next, this.state.closed)) this.cb.onNotice('Đường viền không được tự cắt nhau.')
      else this.state = { ...this.state, ring: next }
      this.render()
    })
    this.markers.push(m)
  }

  private addMidpoint(a: LngLat, b: LngLat, i: number) {
    const mid: LngLat = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
    const el = handle('edit-midpoint', 'Thêm góc ở đây')
    el.addEventListener('click', (e) => {
      e.stopPropagation()
      const ring = [...this.state.ring]
      ring.splice(i + 1, 0, mid)
      this.state = { ...this.state, ring }
      this.render()
    })
    this.markers.push(new maplibregl.Marker({ element: el }).setLngLat(mid).addTo(this.map))
  }

  private addAreaTag() {
    const c = ringCentroid(this.state.ring)
    const el = document.createElement('div')
    el.className = 'edit-area'
    el.textContent = formatHa(this.areaHa)
    this.markers.push(new maplibregl.Marker({ element: el }).setLngLat([c.lng, c.lat]).addTo(this.map))
  }
}
