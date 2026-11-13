import { useEffect, useRef, useState, type ReactNode } from 'react'
import maplibregl, { type GeoJSONSource, type Map as MlMap, type Marker } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { AppShell } from '../shell/AppShell'
import { Icon, type IconName } from '../../shared/ui/Icon'
import { navigate, type Route } from '../../shared/router'
import { BASEMAPS, createBaseMap, setBasemap, setLayerVisible, type BasemapId } from '../../shared/geo/basemap'
import { formatHa, ringCentroid } from '../../shared/geo/area'
import { MEKONG_REGION, nearestProvince } from '../../shared/geo/mekongProvinces'
import { reverseGeocode } from '../../shared/geo/geocode'
import { COARSE_M, GPS_ERROR_MSG, PRECISE_M, accuracyCircle, formatAccuracy, watchPosition, type GpsError, type GpsFix } from '../../shared/geo/gps'
import { removeField, renamePlace, saveField, setActiveField, syncFields, useActiveFieldId, useFields, useSync, type LocalField } from '../../shared/fields/store'
import { MIN_DRAW_ZOOM, OUTSIDE_MSG, ParcelEditor, inServiceArea, type DrawMode, type EditorState } from '../parcel/ParcelEditor'
import { FieldThumb } from './FieldThumb'
import './workspace.css'

type Mode = 'browse' | 'draw' | 'edit'

const DRAW_ZOOM = 16.8
const LARGE_HA = 30
const EMPTY_FC: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] }

function boundsOf(fields: LocalField[]): [[number, number], [number, number]] | null {
  const pts = fields.flatMap((f) => f.ring ?? [[f.centroid.lng, f.centroid.lat] as [number, number]])
  if (!pts.length) return null
  const lngs = pts.map((p) => p[0])
  const lats = pts.map((p) => p[1])
  return [
    [Math.min(...lngs), Math.min(...lats)],
    [Math.max(...lngs), Math.max(...lats)],
  ]
}

function fieldFeatures(fields: LocalField[], activeId: string | null): GeoJSON.FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: fields
      .filter((f) => f.ring)
      .map((f) => ({
        type: 'Feature',
        properties: { id: f.id, active: f.id === activeId },
        geometry: { type: 'Polygon', coordinates: [[...f.ring!, f.ring![0]]] },
      })),
  }
}

/** Seeded demo parcels carry no place label; derive one from the gazetteer. */
const placeOf = (f: LocalField) => f.place_name || nearestProvince(f.centroid.lat, f.centroid.lng, 0.6)?.name || 'Đồng bằng sông Cửu Long'
const areaLabel = (f: LocalField) => (f.area_ha === null ? 'Chưa biết' : formatHa(f.area_ha))
const areaSource = (f: LocalField) =>
  f.area_source === 'drawn' ? 'Ước lượng từ hình vẽ' : f.area_source === 'reported' ? 'Người dùng báo' : f.area_source === 'sample' ? 'Giá trị mẫu' : 'Chưa đo'

