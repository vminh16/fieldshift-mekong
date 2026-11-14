import { useEffect, useRef } from 'react'
import 'maplibre-gl/dist/maplibre-gl.css'
import { createBaseMap } from '../../shared/geo/basemap'
import type { LocalField } from '../../shared/fields/store'

/** Static satellite view of the saved parcel: its outline, or a pin when only a point is known. */
export function ParcelMiniMap({ field }: { field: LocalField }) {
  const host = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const map = createBaseMap(host.current!, { lat: field.centroid.lat, lng: field.centroid.lng, zoom: field.ring ? 16 : 14.5 }, { interactive: false })
    map.on('load', () => {
      map.setLayoutProperty('labels', 'visibility', 'none')
      if (field.ring) {
        const ring = [...field.ring, field.ring[0]]
        map.addSource('parcel', { type: 'geojson', data: { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [ring] } } })
        map.addLayer({ id: 'parcel-fill', type: 'fill', source: 'parcel', paint: { 'fill-color': '#a6d388', 'fill-opacity': 0.18 } })
        map.addLayer({ id: 'parcel-line', type: 'line', source: 'parcel', paint: { 'line-color': '#c2e3a8', 'line-width': 2 } })
        const lngs = field.ring.map((p) => p[0])
        const lats = field.ring.map((p) => p[1])
        map.fitBounds(
          [
            [Math.min(...lngs), Math.min(...lats)],
            [Math.max(...lngs), Math.max(...lats)],
          ],
          { padding: 28, maxZoom: 18, duration: 0 },
        )
      } else {
        map.addSource('parcel', { type: 'geojson', data: { type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: [field.centroid.lng, field.centroid.lat] } } })
        map.addLayer({ id: 'parcel-pt', type: 'circle', source: 'parcel', paint: { 'circle-radius': 7, 'circle-color': '#a6d388', 'circle-stroke-color': '#0d0f0e', 'circle-stroke-width': 2 } })
      }
    })
    return () => map.remove()
  }, [field.id, field.updated_at]) // eslint-disable-line react-hooks/exhaustive-deps

  return <div ref={host} className="minimap" role="img" aria-label={`Ảnh vệ tinh thửa ${field.name}`} />
}
