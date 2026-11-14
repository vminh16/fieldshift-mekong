import { useEffect, useRef, useState } from 'react'
import type { TwinWeek } from '../../../../../contracts/types'
import { CROP_SHORT } from '../../../shared/decision/source'
import { SoilColumn } from '../SoilColumn'
import { FieldScene, type Anchors } from './FieldScene'
import { stateAt } from './weekState'

const STAGE_VI: Record<string, string> = { initial: 'Mới gieo', development: 'Đang phát triển', mid: 'Sinh trưởng mạnh', late: 'Chín, sắp thu' }
const nf = (n: number, d = 0) => n.toLocaleString('vi-VN', { maximumFractionDigits: d })

function webglOk() {
  try {
    const c = document.createElement('canvas')
    return Boolean(c.getContext('webgl2') || c.getContext('webgl'))
  } catch {
    return false
  }
}

/**
 * 3D cut-away of the parcel for a (fractional) week position. The picture eases between weeks;
 * the floating labels show the engine's values for the current whole week.
 */
export function FieldScene3D({ series, pos }: { series: TwinWeek[]; pos: number }) {
  const host = useRef<HTMLDivElement>(null)
  const sceneRef = useRef<FieldScene | null>(null)
  const pondRef = useRef<HTMLSpanElement>(null)
  const rootRef = useRef<HTMLSpanElement>(null)
  const canalRef = useRef<HTMLSpanElement>(null)
  const depthRefs = useRef<(HTMLSpanElement | null)[]>([])
  const [gl] = useState(webglOk)

  useEffect(() => {
    if (!gl || !host.current) return
    const scene = new FieldScene(host.current)
    sceneRef.current = scene
    const place = (el: HTMLElement | null, a: { x: number; y: number; visible?: boolean }) => {
      if (!el) return
      el.style.transform = `translate(${a.x.toFixed(1)}px, ${a.y.toFixed(1)}px)`
      el.style.opacity = a.visible === false ? '0' : '1'
    }
    scene.onFrame = (a: Anchors) => {
      place(pondRef.current, a.pond)
      place(rootRef.current, a.root)
      place(canalRef.current, a.canal)
      a.depth.forEach((d, i) => place(depthRefs.current[i], d))
    }
    return () => {
      scene.dispose()
      sceneRef.current = null
    }
  }, [gl])

  useEffect(() => {
    sceneRef.current?.setTarget(stateAt(series, pos))
  }, [series, pos])

  const week = series[Math.max(0, Math.min(series.length - 1, Math.floor(pos)))]
  if (!gl) return <SoilColumn week={week} />

  const crop = week?.crop ? (CROP_SHORT[week.crop] ?? week.crop) : null
  const stage = week?.stage ? STAGE_VI[week.stage as string] : null
  const pond = week?.ponding_mm.value
  const root = week?.root_depth_m.value
  const wet = week?.root_zone_water.value
  const salt = week?.salinity

  return (
    <div className="scene3d">
      <div ref={host} className="scene3d__canvas" />
      <p className="scene3d__caption">
        {crop ? (
          <>
            <strong>{crop}</strong> · {stage ?? 'Đang trồng'}
          </>
        ) : (
          <>
            <strong>Đất trống</strong> · làm đất, chuẩn bị vụ sau
          </>
        )}
      </p>
      <span ref={pondRef} className="scene3d__tag">
        Nước mặt ruộng {pond ? `${nf(pond)} mm` : ''}
      </span>
      <span ref={rootRef} className="scene3d__tag scene3d__tag--root">
        Rễ {root ? `${nf(root, 1)} m` : ''}
        {wet != null && <b> · ẩm {Math.round(wet * 100)}%</b>}
      </span>
      <span ref={canalRef} className="scene3d__tag scene3d__tag--canal" data-salt={salt?.in_salinity_season || undefined}>
        Kênh · {salt?.value != null ? `${nf(salt.value, 1)} dS/m` : 'mặn chưa đo'}
        {salt?.in_salinity_season && <b> · mùa mặn</b>}
      </span>
      {[0, 0.4, 0.8, 1.2].map((d, i) => (
        <span key={d} ref={(el) => void (depthRefs.current[i] = el)} className="scene3d__depth">
          {nf(d, 1)} m
        </span>
      ))}
      <span className="scene3d__hint" aria-hidden="true">
        Kéo để xoay
      </span>
    </div>
  )
}
