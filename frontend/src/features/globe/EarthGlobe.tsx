import { useEffect, useImperativeHandle, useRef, useState, type Ref } from 'react'
import { EarthRenderer } from './EarthRenderer'
import { WorldMap, type Focus, type WorldMapHandle } from './WorldMap'
import { MEKONG_REGION } from '../../shared/geo/mekongProvinces'
import type { Place } from '../../shared/geo/types'
import './globe.css'

export interface EarthGlobeHandle {
  flyTo: (place: Place) => void
  reset: () => void
}

interface Props {
  ref?: Ref<EarthGlobeHandle>
  places: Place[]
  selected: Place | null
  onPlaceClick: (place: Place) => void
  onSurfaceClick: (lat: number, lng: number) => void
  onRegionClick: () => void
}

type Mode = 'globe' | 'diving' | 'map' | 'rising'

const WIDE = 960
/** Map zoom at which the globe hands over to the map (globe texture is still sharp here). */
const HANDOFF_ZOOM = 5.6
/** Zoom levels over which the two views cross-fade. */
const FADE_SPAN = 0.9

const layoutFor = (w: number, h: number) =>
  w >= WIDE ? { cx: 0.77, cy: 0.69, r: 0.6 } : { cx: 0.5, cy: 0.93, r: Math.min(0.42, (0.62 * w) / h) }
const focusFor = (w: number): Focus => (w >= WIDE ? { fx: 0.72, fy: 0.56 } : { fx: 0.5, fy: 0.68 })

const easeInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2)
const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)))
  return t * t * (3 - 2 * t)
}
const lerp = (a: number, b: number, t: number) => a + (b - a) * t

