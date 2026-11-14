import type { LocalField } from '../../shared/fields/store'

/** The parcel's own outline as a small icon — real geometry, no map tiles needed. */
export function FieldThumb({ field, size = 44 }: { field: LocalField; size?: number }) {
  const pad = 6
  let content
  if (field.ring && field.ring.length >= 3) {
    const k = Math.cos((field.centroid.lat * Math.PI) / 180)
    const pts = field.ring.map(([lng, lat]) => [lng * k, -lat])
    const xs = pts.map((p) => p[0])
    const ys = pts.map((p) => p[1])
    const minX = Math.min(...xs)
    const minY = Math.min(...ys)
    const span = Math.max(Math.max(...xs) - minX, Math.max(...ys) - minY) || 1
    const scale = (size - pad * 2) / span
    const offX = (size - (Math.max(...xs) - minX) * scale) / 2
    const offY = (size - (Math.max(...ys) - minY) * scale) / 2
    const d = pts.map(([x, y], i) => `${i ? 'L' : 'M'}${(offX + (x - minX) * scale).toFixed(1)} ${(offY + (y - minY) * scale).toFixed(1)}`).join('') + 'Z'
    content = <path d={d} className="thumb__shape" />
  } else {
    content = <path d={`M${size / 2} ${size - 10}s-9-8.5-9-15a9 9 0 0 1 18 0c0 6.5-9 15-9 15Z`} className="thumb__shape" />
  }
  return (
    <svg className="thumb" width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
      {content}
    </svg>
  )
}
