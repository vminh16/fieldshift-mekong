import { useEffect, useRef } from 'react'

interface Star {
  x: number
  y: number
  r: number
  base: number
  /** Parallax layer: 0 = far (slow, dim) … 2 = near (faster, brighter). */
  layer: number
  phase: number
  speed: number
  tint: string
}

/** Pixels per second each layer drifts (right → left, a touch upward). */
const DRIFT = [2.2, 4.5, 8]
const TINTS = ['255,255,255', '214,232,255', '255,244,226', '200,244,232']

function makeStars(w: number, h: number): Star[] {
  const count = Math.round(Math.min(320, (w * h) / 5200))
  const rand = (a: number, b: number) => a + Math.random() * (b - a)
  return Array.from({ length: count }, () => {
    const layer = Math.random() < 0.62 ? 0 : Math.random() < 0.75 ? 1 : 2
    return {
      x: rand(0, w),
      y: rand(0, h),
      r: layer === 0 ? rand(0.35, 0.7) : layer === 1 ? rand(0.6, 1.05) : rand(0.9, 1.5),
      base: layer === 0 ? rand(0.25, 0.5) : layer === 1 ? rand(0.45, 0.75) : rand(0.7, 0.95),
      layer,
      phase: rand(0, Math.PI * 2),
      speed: rand(0.4, 1.4),
      tint: TINTS[Math.floor(Math.random() * TINTS.length)],
    }
  })
}

/** Slowly drifting, softly twinkling star field drawn behind the globe. */
export function Starfield() {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = ref.current!
    const ctx = canvas.getContext('2d')!
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let stars: Star[] = []
    let w = 0
    let h = 0
    let raf = 0
    let last = performance.now()

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio, 2)
      w = canvas.clientWidth
      h = canvas.clientHeight
      canvas.width = Math.round(w * dpr)
      canvas.height = Math.round(h * dpr)
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      stars = makeStars(w, h)
    }

    const draw = (now: number) => {
      const dt = Math.min(0.05, (now - last) / 1000)
      last = now
      ctx.clearRect(0, 0, w, h)
      const t = now / 1000
      for (const s of stars) {
        if (!reduce) {
          s.x -= DRIFT[s.layer] * dt
          s.y -= DRIFT[s.layer] * 0.18 * dt
          if (s.x < -4) s.x = w + 4
          if (s.y < -4) s.y = h + 4
        }
        const twinkle = reduce ? 1 : 0.72 + 0.28 * Math.sin(t * s.speed * 1.6 + s.phase)
        const a = s.base * twinkle
        ctx.fillStyle = `rgba(${s.tint},${a})`
        ctx.beginPath()
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
        ctx.fill()
        if (s.layer === 2) {
          // soft halo on the nearest, brightest stars
          ctx.fillStyle = `rgba(${s.tint},${a * 0.12})`
          ctx.beginPath()
          ctx.arc(s.x, s.y, s.r * 3.2, 0, Math.PI * 2)
          ctx.fill()
        }
      }
      raf = requestAnimationFrame(draw)
    }

    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(canvas)
    raf = requestAnimationFrame(draw)
    return () => {
      ro.disconnect()
      cancelAnimationFrame(raf)
    }
  }, [])

  return <canvas ref={ref} className="starfield" aria-hidden="true" />
}
