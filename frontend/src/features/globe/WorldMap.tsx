import { useEffect, useImperativeHandle, useRef, type Ref } from 'react'
import maplibregl, { type Map as MlMap, type PaddingOptions } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { Place } from '../../shared/geo/types'
import { IMAGERY_ATTRIBUTION, IMAGERY_TILES, LABEL_TILES } from '../../shared/geo/tiles'

export interface Focus {
  /** Screen fraction (0–1) where the map's centre should sit. */
  fx: number
  fy: number
}

export interface WorldMapHandle {
  /** Place the camera instantly — called every frame during the globe transition. */
  jump: (lat: number, lng: number, zoom: number, focus: Focus) => void
  /** Smooth flight while the map is already the active view. */
  flyTo: (place: Place, focus: Focus) => void
  view: () => { lat: number; lng: number; zoom: number }
  /** Place-name overlay; hidden while zooming so over-scaled labels never flash. */
  setLabels: (visible: boolean) => void
}

interface Props {
  ref?: Ref<WorldMapHandle>
  places: Place[]
  selectedId: string | null
  onPlaceClick: (p: Place) => void
}


/** Padding that moves MapLibre's focal point to screen fraction (fx, fy). */
function paddingFor(map: MlMap, { fx, fy }: Focus): PaddingOptions {
  const c = map.getContainer()
  const w = c.clientWidth
  const h = c.clientHeight
  const dx = (2 * fx - 1) * w
  const dy = (2 * fy - 1) * h
  return { left: Math.max(0, dx), right: Math.max(0, -dx), top: Math.max(0, dy), bottom: Math.max(0, -dy) }
}

export function WorldMap({ ref, places, selectedId, onPlaceClick }: Props) {
  const hostRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MlMap | null>(null)
  const clickRef = useRef(onPlaceClick)
  clickRef.current = onPlaceClick

  useEffect(() => {
    const map = new maplibregl.Map({
      container: hostRef.current!,
      style: {
        version: 8,
        sources: {
          imagery: {
            type: 'raster',
            tiles: [IMAGERY_TILES],
            tileSize: 256,
            maxzoom: 19,
            attribution: IMAGERY_ATTRIBUTION,
          },
          labels: { type: 'raster', tiles: [LABEL_TILES], tileSize: 256, maxzoom: 19 },
        },
        layers: [
          { id: 'imagery', type: 'raster', source: 'imagery', paint: { 'raster-fade-duration': 120 } },
          {
            id: 'labels',
            type: 'raster',
            source: 'labels',
            paint: { 'raster-opacity': 0, 'raster-opacity-transition': { duration: 700, delay: 0 } },
          },
        ],
      },
      center: [105.75, 9.95],
      zoom: 5,
      attributionControl: { compact: true },
      dragRotate: false,
      pitchWithRotate: false,
      maxPitch: 0,
      fadeDuration: 0,
    })
    map.touchZoomRotate.disableRotation()
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right')
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Clickable markers for the Mekong provinces.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const markers = places.map((p) => {
      const el = document.createElement('button')
      el.type = 'button'
      el.className = `map-marker${p.id === selectedId ? ' is-active' : ''}`
      el.setAttribute('aria-label', `Chọn ${p.name}`)
      el.innerHTML = `<span class="map-marker__dot"></span><span class="map-marker__label"></span>`
      el.querySelector('.map-marker__label')!.textContent = p.name
      el.addEventListener('click', (e) => {
        e.stopPropagation()
        clickRef.current(p)
      })
      return new maplibregl.Marker({ element: el, anchor: 'left', offset: [-7, 0] }).setLngLat([p.lng, p.lat]).addTo(map)
    })
    return () => markers.forEach((m) => m.remove())
  }, [places, selectedId])

  useImperativeHandle(ref, () => ({
    jump: (lat, lng, zoom, focus) => {
      const map = mapRef.current
      if (!map) return
      map.jumpTo({ center: [lng, lat], zoom, padding: paddingFor(map, focus) })
    },
    flyTo: (place, focus) => {
      const map = mapRef.current
      if (!map) return
      map.flyTo({
        center: [place.lng, place.lat],
        zoom: place.zoom,
        padding: paddingFor(map, focus),
        speed: 1.1,
        curve: 1.42,
        essential: true,
      })
    },
    setLabels: (visible) => {
      const map = mapRef.current
      if (!map) return
      const apply = () => map.setPaintProperty('labels', 'raster-opacity', visible ? 0.85 : 0)
      if (map.getLayer('labels')) apply()
      else map.once('load', apply)
    },
    view: () => {
      const map = mapRef.current!
      const c = map.getCenter()
      return { lat: c.lat, lng: c.lng, zoom: map.getZoom() }
    },
  }))

  return <div ref={hostRef} className="world-map" />
}