export function EarthGlobe({ ref, places, selected, onPlaceClick, onSurfaceClick, onRegionClick }: Props) {
  const hostRef = useRef<HTMLDivElement>(null)
  const globeLayerRef = useRef<HTMLDivElement>(null)
  const mapLayerRef = useRef<HTMLDivElement>(null)
  const hintRef = useRef<HTMLButtonElement>(null)
  const earthRef = useRef<EarthRenderer | null>(null)
  const mapRef = useRef<WorldMapHandle>(null)
  const timelineRef = useRef(0)
  const [mode, setMode] = useState<Mode>('globe')
  const modeRef = useRef<Mode>('globe')
  const cbRef = useRef({ onSurfaceClick, onRegionClick })
  cbRef.current = { onSurfaceClick, onRegionClick }

  const go = (m: Mode) => {
    modeRef.current = m
    setMode(m)
  }

  /** Cross-fade driven by the current zoom level, written straight to the DOM (no React render per frame). */
  const setBlend = (mapZoom: number, handoff: number) => {
    const a = smooth(handoff - FADE_SPAN / 2, handoff + FADE_SPAN / 2, mapZoom)
    if (mapLayerRef.current) mapLayerRef.current.style.opacity = String(a)
    if (globeLayerRef.current) globeLayerRef.current.style.opacity = String(1 - a)
  }

  useEffect(() => {
    const host = hostRef.current!
    const earth = new EarthRenderer(host)
    earthRef.current = earth
    if (import.meta.env.DEV) (window as unknown as { __earth: EarthRenderer }).__earth = earth

    const resize = () => {
      const w = host.clientWidth
      const h = host.clientHeight
      earth.setLayout(layoutFor(w, h))
      earth.resize(w, h)
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(host)

    earth.onFrame = () => {
      const hint = hintRef.current
      if (!hint) return
      const p = earth.project(MEKONG_REGION.lat, MEKONG_REGION.lng)
      const show = p.visible && modeRef.current === 'globe'
      hint.style.transform = `translate(${p.x}px, ${p.y}px)`
      hint.classList.toggle('is-hidden', !show)
      hint.tabIndex = show ? 0 : -1
    }

    let down: { x: number; y: number; t: number } | null = null
    const onDown = (e: PointerEvent) => (down = { x: e.clientX, y: e.clientY, t: performance.now() })
    const onUp = (e: PointerEvent) => {
      if (!down || modeRef.current !== 'globe') return
      const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y)
      const quick = performance.now() - down.t < 600
      down = null
      if (moved > 6 || !quick) return
      const hit = earth.pick(e.clientX, e.clientY)
      if (hit) cbRef.current.onSurfaceClick(hit.lat, hit.lng)
    }
    earth.canvas.addEventListener('pointerdown', onDown)
    earth.canvas.addEventListener('pointerup', onUp)

    return () => {
      cancelAnimationFrame(timelineRef.current)
      ro.disconnect()
      earth.dispose()
      earthRef.current = null
    }
  }, [])

  /**
   * One timeline drives BOTH views with the same zoom level every frame, so the
   * handover is continuous: the globe dives until ~z5.6, the map is already
   * positioned underneath at the identical scale, and opacity follows zoom.
   */
  const runZoom = (opts: {
    lat: number
    lng: number
    from: number
    to: number
    focusFrom: Focus
    focusTo: Focus
    dur: number
    done: () => void
  }) => {
    const earth = earthRef.current!
    const handoff = Math.min(HANDOFF_ZOOM, Math.max(opts.from, opts.to) - 0.4)
    cancelAnimationFrame(timelineRef.current)
    const start = performance.now()
    const frame = (now: number) => {
      const t = Math.min(1, (now - start) / opts.dur)
      const e = easeInOut(t)
      const z = lerp(opts.from, opts.to, e)
      const f = smooth(0, 0.7, e)
      const focus = { fx: lerp(opts.focusFrom.fx, opts.focusTo.fx, f), fy: lerp(opts.focusFrom.fy, opts.focusTo.fy, f) }
      earth.setDrive({ mapZoom: Math.min(z, handoff + FADE_SPAN), lat: opts.lat, ...focus })
      mapRef.current?.jump(opts.lat, opts.lng, z, focus)
      setBlend(z, handoff)
      if (t < 1) timelineRef.current = requestAnimationFrame(frame)
      else opts.done()
    }
    timelineRef.current = requestAnimationFrame(frame)
  }

  useImperativeHandle(ref, () => ({
    flyTo: (place) => {
      const earth = earthRef.current
      const host = hostRef.current
      if (!earth || !host) return
      const focus = focusFor(host.clientWidth)

      if (modeRef.current === 'map') {
        mapRef.current?.flyTo(place, focus)
        return
      }

      go('diving')
      mapRef.current?.setLabels(false)
      const from = earth.homeMapZoom(place.lat)
      // Pre-position the (still invisible) map so its tiles load during the turn.
      mapRef.current?.jump(place.lat, place.lng, HANDOFF_ZOOM, focus)
      const turn = earth.turnDuration(place)
      earth.orient(place, turn)
      // Start descending before the turn finishes so the motion never stops.
      window.setTimeout(() => {
        runZoom({
          lat: place.lat,
          lng: place.lng,
          from,
          to: place.zoom,
          focusFrom: earth.homeCentre,
          focusTo: focus,
          dur: 1500 + Math.max(0, place.zoom - from) * 260,
          done: () => {
            go('map')
            mapRef.current?.setLabels(true)
          },
        })
      }, turn * 0.55)
    },

    reset: () => {
      const earth = earthRef.current
      const host = hostRef.current
      if (!earth || !host || !mapRef.current) return
      go('rising')
      mapRef.current.setLabels(false)
      const v = mapRef.current.view()
      // The map may have been panned: turn the globe to match before zooming out.
      earth.orientInstant(v)
      runZoom({
        lat: v.lat,
        lng: v.lng,
        from: v.zoom,
        to: earth.homeMapZoom(v.lat),
        focusFrom: focusFor(host.clientWidth),
        focusTo: earth.homeCentre,
        dur: 1400 + Math.max(0, v.zoom - 4) * 200,
        done: () => {
          earth.setDrive(null)
          earth.settle()
          go('globe')
        },
      })
    },
  }))

  return (
    <div className="earth-stage" data-mode={mode}>
      <div ref={mapLayerRef} className="earth-stage__map" aria-hidden={mode !== 'map'}>
        <WorldMap ref={mapRef} places={places} selectedId={selected?.id ?? null} onPlaceClick={onPlaceClick} />
      </div>
      <div ref={globeLayerRef} className="earth-stage__globe">
        <div ref={hostRef} className="earth-stage__canvas" />
      </div>
      <button
        ref={hintRef}
        type="button"
        className="earth-hint is-hidden"
        onClick={() => cbRef.current.onRegionClick()}
        aria-label="Phóng to Đồng bằng sông Cửu Long"
      >
        <span className="earth-hint__pulse" aria-hidden="true" />
        <span className="earth-hint__label">ĐBSCL</span>
      </button>
      {mode !== 'map' && (
        <p className="earth-stage__credit">Bề mặt Trái Đất: NASA Blue Marble · Solar System Scope (CC BY 4.0)</p>
      )}
    </div>
  )
}
