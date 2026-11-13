import { useEffect, useRef, useState } from 'react'
import maplibregl, { type GeoJSONSource, type Map as MlMap, type Marker } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { AppShell } from '../shell/AppShell'
import { Icon } from '../../shared/ui/Icon'
import { href, navigate } from '../../shared/router'
import { IMAGERY_ATTRIBUTION, IMAGERY_TILES, LABEL_TILES } from '../../shared/geo/tiles'
import { formatHa } from '../../shared/geo/area'
import { MEKONG_REGION } from '../../shared/geo/mekongProvinces'
import {
  FIELD_STATUS_LABEL,
  removeField,
  setActiveField,
  useActiveFieldId,
  useFields,
  type LocalField,
} from '../../shared/fields/store'
import '../parcel/parcel.css'
import './fields.css'

function toFeatures(fields: LocalField[], activeId: string | null): GeoJSON.FeatureCollection {
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

function boundsOf(fields: LocalField[]): [[number, number], [number, number]] | null {
  const pts = fields.flatMap((f) => f.ring ?? [[f.centroid.lng, f.centroid.lat] as [number, number]])
  if (pts.length === 0) return null
  const lngs = pts.map((p) => p[0])
  const lats = pts.map((p) => p[1])
  return [
    [Math.min(...lngs), Math.min(...lats)],
    [Math.max(...lngs), Math.max(...lats)],
  ]
}

export function FieldsScreen({ highlightNew }: { highlightNew: boolean }) {
  const fields = useFields()
  const activeId = useActiveFieldId()
  const hostRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MlMap | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [showSaved, setShowSaved] = useState(highlightNew)

  useEffect(() => {
    if (!hostRef.current) return
    const map = new maplibregl.Map({
      container: hostRef.current,
      style: {
        version: 8,
        sources: {
          imagery: { type: 'raster', tiles: [IMAGERY_TILES], tileSize: 256, maxzoom: 19, attribution: IMAGERY_ATTRIBUTION },
          labels: { type: 'raster', tiles: [LABEL_TILES], tileSize: 256, maxzoom: 19 },
          fields: { type: 'geojson', data: toFeatures([], null) },
        },
        layers: [
          { id: 'imagery', type: 'raster', source: 'imagery' },
          { id: 'labels', type: 'raster', source: 'labels', paint: { 'raster-opacity': 0.7 } },
          {
            id: 'fields-fill',
            type: 'fill',
            source: 'fields',
            paint: { 'fill-color': '#4fd8b4', 'fill-opacity': ['case', ['get', 'active'], 0.3, 0.12] },
          },
          {
            id: 'fields-line',
            type: 'line',
            source: 'fields',
            paint: { 'line-color': ['case', ['get', 'active'], '#7be6c8', '#e8f3f0'], 'line-width': ['case', ['get', 'active'], 3, 1.5] },
          },
        ],
      },
      center: [MEKONG_REGION.lng, MEKONG_REGION.lat],
      zoom: MEKONG_REGION.zoom,
      attributionControl: { compact: true },
      dragRotate: false,
      pitchWithRotate: false,
    })
    map.touchZoomRotate.disableRotation()
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right')
    map.on('click', 'fields-fill', (e) => {
      const id = e.features?.[0]?.properties?.id as string | undefined
      if (id) setActiveField(id)
    })
    map.on('mouseenter', 'fields-fill', () => (map.getCanvas().style.cursor = 'pointer'))
    map.on('mouseleave', 'fields-fill', () => (map.getCanvas().style.cursor = ''))
    mapRef.current = map
    const b = boundsOf(fields)
    if (b) map.fitBounds(b, { padding: 80, maxZoom: 17, duration: 0 })
    return () => {
      map.remove()
      mapRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fields.length === 0])

  // Keep polygons, point pins and the active highlight in sync.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const apply = () => (map.getSource('fields') as GeoJSONSource | undefined)?.setData(toFeatures(fields, activeId))
    if (map.getSource('fields')) apply()
    else map.once('load', apply)
    const pins: Marker[] = fields
      .filter((f) => !f.ring)
      .map((f) => {
        const el = document.createElement('button')
        el.type = 'button'
        el.className = 'parcel-pin'
        el.setAttribute('aria-label', `Chọn ${f.name}`)
        el.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-6.5-6.2-6.5-11a6.5 6.5 0 0 1 13 0c0 4.8-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.5"/></svg>'
        el.addEventListener('click', () => setActiveField(f.id))
        return new maplibregl.Marker({ element: el, anchor: 'bottom' }).setLngLat([f.centroid.lng, f.centroid.lat]).addTo(map)
      })
    return () => pins.forEach((p) => p.remove())
  }, [fields, activeId])

  const focus = (f: LocalField) => {
    setActiveField(f.id)
    const map = mapRef.current
    if (!map) return
    const b = boundsOf([f])!
    if (f.ring) map.fitBounds(b, { padding: 100, maxZoom: 17.5, duration: 900 })
    else map.flyTo({ center: [f.centroid.lng, f.centroid.lat], zoom: 16, duration: 900 })
  }

  const active = fields.find((f) => f.id === activeId)

  if (fields.length === 0) {
    return (
      <AppShell crumbs={[{ label: 'Ruộng của tôi' }]}>
        <section className="fields-empty">
          <div className="fields-empty__art" aria-hidden="true">
            <Icon name="polygon" className="icon fields-empty__icon" />
          </div>
          <h1>Bắt đầu với thửa ruộng đầu tiên</h1>
          <p>
            Khoanh ranh giới trên ảnh vệ tinh, hoặc chỉ cần chấm một điểm giữa ruộng. Bạn có thể thêm nhiều thửa và so sánh phương án luân canh cho từng
            thửa.
          </p>
          <div className="fields-empty__actions">
            <a className="btn btn--primary" href={href('/ruong/moi')}>
              <Icon name="plus" /> Khoanh thửa ruộng
            </a>
            <a className="btn btn--ghost" href={href('/')}>
              Tìm vị trí trên địa cầu
            </a>
          </div>
        </section>
      </AppShell>
    )
  }

  return (
    <AppShell bleed crumbs={[{ label: 'Ruộng của tôi' }]}>
      <div className="fields">
        <div ref={hostRef} className="fields-map" />

        <section className="fields-list" aria-label="Danh sách thửa">
          <header className="fields-list__head">
            <h1>
              Ruộng của tôi <span>{fields.length} thửa</span>
            </h1>
          </header>

          {showSaved && active && (
            <div className="saved-banner" role="status">
              <Icon name="check" />
              <div>
                <strong>Đã lưu “{active.name}”.</strong>
                <span>Bước tiếp: khai báo chuỗi vụ đang trồng, nước và đất để mô phỏng luân canh.</span>
              </div>
              <button type="button" aria-label="Đóng thông báo" onClick={() => setShowSaved(false)}>
                ×
              </button>
            </div>
          )}

          <ul className="field-cards">
            {fields.map((f) => (
              <li key={f.id}>
                <article className="field-card" data-active={f.id === activeId || undefined}>
                  <button type="button" className="field-card__main" onClick={() => focus(f)} aria-pressed={f.id === activeId}>
                    <span className="field-card__name">{f.name}</span>
                    <span className="field-card__meta">
                      {f.area_ha !== null ? formatHa(f.area_ha) : 'Diện tích chưa biết'}
                      {f.area_source === 'drawn' && ' · ước lượng'}
                      {' · '}
                      {f.ring ? 'Có ranh giới' : 'Chỉ có điểm'}
                    </span>
                    <span className="field-card__place">{f.place_name}</span>
                    <span className="status-tag" data-status={f.status}>
                      {FIELD_STATUS_LABEL[f.status]}
                    </span>
                  </button>
                  {f.id === activeId && (
                    <div className="field-card__actions">
                      <button type="button" className="btn btn--primary btn--sm" onClick={() => navigate('/mo-phong', { thua: f.id })}>
                        <Icon name="rotate" /> Mô phỏng luân canh
                      </button>
                      <a className="btn btn--ghost btn--sm" href={href(`/ruong/${f.id}/sua`)}>
                        <Icon name="edit" /> Sửa ranh giới
                      </a>
                      {confirmDelete === f.id ? (
                        <span className="confirm-delete">
                          Xoá thửa này?
                          <button
                            type="button"
                            className="btn btn--danger btn--sm"
                            onClick={() => {
                              removeField(f.id)
                              setConfirmDelete(null)
                            }}
                          >
                            Xoá
                          </button>
                          <button type="button" className="btn btn--ghost btn--sm" onClick={() => setConfirmDelete(null)}>
                            Giữ lại
                          </button>
                        </span>
                      ) : (
                        <button type="button" className="btn btn--ghost btn--sm" aria-label={`Xoá ${f.name}`} onClick={() => setConfirmDelete(f.id)}>
                          <Icon name="trash" />
                        </button>
                      )}
                    </div>
                  )}
                </article>
              </li>
            ))}
            <li>
              <a className="field-card field-card--add" href={href('/ruong/moi')}>
                <Icon name="plus" /> Thêm thửa
              </a>
            </li>
          </ul>
        </section>
      </div>
    </AppShell>
  )
}
