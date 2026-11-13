import { useEffect, useMemo, useRef, useState } from 'react'
import maplibregl, { type GeoJSONSource, type Map as MlMap, type Marker } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { AppShell } from '../shell/AppShell'
import { Icon } from '../../shared/ui/Icon'
import { href, navigate } from '../../shared/router'
import { IMAGERY_ATTRIBUTION, IMAGERY_TILES, LABEL_TILES } from '../../shared/geo/tiles'
import { formatHa, ringAreaM2, ringCentroid, wouldSelfIntersect } from '../../shared/geo/area'
import { MEKONG_REGION } from '../../shared/geo/mekongProvinces'
import { upsertField, type LocalField } from '../../shared/fields/store'
import './parcel.css'

type LngLat = [number, number]
type Mode = 'polygon' | 'point'
type Step = 'locate' | 'name'

/** Below this zoom one screen pixel is several metres — too coarse to trace a paddy edge. */
const MIN_DRAW_ZOOM = 15
const DRAW_ZOOM = 16.8
/** Area the planning API accepts (POST /v1/fields: lat 8–11.5, lon 104–107.5). */
const inServiceArea = ([lng, lat]: LngLat) => lat >= 8 && lat <= 11.5 && lng >= 104 && lng <= 107.5
const OUTSIDE_MSG = 'Mô hình hiện chỉ hỗ trợ Đồng bằng sông Cửu Long (vĩ độ 8–11,5° B, kinh độ 104–107,5° Đ).'
/** Larger than any household paddy in the delta — likely a mis-drawn outline. */
const LARGE_HA = 30

export interface InitialView {
  lat: number
  lng: number
  zoom: number
  place: string
}

const featureCollection = (features: GeoJSON.Feature[]): GeoJSON.FeatureCollection => ({ type: 'FeatureCollection', features })

function parcelFeatures(ring: LngLat[], closed: boolean): GeoJSON.FeatureCollection {
  if (closed && ring.length >= 3) {
    return featureCollection([{ type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [[...ring, ring[0]]] } }])
  }
  if (ring.length >= 2) {
    return featureCollection([{ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: ring } }])
  }
  return featureCollection([])
}

function markerEl(className: string, label: string): HTMLButtonElement {
  const el = document.createElement('button')
  el.type = 'button'
  el.className = className
  el.setAttribute('aria-label', label)
  return el
}

