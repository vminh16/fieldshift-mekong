import maplibregl, { type Map as MlMap } from 'maplibre-gl'
import { IMAGERY_ATTRIBUTION, IMAGERY_TILES, LABEL_TILES } from './tiles'

export type BasemapId = 'satellite' | 'topo'

export const BASEMAPS: Record<BasemapId, { label: string }> = {
  satellite: { label: 'Ảnh vệ tinh' },
  topo: { label: 'Bản đồ địa hình' },
}

const TOPO_TILES = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}'

/** A flat (no rotation, no pitch) raster map shared by every map screen in the app. */
export function createBaseMap(container: HTMLElement, view: { lat: number; lng: number; zoom: number }, opts: { interactive?: boolean } = {}): MlMap {
  const map = new maplibregl.Map({
    container,
    style: {
      version: 8,
      sources: {
        // Esri imagery over the rural delta often stops at z18 (z19 returns a "not yet available" tile): over-zoom z18 instead.
        imagery: { type: 'raster', tiles: [IMAGERY_TILES], tileSize: 256, maxzoom: 18, attribution: IMAGERY_ATTRIBUTION },
        topo: { type: 'raster', tiles: [TOPO_TILES], tileSize: 256, maxzoom: 19, attribution: 'Bản đồ: Esri' },
        labels: { type: 'raster', tiles: [LABEL_TILES], tileSize: 256, maxzoom: 19 },
      },
      layers: [
        { id: 'imagery', type: 'raster', source: 'imagery' },
        { id: 'topo', type: 'raster', source: 'topo', layout: { visibility: 'none' } },
        { id: 'labels', type: 'raster', source: 'labels', paint: { 'raster-opacity': 0.7 } },
      ],
    },
    center: [view.lng, view.lat],
    zoom: view.zoom,
    maxZoom: 19.5,
    attributionControl: { compact: true },
    dragRotate: false,
    pitchWithRotate: false,
    doubleClickZoom: false,
    interactive: opts.interactive ?? true,
  })
  map.touchZoomRotate.disableRotation()
  return map
}

export function setBasemap(map: MlMap, id: BasemapId) {
  map.setLayoutProperty('imagery', 'visibility', id === 'satellite' ? 'visible' : 'none')
  map.setLayoutProperty('topo', 'visibility', id === 'topo' ? 'visible' : 'none')
}

export function setLayerVisible(map: MlMap, layerIds: string[], visible: boolean) {
  for (const id of layerIds) if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', visible ? 'visible' : 'none')
}