export function FieldsWorkspace({ route }: { route: Route }) {
  const fields = useFields()
  const sync = useSync()
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const activeId = useActiveFieldId()
  const active = fields.find((f) => f.id === activeId) ?? null

  const editMatch = route.path.match(/^\/ruong\/([^/]+)\/sua$/)
  const editing = editMatch ? (fields.find((f) => f.id === editMatch[1]) ?? null) : null
  const mode: Mode = route.path === '/ruong/moi' ? 'draw' : editing ? 'edit' : 'browse'

  const hostRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MlMap | null>(null)
  const editorRef = useRef<ParcelEditor | null>(null)
  const [ready, setReady] = useState(false)
  const [zoom, setZoom] = useState(0)
  const [ed, setEd] = useState<EditorState>({ mode: 'polygon', ring: [], closed: false, point: null })
  const [step, setStep] = useState<'locate' | 'name'>('locate')
  const [name, setName] = useState('')
  const [reportedHa, setReportedHa] = useState('')
  const [notice, setNotice] = useState<string | null>(null)
  const [collapsed, setCollapsed] = useState(() => window.matchMedia('(max-width: 759px)').matches)
  const [cardOpen, setCardOpen] = useState(true)
  const [menuFor, setMenuFor] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [layersOpen, setLayersOpen] = useState(false)
  const [basemapOpen, setBasemapOpen] = useState(false)
  const [basemap, setBasemapId] = useState<BasemapId>('satellite')
  const [showLabels, setShowLabels] = useState(true)
  const [showOthers, setShowOthers] = useState(true)
  const [gps, setGps] = useState<{ status: 'off' | 'locating' | 'on'; fix: GpsFix | null }>({ status: 'off', fix: null })
  const stopGpsRef = useRef<(() => void) | null>(null)
  const gpsDotRef = useRef<Marker | null>(null)

  const noticeTimer = useRef(0)
  const flash = (msg: string) => {
    setNotice(msg)
    window.clearTimeout(noticeTimer.current)
    noticeTimer.current = window.setTimeout(() => setNotice(null), 4200)
  }

  // ---------- map, created once ----------
  useEffect(() => {
    const p = route.params
    const lat = Number(p.get('lat'))
    const lng = Number(p.get('lng'))
    const hasView = p.has('lat') && p.has('lng') && Number.isFinite(lat) && Number.isFinite(lng)
    const map = createBaseMap(hostRef.current!, hasView ? { lat, lng, zoom: Number(p.get('z')) || 13 } : { lat: MEKONG_REGION.lat, lng: MEKONG_REGION.lng, zoom: MEKONG_REGION.zoom })
    map.addControl(new maplibregl.ScaleControl({ unit: 'metric', maxWidth: 120 }), 'bottom-left')
    mapRef.current = map
    if (!hasView) {
      const b = boundsOf(fields)
      if (b) map.fitBounds(b, { padding: 120, maxZoom: 17, duration: 0 })
    }
    setZoom(map.getZoom())
    map.on('zoom', () => setZoom(map.getZoom()))

    map.on('load', () => {
      map.addSource('fields', { type: 'geojson', data: EMPTY_FC })
      map.addLayer({ id: 'fields-fill', type: 'fill', source: 'fields', paint: { 'fill-color': '#a6d388', 'fill-opacity': ['case', ['get', 'active'], 0.2, 0.06] } })
      map.addLayer({
        id: 'fields-line',
        type: 'line',
        source: 'fields',
        paint: { 'line-color': ['case', ['get', 'active'], '#c2e3a8', '#eef0eb'], 'line-width': ['case', ['get', 'active'], 2.5, 1.25], 'line-opacity': ['case', ['get', 'active'], 1, 0.75] },
      })
      map.addSource('gps', { type: 'geojson', data: EMPTY_FC })
      map.addLayer({ id: 'gps-acc-fill', type: 'fill', source: 'gps', paint: { 'fill-color': '#8fb8e8', 'fill-opacity': 0.12 } })
      map.addLayer({ id: 'gps-acc-line', type: 'line', source: 'gps', paint: { 'line-color': '#8fb8e8', 'line-width': 1, 'line-opacity': 0.7 } })
      const editor = new ParcelEditor(map, { onChange: (s) => setEd({ ...s }), onNotice: flash })
      editor.attach()
      editorRef.current = editor
      map.on('click', 'fields-fill', (e) => {
        if (editor.isActive) return
        const id = e.features?.[0]?.properties?.id as string | undefined
        if (id) {
          setActiveField(id)
          setCardOpen(true)
        }
      })
      map.on('mouseenter', 'fields-fill', () => !editor.isActive && (map.getCanvas().style.cursor = 'pointer'))
      map.on('mouseleave', 'fields-fill', () => !editor.isActive && (map.getCanvas().style.cursor = ''))
      setReady(true)
    })
    return () => {
      stopGpsRef.current?.()
      gpsDotRef.current?.remove()
      editorRef.current?.destroy()
      map.remove()
      mapRef.current = null
      editorRef.current = null
    }
    // Created once; later route changes move the camera instead of rebuilding the map.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ---------- enter / leave drawing ----------
  useEffect(() => {
    const editor = editorRef.current
    const map = mapRef.current
    if (!ready || !editor || !map) return
    setStep('locate')
    setMenuFor(null)
    if (mode === 'browse') return editor.stop()
    if (mode === 'draw') {
      setName('')
      setReportedHa('')
      editor.start({ mode: route.params.get('kieu') === 'diem' ? 'point' : 'polygon' })
      // The workspace stays mounted across routes, so a draw link carrying a view must move the camera here.
      const lat = Number(route.params.get('lat'))
      const lng = Number(route.params.get('lng'))
      if (route.params.has('lat') && Number.isFinite(lat) && Number.isFinite(lng)) {
        map.jumpTo({ center: [lng, lat], zoom: Number(route.params.get('z')) || map.getZoom() })
      }
      return
    }
    // edit
    const f = editing!
    setName(f.name)
    setReportedHa(f.area_source === 'reported' && f.area_ha ? String(f.area_ha) : '')
    editor.start(f.ring ? { mode: 'polygon', ring: f.ring, closed: true } : { mode: 'point', point: [f.centroid.lng, f.centroid.lat] })
    const b = boundsOf([f])!
    if (f.ring) map.fitBounds(b, { padding: { top: 120, bottom: 80, left: 80, right: 420 }, maxZoom: 18, duration: 700 })
    else map.flyTo({ center: [f.centroid.lng, f.centroid.lat], zoom: 17, duration: 700 })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, mode, editing?.id])

  // ---------- other parcels on the map ----------
  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map) return
    // The parcel being edited is drawn by the editor; "others" can be hidden, but never the selected one while browsing.
    const shown = fields.filter((f) => f.id !== editing?.id && (showOthers || (mode === 'browse' && f.id === activeId)))
    ;(map.getSource('fields') as GeoJSONSource).setData(fieldFeatures(shown, mode === 'browse' ? activeId : null))
    const pins: Marker[] = shown
      .filter((f) => !f.ring)
      .map((f) => {
        const el = document.createElement('button')
        el.type = 'button'
        el.className = `field-pin${f.id === activeId && mode === 'browse' ? ' is-active' : ''}`
        el.setAttribute('aria-label', `Chọn ${f.name}`)
        el.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-6.5-6.2-6.5-11a6.5 6.5 0 0 1 13 0c0 4.8-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.4"/></svg>'
        el.addEventListener('click', (e) => {
          e.stopPropagation()
          if (mode !== 'browse') return
          setActiveField(f.id)
          setCardOpen(true)
        })
        return new maplibregl.Marker({ element: el, anchor: 'bottom' }).setLngLat([f.centroid.lng, f.centroid.lat]).addTo(map)
      })
    return () => pins.forEach((p) => p.remove())
  }, [ready, fields, activeId, mode, editing?.id, showOthers])

  useEffect(() => {
    const map = mapRef.current
    if (!ready || !map) return
    setBasemap(map, basemap)
    setLayerVisible(map, ['labels'], showLabels)
  }, [ready, basemap, showLabels])

  // ---------- keyboard while drawing ----------
  useEffect(() => {
    if (mode === 'browse' || step !== 'locate') return
    const onKey = (e: KeyboardEvent) => {
      const editor = editorRef.current
      if (!editor || (e.target as HTMLElement).closest('input, select, textarea')) return
      if (e.key === 'Enter') editor.close()
      else if (e.key === 'Backspace' || (e.key === 'z' && (e.ctrlKey || e.metaKey))) {
        e.preventDefault()
        editor.undo()
      } else if (e.key === 'Escape') editor.clear()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [mode, step])

  // ---------- actions ----------
  const focusField = (f: LocalField) => {
    setActiveField(f.id)
    setCardOpen(true)
    const map = mapRef.current
    if (!map) return
    if (f.ring) map.fitBounds(boundsOf([f])!, { padding: { top: 120, bottom: 80, left: 80, right: 420 }, maxZoom: 17.5, duration: 800 })
    else map.flyTo({ center: [f.centroid.lng, f.centroid.lat], zoom: 16.5, duration: 800 })
  }

  const startDraw = (kind: DrawMode) => {
    if (mode === 'browse') return navigate('/ruong/moi', { kieu: kind === 'point' ? 'diem' : null })
    if (mode === 'draw') editorRef.current?.setMode(kind)
  }

  const goStep = (s: 'locate' | 'name') => {
    setStep(s)
    editorRef.current?.lock(s === 'name')
  }

  const save = async () => {
    const editor = editorRef.current!
    const st = editor.snapshot
    const trimmed = name.trim()
    if (!trimmed) return flash('Đặt tên cho thửa để dễ nhận ra sau này.')
    const reported = reportedHa.trim() === '' ? null : Number(reportedHa.replace(',', '.'))
    if (reported !== null && (!Number.isFinite(reported) || reported <= 0)) return flash('Diện tích phải là số lớn hơn 0.')
    const polygon = st.mode === 'polygon'
    const centroid = polygon ? ringCentroid(st.ring) : { lng: st.point![0], lat: st.point![1] }
    // Offline first: nearest province centroid from the gazetteer; refined below by the geocoder when available.
    const moved = !editing || Math.hypot(centroid.lat - editing.centroid.lat, centroid.lng - editing.centroid.lng) > 0.01
    const place = (!moved && editing?.place_name) || route.params.get('noi') || nearestProvince(centroid.lat, centroid.lng, 0.6)?.name || 'Đồng bằng sông Cửu Long'
    setSaving(true)
    try {
      const { field, offline } = await saveField({
        id: editing?.id,
        name: trimmed,
        ring: polygon ? st.ring : null,
        centroid,
        area_ha: polygon ? Math.round(editor.areaHa * 1000) / 1000 : reported,
        area_source: polygon ? 'drawn' : reported !== null ? 'reported' : null,
        place_name: place,
      })
      if (moved && !offline) {
        reverseGeocode(centroid.lat, centroid.lng)
          .then((p) => (p?.name ? renamePlace(field.id, p.name) : undefined))
          .catch(() => undefined)
      }
      setCardOpen(true)
      navigate('/ruong')
      flash(
        offline
          ? `Chưa kết nối được máy chủ — đã lưu “${trimmed}” trên máy này, sẽ tự đồng bộ khi có mạng.`
          : editing
            ? 'Đã lưu thay đổi.'
            : `Đã lưu “${trimmed}”. Bước tiếp: cập nhật thông tin canh tác.`,
      )
    } catch (e) {
      flash(e instanceof Error ? e.message : 'Không lưu được thửa.')
    } finally {
      setSaving(false)
    }
  }

  const remove = async (f: LocalField) => {
    setDeleting(true)
    try {
      await removeField(f.id)
      setMenuFor(null)
      flash(`Đã xoá “${f.name}”.`)
    } catch (e) {
      flash(e instanceof Error ? e.message : 'Không xoá được thửa.')
    } finally {
      setDeleting(false)
    }
  }

  // ---------- GPS ----------
  const flyToFix = (fix: GpsFix, first: boolean) => {
    const map = mapRef.current
    if (!map) return
    // Zoom to what the fix can actually resolve: a coarse Wi-Fi/cell fix should not pretend to show a paddy.
    const zoom = fix.accuracy <= PRECISE_M ? Math.max(DRAW_ZOOM, map.getZoom()) : fix.accuracy <= COARSE_M ? 16 : 13
    map.flyTo({ center: [fix.lng, fix.lat], zoom: first ? zoom : Math.max(map.getZoom(), Math.min(zoom, DRAW_ZOOM)), duration: 1100 })
  }

  const showFix = (fix: GpsFix) => {
    const map = mapRef.current
    if (!map) return
    ;(map.getSource('gps') as GeoJSONSource | undefined)?.setData({ type: 'FeatureCollection', features: [accuracyCircle(fix)] })
    if (!gpsDotRef.current) {
      const el = document.createElement('div')
      el.className = 'gps-dot'
      el.setAttribute('role', 'img')
      el.setAttribute('aria-label', 'Vị trí của bạn')
      gpsDotRef.current = new maplibregl.Marker({ element: el })
    }
    gpsDotRef.current.setLngLat([fix.lng, fix.lat]).addTo(map)
  }

  const stopGps = () => {
    stopGpsRef.current?.()
    stopGpsRef.current = null
    gpsDotRef.current?.remove()
    gpsDotRef.current = null
    ;(mapRef.current?.getSource('gps') as GeoJSONSource | undefined)?.setData(EMPTY_FC)
    setGps({ status: 'off', fix: null })
  }

  /** First press: start tracking and fly there. Later presses: re-center on the latest fix. */
  const locateMe = () => {
    if (gps.fix) return flyToFix(gps.fix, false)
    if (gps.status === 'locating') return
    setGps({ status: 'locating', fix: null })
    flash('Đang định vị…')
    let first = true
    stopGpsRef.current = watchPosition(
      (fix) => {
        setGps({ status: 'on', fix })
        showFix(fix)
        if (!first) return
        first = false
        flyToFix(fix, true)
        if (!inServiceArea([fix.lng, fix.lat])) flash(`Bạn đang ở ngoài vùng hỗ trợ. ${OUTSIDE_MSG}`)
        else if (fix.accuracy > COARSE_M) flash(`Đã định vị nhưng sai số lớn (${formatAccuracy(fix.accuracy)}). Bật GPS / vị trí chính xác cao để chính xác hơn.`)
        else flash(`Đã định vị · sai số ${formatAccuracy(fix.accuracy)}`)
      },
      (err: GpsError) => {
        flash(GPS_ERROR_MSG[err])
        // Keep the last good fix if the signal drops mid-walk; otherwise turn GPS off.
        if (first || err === 'denied') stopGps()
      },
    )
  }

  const placeAtGps = () => {
    const fix = gps.fix
    if (!fix) return locateMe()
    if (fix.accuracy > PRECISE_M) return flash(`Sai số hiện tại ${formatAccuracy(fix.accuracy)} — quá lớn để chấm góc ruộng. Đợi tín hiệu tốt hơn hoặc chấm trên ảnh.`)
    if (editorRef.current?.placeAt([fix.lng, fix.lat])) mapRef.current?.easeTo({ center: [fix.lng, fix.lat], duration: 500 })
  }

  const drawing = mode !== 'browse'
  const canUndo = drawing && step === 'locate' && (ed.mode === 'point' ? ed.point !== null : ed.ring.length > 0)
  const located = ed.mode === 'polygon' ? ed.closed : ed.point !== null
  const areaHa = editorRef.current?.areaHa ?? 0

  return (
    <AppShell bleed>
      <div className="ws" data-collapsed={collapsed || undefined}>
        {/* ---------- parcel list ---------- */}
        <aside className="ws-list" aria-label="Danh sách thửa">
          {collapsed ? (
            <button type="button" className="icon-btn" aria-label="Mở danh sách thửa" title="Mở danh sách thửa" onClick={() => setCollapsed(false)}>
              <Icon name="chevronsRight" />
            </button>
          ) : (
            <>
              <header className="ws-list__head">
                <h1>
                  <Icon name="fields" /> Ruộng của tôi
                </h1>
                <button type="button" className="icon-btn" aria-label="Thu gọn danh sách" title="Thu gọn" onClick={() => setCollapsed(true)}>
                  <Icon name="chevronsLeft" />
                </button>
              </header>
              <p className="ws-list__lead">Quản lý và theo dõi các thửa ruộng của bạn.</p>
              {sync === 'offline' && (
                <div className="sync-note" role="status">
                  <span>Chưa kết nối được máy chủ. Thửa mới sẽ lưu trên máy này và tự đồng bộ sau.</span>
                  <button type="button" className="btn btn--ghost btn--sm" onClick={() => syncFields()}>
                    Thử lại
                  </button>
                </div>
              )}
              <button type="button" className="btn btn--primary ws-list__add" onClick={() => startDraw('polygon')} disabled={drawing}>
                <Icon name="plus" /> Thêm ruộng
              </button>
              {fields.length === 0 ? (
                <p className="ws-list__empty">Chưa có thửa nào. Bấm “Thêm ruộng”, phóng tới ruộng của bạn rồi chấm lần lượt các góc trên ảnh vệ tinh.</p>
              ) : (
                <ul className="ws-items">
                  {fields.map((f) => (
                    <li key={f.id} className="ws-item" data-active={(f.id === activeId && !drawing) || f.id === editing?.id || undefined}>
                      <button type="button" className="ws-item__main" onClick={() => focusField(f)} disabled={drawing}>
                        <FieldThumb field={f} />
                        <span className="ws-item__text">
                          <span className="ws-item__name">{f.name}</span>
                          <span className="ws-item__meta">
                            {f.sample ? 'Ruộng mẫu' : areaLabel(f)} · {placeOf(f)}
                          </span>
                          {f.pending && <span className="ws-item__flag">Chưa đồng bộ</span>}
                        </span>
                      </button>
                      <button
                        type="button"
                        className="icon-btn icon-btn--sm"
                        aria-label={`Tuỳ chọn cho ${f.name}`}
                        aria-expanded={menuFor === f.id}
                        disabled={drawing}
                        onClick={() => {
                          setMenuFor(menuFor === f.id ? null : f.id)
                          setConfirmDelete(null)
                        }}
                      >
                        <Icon name="more" />
                      </button>
                      {menuFor === f.id && (
                        <div className="menu" role="menu">
                          {confirmDelete === f.id ? (
                            <div className="menu__confirm">
                              <p>Xoá “{f.name}”? Không hoàn tác được.</p>
                              <div>
                                <button type="button" className="btn btn--ghost btn--sm" onClick={() => setConfirmDelete(null)}>
                                  Giữ lại
                                </button>
                                <button
                                  type="button"
                                  className="btn btn--danger btn--sm"
                                  disabled={deleting}
                                  onClick={() => remove(f)}
                                >
                                  {deleting ? 'Đang xoá…' : 'Xoá'}
                                </button>
                              </div>
                            </div>
                          ) : (
                            <>
                              <button type="button" role="menuitem" onClick={() => navigate(`/ruong/${f.id}/sua`)}>
                                <Icon name="edit" /> Chỉnh sửa ranh giới
                              </button>
                              {f.sample ? (
                                <p className="menu__note">Ruộng mẫu của hệ thống — không xoá được.</p>
                              ) : (
                                <button type="button" role="menuitem" className="menu__danger" onClick={() => setConfirmDelete(f.id)}>
                                  <Icon name="trash" /> Xoá thửa
                                </button>
                              )}
                            </>
                          )}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </aside>

        {/* ---------- map ---------- */}
        <div className="ws-map">
          <div ref={hostRef} className="ws-map__canvas" />

          <div className="toolbar" role="toolbar" aria-label="Công cụ bản đồ">
            <ToolButton icon="cursor" label="Chọn" iconOnly pressed={!drawing} onClick={() => navigate('/ruong')} />
            <ToolButton icon="polygon" label="Khoanh vùng" pressed={mode === 'draw' && ed.mode === 'polygon'} disabled={mode === 'edit' && ed.mode !== 'polygon'} onClick={() => startDraw('polygon')} />
            <ToolButton icon="pin" label="Chấm điểm" pressed={mode === 'draw' && ed.mode === 'point'} disabled={mode === 'edit' && ed.mode !== 'point'} onClick={() => startDraw('point')} />
            <ToolButton icon="edit" label="Chỉnh sửa" pressed={mode === 'edit'} disabled={mode === 'draw' || !active} onClick={() => active && navigate(`/ruong/${active.id}/sua`)} />
            <ToolButton icon="undo" label="Hoàn tác" iconOnly disabled={!canUndo} onClick={() => editorRef.current?.undo()} />
            <span className="toolbar__sep" aria-hidden="true" />
            <div className="popover-anchor">
              <ToolButton icon="layers" label="Lớp bản đồ" pressed={layersOpen} onClick={() => setLayersOpen(!layersOpen)} caret />
              {layersOpen && (
                <div className="popover" role="group" aria-label="Lớp hiển thị">
                  <label className="check-row">
                    <input type="checkbox" checked={showLabels} onChange={(e) => setShowLabels(e.target.checked)} /> Tên địa danh
                  </label>
                  <label className="check-row">
                    <input type="checkbox" checked={showOthers} onChange={(e) => setShowOthers(e.target.checked)} /> Ranh giới các thửa khác
                  </label>
                  <p className="popover__note">Lớp dữ liệu NASA (ẩm đất, mưa) sẽ thêm ở bước phân tích.</p>
                </div>
              )}
            </div>
          </div>

          <div className="map-ctrls" role="group" aria-label="Điều khiển bản đồ">
            <div className="map-ctrls__stack">
              <button type="button" aria-label="Phóng to bản đồ" title="Phóng to bản đồ" onClick={() => mapRef.current?.zoomIn()}>
                <Icon name="plus" />
              </button>
              <button type="button" aria-label="Thu nhỏ bản đồ" title="Thu nhỏ bản đồ" onClick={() => mapRef.current?.zoomOut()}>
                <Icon name="minus" />
              </button>
            </div>
            <div className="gps-ctrl">
              <button
                type="button"
                className="map-ctrls__single"
                data-gps={gps.status}
                aria-label={gps.fix ? 'Về vị trí của tôi' : 'Định vị vị trí của tôi'}
                title={gps.fix ? 'Về vị trí của tôi' : 'Định vị vị trí của tôi'}
                onClick={locateMe}
              >
                <Icon name="navigate" />
              </button>
              {gps.status !== 'off' && (
                <span className="gps-chip" data-precise={(gps.fix && gps.fix.accuracy <= PRECISE_M) || undefined}>
                  {gps.fix ? `GPS ${formatAccuracy(gps.fix.accuracy)}` : 'Đang định vị…'}
                  <button type="button" aria-label="Tắt định vị" title="Tắt định vị" onClick={stopGps}>
                    <Icon name="close" className="icon icon--xs" />
                  </button>
                </span>
              )}
            </div>
          </div>

          <div className="basemap popover-anchor">
            <button type="button" className="basemap__btn" aria-expanded={basemapOpen} onClick={() => setBasemapOpen(!basemapOpen)}>
              <Icon name="image" /> {BASEMAPS[basemap].label} <Icon name="chevron" className="icon icon--sm" />
            </button>
            {basemapOpen && (
              <div className="popover popover--up" role="radiogroup" aria-label="Nền bản đồ">
                {(Object.keys(BASEMAPS) as BasemapId[]).map((id) => (
                  <label key={id} className="check-row">
                    <input
                      type="radio"
                      name="basemap"
                      checked={basemap === id}
                      onChange={() => {
                        setBasemapId(id)
                        setBasemapOpen(false)
                      }}
                    />{' '}
                    {BASEMAPS[id].label}
                  </label>
                ))}
              </div>
            )}
          </div>

          {notice && (
            <div className="toast" role="status">
              {notice}
            </div>
          )}

          {/* ---------- right card ---------- */}
          {drawing ? (
            <Card
              title={mode === 'edit' ? 'Chỉnh ranh giới' : ed.mode === 'point' ? 'Chấm vị trí thửa' : 'Khoanh thửa mới'}
              subtitle={mode === 'edit' ? editing?.name : 'Bước ' + (step === 'locate' ? '1/2 · Vị trí' : '2/2 · Đặt tên')}
              icon={<Icon name={ed.mode === 'point' ? 'pin' : 'polygon'} className="icon card__icon" />}
              onClose={() => navigate('/ruong')}
              closeLabel="Huỷ"
            >
              {step === 'locate' ? (
                <>
                  {zoom < MIN_DRAW_ZOOM && (
                    <div className="callout">
                      <p>Phóng to tới thửa ruộng của bạn (thấy rõ bờ) để bắt đầu.</p>
                      <button type="button" className="btn btn--ghost btn--sm" onClick={() => mapRef.current?.easeTo({ zoom: DRAW_ZOOM, duration: 900 })}>
                        <Icon name="zoomIn" /> Phóng to
                      </button>
                    </div>
                  )}
                  <p className="card__hint" aria-live="polite">
                    {hintFor(ed)}
                  </p>
                  {!(ed.mode === 'polygon' && ed.closed) && (
                    <div className="gps-box">
                      {gps.fix ? (
                        <>
                          <button type="button" className="btn btn--ghost btn--sm" onClick={placeAtGps}>
                            <Icon name="navigate" /> {ed.mode === 'point' ? 'Ghim tại chỗ tôi đứng' : 'Chấm góc tại chỗ tôi đứng'}
                          </button>
                          <span className="gps-box__acc" data-ok={gps.fix.accuracy <= PRECISE_M || undefined}>
                            {formatAccuracy(gps.fix.accuracy)}
                          </span>
                        </>
                      ) : (
                        <button type="button" className="btn btn--ghost btn--sm" onClick={locateMe} disabled={gps.status === 'locating'}>
                          <Icon name="navigate" /> {gps.status === 'locating' ? 'Đang định vị…' : 'Đang đứng ở ruộng? Dùng GPS'}
                        </button>
                      )}
                      {ed.mode === 'polygon' && gps.fix && <p className="gps-box__tip">Đi dọc bờ ruộng, đến mỗi góc thì bấm một lần.</p>}
                    </div>
                  )}
                  {ed.mode === 'polygon' && (
                    <dl className="stats">
                      <div>
                        <dt>Diện tích</dt>
                        <dd>{ed.closed ? formatHa(areaHa) : '—'}</dd>
                        {ed.closed && <dd className="stats__note">Ước lượng</dd>}
                      </div>
                      <div>
                        <dt>Điểm ranh giới</dt>
                        <dd>{ed.ring.length} điểm</dd>
                      </div>
                    </dl>
                  )}
                  {ed.closed && areaHa > LARGE_HA && <p className="card__warn">Thửa lớn hơn {LARGE_HA} ha — kiểm tra lại các góc.</p>}
                  <div className="card__row">
                    {ed.mode === 'polygon' && !ed.closed && ed.ring.length >= 3 && (
                      <button type="button" className="btn btn--ghost btn--sm" onClick={() => editorRef.current?.close()}>
                        <Icon name="check" /> Đóng vùng
                      </button>
                    )}
                    {(ed.ring.length > 0 || ed.point) && (
                      <button type="button" className="btn btn--ghost btn--sm" onClick={() => editorRef.current?.clear()}>
                        Xoá hết
                      </button>
                    )}
                  </div>
                  <button type="button" className="btn btn--primary card__cta" disabled={!located} onClick={() => goStep('name')}>
                    Tiếp tục <Icon name="arrowRight" />
                  </button>
                  <p className="card__keys">
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
                  <label className="form-field">
                    <span>Tên thửa</span>
                    <input autoFocus value={name} maxLength={60} placeholder="Ruộng sau nhà" onChange={(e) => setName(e.target.value)} />
                  </label>
                  {ed.mode === 'polygon' ? (
                    <dl className="stats stats--single">
                      <div>
                        <dt>Diện tích</dt>
                        <dd>{formatHa(areaHa)}</dd>
                        <dd className="stats__note">Ước lượng từ hình vẽ trên ảnh vệ tinh, không thay số đo địa chính.</dd>
                      </div>
                    </dl>
                  ) : (
                    <label className="form-field">
                      <span>Diện tích, nếu biết</span>
                      <span className="input-unit">
                        <input inputMode="decimal" value={reportedHa} placeholder="Bỏ trống nếu chưa biết" onChange={(e) => setReportedHa(e.target.value)} />
                        <span>ha</span>
                      </span>
                      <span className="form-field__help">Bỏ trống thì diện tích ghi “Chưa biết”, không tự điền số.</span>
                    </label>
                  )}
                  <div className="card__row">
                    <button type="button" className="btn btn--ghost btn--sm" onClick={() => goStep('locate')}>
                      <Icon name="arrowLeft" /> Sửa vị trí
                    </button>
                  </div>
                  <button type="submit" className="btn btn--primary card__cta" disabled={saving}>
                    <Icon name="check" /> {saving ? 'Đang lưu…' : mode === 'edit' ? 'Lưu thay đổi' : 'Lưu thửa'}
                  </button>
                </form>
              )}
            </Card>
          ) : (
            active &&
            cardOpen && (
              <Card
                title={active.name}
                subtitle={
                  <>
                    <Icon name="pin" className="icon icon--xs" /> {placeOf(active)}
                    {active.sample && <span className="tag">Ruộng mẫu</span>}
                    {active.pending && <span className="tag tag--warn">Chưa đồng bộ</span>}
                  </>
                }
                icon={<FieldThumb field={active} size={40} />}
                onClose={() => setCardOpen(false)}
                closeLabel="Đóng"
              >
                <dl className="stats">
                  <div>
                    <dt>Diện tích</dt>
                    <dd>{areaLabel(active)}</dd>
                    <dd className="stats__note">{areaSource(active)}</dd>
                  </div>
                  <div>
                    <dt>Ranh giới</dt>
                    <dd>{active.ring ? `${active.ring.length} điểm` : '1 điểm ghim'}</dd>
                    <dd className="stats__note">{active.ring ? 'Đã khoanh' : 'Chưa khoanh vùng'}</dd>
                  </div>
                </dl>
                <ul className="rows">
                  <Row icon="edit" label="Chỉnh sửa ranh giới" onClick={() => navigate(`/ruong/${active.id}/sua`)} />
                  <Row icon="sprout" label="Thông tin canh tác" tag="Chưa cập nhật" onClick={() => navigate('/de-xuat', { thua: active.id })} />
                  <Row icon="history" label="Lịch sử phân tích" tag="Chưa có" onClick={() => navigate('/theo-doi', { thua: active.id })} />
                </ul>
                <button type="button" className="btn btn--primary card__cta" onClick={() => navigate('/de-xuat', { thua: active.id })}>
                  <Icon name="chart" /> Phân tích & đề xuất luân canh <Icon name="arrowRight" />
                </button>
              </Card>
            )
          )}
        </div>
      </div>
    </AppShell>
  )
}

function hintFor(ed: EditorState): string {
  if (ed.mode === 'point') return ed.point ? 'Kéo ghim để chỉnh. Ghim nên nằm giữa thửa.' : 'Bấm vào giữa thửa ruộng để ghim vị trí.'
  if (ed.closed) return 'Kéo các góc cho khớp bờ ruộng. Bấm chấm nhỏ giữa cạnh để thêm góc.'
  if (ed.ring.length === 0) return 'Bấm lần lượt vào các góc ruộng, đi theo bờ.'
  if (ed.ring.length < 3) return `Đã chấm ${ed.ring.length} góc. Chấm tiếp các góc còn lại.`
  return 'Bấm vào góc đầu tiên, hoặc nhấn Enter, để đóng vùng.'
}

function ToolButton({
  icon,
  label,
  pressed,
  disabled,
  onClick,
  caret,
  iconOnly,
}: {
  icon: IconName
  label: string
  pressed?: boolean
  disabled?: boolean
  onClick: () => void
  caret?: boolean
  iconOnly?: boolean
}) {
  return (
    <button type="button" className="tool" aria-pressed={pressed} aria-label={iconOnly ? label : undefined} disabled={disabled} onClick={onClick} title={label}>
      <Icon name={icon} />
      {!iconOnly && <span className="tool__label">{label}</span>}
      {caret && <Icon name="chevron" className="icon icon--sm" />}
    </button>
  )
}

function Card({ title, subtitle, icon, onClose, closeLabel, children }: { title: string; subtitle?: ReactNode; icon: ReactNode; onClose: () => void; closeLabel: string; children: ReactNode }) {
  return (
    <section className="card" aria-label={title}>
      <header className="card__head">
        <span className="card__media">{icon}</span>
        <div className="card__titles">
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        <button type="button" className="icon-btn" aria-label={closeLabel} title={closeLabel} onClick={onClose}>
          <Icon name="close" />
        </button>
      </header>
      {children}
    </section>
  )
}

function Row({ icon, label, tag, onClick }: { icon: IconName; label: string; tag?: string; onClick: () => void }) {
  return (
    <li>
      <button type="button" className="row" onClick={onClick}>
        <Icon name={icon} />
        <span className="row__label">{label}</span>
        {tag && <span className="row__tag">{tag}</span>}
        <Icon name="chevronRight" className="icon icon--sm" />
      </button>
    </li>
  )
}