export function ParcelDrawScreen({ initial, editing }: { initial: InitialView; editing?: LocalField }) {
  const hostRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MlMap | null>(null)
  const markersRef = useRef<Marker[]>([])

  const [mode, setMode] = useState<Mode>(editing && !editing.ring ? 'point' : 'polygon')
  const [ring, setRing] = useState<LngLat[]>(editing?.ring ?? [])
  const [closed, setClosed] = useState(Boolean(editing?.ring))
  const [point, setPoint] = useState<LngLat | null>(editing && !editing.ring ? [editing.centroid.lng, editing.centroid.lat] : null)
  const [zoom, setZoom] = useState(initial.zoom)
  const [step, setStep] = useState<Step>('locate')
  const [name, setName] = useState(editing?.name ?? '')
  const [reportedHa, setReportedHa] = useState(editing?.area_source === 'reported' && editing.area_ha ? String(editing.area_ha) : '')
  const [notice, setNotice] = useState<string | null>(null)
  const [locating, setLocating] = useState(false)

  // Event handlers registered once read the latest state through this ref.
  const live = useRef({ mode, ring, closed, step })
  live.current = { mode, ring, closed, step }

  const areaHa = useMemo(() => (closed ? ringAreaM2(ring) / 10_000 : 0), [ring, closed])
  const canDraw = zoom >= MIN_DRAW_ZOOM
  const located = mode === 'polygon' ? closed : point !== null

  const noticeTimer = useRef(0)
  const flash = (msg: string) => {
    setNotice(msg)
    window.clearTimeout(noticeTimer.current)
    noticeTimer.current = window.setTimeout(() => setNotice(null), 4200)
  }

  // ---------- map ----------
  useEffect(() => {
    const map = new maplibregl.Map({
      container: hostRef.current!,
      style: {
        version: 8,
        sources: {
          imagery: { type: 'raster', tiles: [IMAGERY_TILES], tileSize: 256, maxzoom: 19, attribution: IMAGERY_ATTRIBUTION },
          labels: { type: 'raster', tiles: [LABEL_TILES], tileSize: 256, maxzoom: 19 },
          parcel: { type: 'geojson', data: featureCollection([]) },
          draft: { type: 'geojson', data: featureCollection([]) },
        },
        layers: [
          { id: 'imagery', type: 'raster', source: 'imagery' },
          { id: 'labels', type: 'raster', source: 'labels', paint: { 'raster-opacity': 0.75 } },
          { id: 'parcel-fill', type: 'fill', source: 'parcel', filter: ['==', '$type', 'Polygon'], paint: { 'fill-color': '#4fd8b4', 'fill-opacity': 0.22 } },
          { id: 'parcel-casing', type: 'line', source: 'parcel', paint: { 'line-color': '#062019', 'line-width': 5, 'line-opacity': 0.55 } },
          { id: 'parcel-line', type: 'line', source: 'parcel', paint: { 'line-color': '#7be6c8', 'line-width': 2.5 } },
          { id: 'draft-line', type: 'line', source: 'draft', paint: { 'line-color': '#7be6c8', 'line-width': 2, 'line-dasharray': [2, 2] } },
        ],
      },
      center: [initial.lng, initial.lat],
      zoom: initial.zoom,
      maxZoom: 19.5,
      attributionControl: { compact: true },
      dragRotate: false,
      pitchWithRotate: false,
      doubleClickZoom: false,
    })
    map.touchZoomRotate.disableRotation()
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right')
    map.getCanvas().style.cursor = 'crosshair'
    mapRef.current = map

    map.on('zoom', () => setZoom(map.getZoom()))

    map.on('click', (e) => {
      const s = live.current
      if (s.step !== 'locate') return
      const p: LngLat = [e.lngLat.lng, e.lngLat.lat]
      if (map.getZoom() < MIN_DRAW_ZOOM) return flash('Phóng to tới đúng thửa ruộng (bờ ruộng thấy rõ) rồi mới bắt đầu chấm.')
      if (!inServiceArea(p)) return flash(OUTSIDE_MSG)
      if (s.mode === 'point') return setPoint(p)
      if (s.closed) return
      if (wouldSelfIntersect(s.ring, p)) return flash('Đường viền không được tự cắt nhau. Chấm điểm khác.')
      setRing([...s.ring, p])
    })

    map.on('mousemove', (e) => {
      const s = live.current
      const src = map.getSource('draft') as GeoJSONSource | undefined
      if (!src) return
      if (s.mode !== 'polygon' || s.closed || s.ring.length === 0 || s.step !== 'locate') return src.setData(featureCollection([]))
      const last = s.ring[s.ring.length - 1]
      src.setData(
        featureCollection([{ type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: [last, [e.lngLat.lng, e.lngLat.lat]] } }]),
      )
    })

    if (editing?.ring) {
      const lngs = editing.ring.map((p) => p[0])
      const lats = editing.ring.map((p) => p[1])
      map.fitBounds(
        [
          [Math.min(...lngs), Math.min(...lats)],
          [Math.max(...lngs), Math.max(...lats)],
        ],
        { padding: 120, maxZoom: 18, duration: 0 },
      )
    }

    return () => {
      markersRef.current.forEach((m) => m.remove())
      map.remove()
      mapRef.current = null
    }
    // The map is created once; `initial`/`editing` only seed it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ---------- geometry + handles ----------
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const draw = () => {
      ;(map.getSource('parcel') as GeoJSONSource | undefined)?.setData(mode === 'polygon' ? parcelFeatures(ring, closed) : featureCollection([]))
      if (closed || mode === 'point') (map.getSource('draft') as GeoJSONSource | undefined)?.setData(featureCollection([]))
    }
    // isStyleLoaded() is false while tiles stream in (after 'load' already fired), so test the source itself.
    if (map.getSource('parcel')) draw()
    else map.once('load', draw)

    markersRef.current.forEach((m) => m.remove())
    const markers: Marker[] = []
    const editable = step === 'locate'

    if (mode === 'point' && point) {
      const el = markerEl('parcel-pin', 'Vị trí thửa — kéo để chỉnh')
      el.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-6.5-6.2-6.5-11a6.5 6.5 0 0 1 13 0c0 4.8-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.5"/></svg>'
      const m = new maplibregl.Marker({ element: el, anchor: 'bottom', draggable: editable }).setLngLat(point).addTo(map)
      m.on('dragend', () => {
        const ll = m.getLngLat()
        const p: LngLat = [ll.lng, ll.lat]
        if (inServiceArea(p)) setPoint(p)
        else {
          m.setLngLat(point)
          flash(OUTSIDE_MSG)
        }
      })
      markers.push(m)
    }

    if (mode === 'polygon') {
      ring.forEach((v, i) => {
        const first = i === 0 && !closed && ring.length >= 3
        const el = markerEl(`vertex${first ? ' vertex--close' : ''}`, first ? 'Đóng vùng tại điểm đầu' : `Góc ${i + 1} — kéo để chỉnh`)
        const m = new maplibregl.Marker({ element: el, draggable: editable }).setLngLat(v).addTo(map)
        el.addEventListener('click', (e) => {
          e.stopPropagation()
          if (first) closeRing()
        })
        // While dragging, write straight to the map source; commit to React state on release.
        m.on('drag', () => {
          const ll = m.getLngLat()
          const next = ring.map((p, j) => (j === i ? ([ll.lng, ll.lat] as LngLat) : p))
          ;(map.getSource('parcel') as GeoJSONSource).setData(parcelFeatures(next, closed))
        })
        m.on('dragend', () => {
          const ll = m.getLngLat()
          const moved: LngLat = [ll.lng, ll.lat]
          const next = ring.map((p, j) => (j === i ? moved : p))
          const crosses = selfCrossAny(next, closed)
          if (!inServiceArea(moved) || crosses) {
            flash(crosses ? 'Đường viền không được tự cắt nhau.' : OUTSIDE_MSG)
            setRing([...ring]) // re-render handles at their old positions
            return
          }
          setRing(next)
        })
        markers.push(m)
      })

      // Midpoint handles: click to add a corner between two existing ones.
      if (closed && editable) {
        ring.forEach((a, i) => {
          const b = ring[(i + 1) % ring.length]
          const mid: LngLat = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
          const el = markerEl('midpoint', 'Thêm góc ở đây')
          el.addEventListener('click', (e) => {
            e.stopPropagation()
            const next = [...ring]
            next.splice(i + 1, 0, mid)
            setRing(next)
          })
          markers.push(new maplibregl.Marker({ element: el }).setLngLat(mid).addTo(map))
        })
      }

      if (closed) {
        const c = ringCentroid(ring)
        const el = document.createElement('div')
        el.className = 'area-tag'
        el.textContent = formatHa(ringAreaM2(ring) / 10_000)
        markers.push(new maplibregl.Marker({ element: el }).setLngLat([c.lng, c.lat]).addTo(map))
      }
    }
    markersRef.current = markers
    // closeRing reads current ring via closure; recreated with it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ring, closed, point, mode, step])

  function closeRing() {
    const r = live.current.ring
    if (r.length < 3) return flash('Cần ít nhất 3 góc để thành một thửa.')
    if (selfCrossAny(r, true)) return flash('Không thể đóng: cạnh cuối sẽ cắt qua đường viền.')
    setClosed(true)
  }

  function undo() {
    if (mode === 'point') return setPoint(null)
    if (closed) return setClosed(false)
    setRing(ring.slice(0, -1))
  }

  function clearAll() {
    setRing([])
    setClosed(false)
    setPoint(null)
  }

  // Keyboard: Enter closes, Backspace undoes, Esc clears — skipped while typing in a field.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (live.current.step !== 'locate') return
      const t = e.target as HTMLElement
      if (t.closest('input, select, textarea')) return
      if (e.key === 'Enter') closeRing()
      else if (e.key === 'Backspace' || (e.key === 'z' && (e.ctrlKey || e.metaKey))) {
        e.preventDefault()
        undo()
      } else if (e.key === 'Escape') clearAll()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  const zoomToDraw = () => mapRef.current?.easeTo({ zoom: DRAW_ZOOM, duration: 900 })

  const locateMe = () => {
    if (!('geolocation' in navigator)) return flash('Trình duyệt không hỗ trợ định vị.')
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false)
        const p: LngLat = [pos.coords.longitude, pos.coords.latitude]
        if (!inServiceArea(p)) flash(`Bạn đang ở ngoài vùng hỗ trợ. ${OUTSIDE_MSG}`)
        mapRef.current?.flyTo({ center: p, zoom: Math.max(DRAW_ZOOM, mapRef.current.getZoom()), duration: 1400 })
      },
      () => {
        setLocating(false)
        flash('Không lấy được vị trí. Kiểm tra quyền định vị của trình duyệt.')
      },
      { enableHighAccuracy: true, timeout: 10_000 },
    )
  }

  const switchMode = (m: Mode) => {
    if (m === mode) return
    clearAll()
    setMode(m)
  }

  const save = () => {
    const trimmed = name.trim()
    if (!trimmed) return flash('Đặt tên cho thửa để dễ nhận ra sau này.')
    const reported = reportedHa.trim() === '' ? null : Number(reportedHa.replace(',', '.'))
    if (reported !== null && (!Number.isFinite(reported) || reported <= 0)) return flash('Diện tích phải là số lớn hơn 0.')
    const centroid = mode === 'polygon' ? ringCentroid(ring) : { lng: point![0], lat: point![1] }
    const saved = upsertField({
      id: editing?.id,
      name: trimmed,
      ring: mode === 'polygon' ? ring : null,
      centroid,
      area_ha: mode === 'polygon' ? Math.round(areaHa * 1000) / 1000 : reported,
      area_source: mode === 'polygon' ? 'drawn' : reported !== null ? 'reported' : null,
      place_name: editing?.place_name ?? initial.place,
    })
    navigate('/ruong', { chon: saved.id, moi: editing ? null : 1 })
  }

  const instruction =
    mode === 'point'
      ? point
        ? 'Kéo ghim để chỉnh. Ghim nên nằm giữa thửa.'
        : 'Bấm vào giữa thửa ruộng để ghim vị trí.'
      : closed
        ? 'Kéo các góc để khớp bờ ruộng. Bấm chấm nhỏ giữa cạnh để thêm góc.'
        : ring.length === 0
          ? 'Bấm lần lượt vào các góc ruộng, đi theo bờ.'
          : ring.length < 3
            ? `Đã chấm ${ring.length} góc. Chấm tiếp các góc còn lại.`
            : 'Bấm vào góc đầu tiên (hoặc nhấn Enter) để đóng vùng.'

  return (
    <AppShell
      bleed
      crumbs={[{ label: 'Ruộng của tôi', to: href('/ruong') }, { label: editing ? `Sửa ranh giới · ${editing.name}` : 'Thêm thửa mới' }]}
      actions={
        <a className="btn btn--ghost btn--sm" href={href('/ruong')}>
          Huỷ
        </a>
      }
    >
      <div className="parcel">
        <div ref={hostRef} className="parcel__map" data-drawing={step === 'locate' || undefined} />

        <div className="parcel__tools" role="toolbar" aria-label="Công cụ bản đồ">
          <button type="button" className="map-btn" onClick={locateMe} aria-label="Đến vị trí của tôi" title="Đến vị trí của tôi" disabled={locating}>
            <Icon name="locate" />
          </button>
        </div>

        {!canDraw && step === 'locate' && (
          <div className="zoom-gate" role="status">
            <Icon name="zoomIn" />
            <span>Phóng to tới thửa ruộng của bạn để bắt đầu khoanh</span>
            <button type="button" className="btn btn--primary btn--sm" onClick={zoomToDraw}>
              Phóng to
            </button>
          </div>
        )}

        {notice && (
          <div className="parcel__notice" role="alert">
            {notice}
          </div>
        )}

        <section className="parcel-panel" aria-label="Khoanh thửa ruộng">
          <ol className="parcel-panel__steps" aria-label="Tiến độ">
            <li aria-current={step === 'locate' ? 'step' : undefined} data-done={step === 'name' || undefined}>
              <span>1</span> Vị trí
            </li>
            <li aria-current={step === 'name' ? 'step' : undefined}>
              <span>2</span> Đặt tên & lưu
            </li>
          </ol>

          {step === 'locate' ? (
            <>
              <h1 className="parcel-panel__title">{editing ? 'Chỉnh ranh giới thửa' : 'Khoanh thửa ruộng'}</h1>
              <div className="segmented" role="radiogroup" aria-label="Cách định vị">
                <button type="button" role="radio" aria-checked={mode === 'polygon'} onClick={() => switchMode('polygon')}>
                  <Icon name="polygon" /> Khoanh vùng
                </button>
                <button type="button" role="radio" aria-checked={mode === 'point'} onClick={() => switchMode('point')}>
                  <Icon name="pin" /> Chấm điểm
                </button>
              </div>
              <p className="parcel-panel__hint" aria-live="polite">
                {instruction}
              </p>

              {mode === 'polygon' && (
                <dl className="parcel-panel__stats">
                  <div>
                    <dt>Số góc</dt>
                    <dd>{ring.length}</dd>
                  </div>
                  <div>
                    <dt>Diện tích</dt>
                    <dd>
                      {closed ? formatHa(areaHa) : '—'}
                      {closed && <span className="evidence-chip">Ước lượng</span>}
                    </dd>
                  </div>
                </dl>
              )}
              {closed && areaHa > LARGE_HA && <p className="parcel-panel__warn">Thửa lớn hơn {LARGE_HA} ha — kiểm tra lại các góc.</p>}

              <div className="parcel-panel__row">
                <button type="button" className="btn btn--ghost btn--sm" onClick={undo} disabled={mode === 'polygon' ? ring.length === 0 : !point}>
                  <Icon name="undo" /> Hoàn tác
                </button>
                {mode === 'polygon' && !closed && ring.length >= 3 && (
                  <button type="button" className="btn btn--ghost btn--sm" onClick={closeRing}>
                    <Icon name="check" /> Đóng vùng
                  </button>
                )}
                {(ring.length > 0 || point) && (
                  <button type="button" className="btn btn--ghost btn--sm" onClick={clearAll}>
                    Xoá hết
                  </button>
                )}
              </div>
              <button type="button" className="btn btn--primary parcel-panel__next" disabled={!located} onClick={() => setStep('name')}>
                Tiếp tục <Icon name="arrowRight" />
              </button>
              <p className="parcel-panel__keys">
                <kbd>Enter</kbd> đóng vùng · <kbd>⌫</kbd> hoàn tác · <kbd>Esc</kbd> xoá
              </p>
            </>
          ) : (
            <form
              onSubmit={(e) => {
                e.preventDefault()
                save()
              }}
            >
              <h1 className="parcel-panel__title">Đặt tên thửa</h1>
              <label className="form-field">
                <span>Tên thửa</span>
                <input autoFocus value={name} maxLength={60} placeholder="Ruộng sau nhà" onChange={(e) => setName(e.target.value)} />
              </label>
              {mode === 'polygon' ? (
                <div className="form-field">
                  <span>Diện tích</span>
                  <p className="form-field__static">
                    {formatHa(areaHa)} <span className="evidence-chip">Ước lượng từ hình vẽ</span>
                  </p>
                  <p className="form-field__help">Tính từ đường viền trên ảnh vệ tinh, không thay cho số đo địa chính.</p>
                </div>
              ) : (
                <label className="form-field">
                  <span>Diện tích (nếu biết)</span>
                  <span className="input-unit">
                    <input inputMode="decimal" value={reportedHa} placeholder="Bỏ trống nếu chưa biết" onChange={(e) => setReportedHa(e.target.value)} />
                    <span>ha</span>
                  </span>
                  <span className="form-field__help">Bỏ trống thì diện tích ghi là “Chưa biết”, không tự điền số.</span>
                </label>
              )}
              <p className="parcel-panel__place">
                <Icon name="pin" /> {editing?.place_name || initial.place}
              </p>
              <div className="parcel-panel__row">
                <button type="button" className="btn btn--ghost btn--sm" onClick={() => setStep('locate')}>
                  <Icon name="arrowLeft" /> Sửa vị trí
                </button>
              </div>
              <button type="submit" className="btn btn--primary parcel-panel__next">
                <Icon name="check" /> {editing ? 'Lưu thay đổi' : 'Lưu thửa'}
              </button>
            </form>
          )}
        </section>
      </div>
    </AppShell>
  )
}

/** Do any two non-adjacent edges cross? `closed` adds the last→first edge. */
function selfCrossAny(ring: LngLat[], closed: boolean): boolean {
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

export function initialViewFrom(params: URLSearchParams): InitialView {
  const num = (k: string) => {
    const v = Number(params.get(k))
    return params.has(k) && Number.isFinite(v) ? v : null
  }
  const lat = num('lat')
  const lng = num('lng')
  return {
    lat: lat ?? MEKONG_REGION.lat,
    lng: lng ?? MEKONG_REGION.lng,
    zoom: num('z') ?? (lat !== null ? 13 : MEKONG_REGION.zoom),
    place: params.get('noi') ?? MEKONG_REGION.name,
  }
}
