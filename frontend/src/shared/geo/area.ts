/** Geodesic polygon area (m²) on the WGS84 mean sphere — same method as Turf/Leaflet.draw. */
const R = 6_378_137
const rad = (d: number) => (d * Math.PI) / 180

export function ringAreaM2(ring: [number, number][]): number {
  const n = ring.length
  if (n < 3) return 0
  let sum = 0
  for (let i = 0; i < n; i++) {
    const [lng1, lat1] = ring[i]
    const [lng2, lat2] = ring[(i + 1) % n]
    sum += rad(lng2 - lng1) * (2 + Math.sin(rad(lat1)) + Math.sin(rad(lat2)))
  }
  return Math.abs((sum * R * R) / 2)
}

export function ringCentroid(ring: [number, number][]): { lat: number; lng: number } {
  const lng = ring.reduce((a, p) => a + p[0], 0) / ring.length
  const lat = ring.reduce((a, p) => a + p[1], 0) / ring.length
  return { lat, lng }
}

/** True if segment (a,b) properly crosses (c,d). */
function crosses(a: number[], b: number[], c: number[], d: number[]) {
  const o = (p: number[], q: number[], r: number[]) => Math.sign((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))
  return o(a, b, c) * o(a, b, d) < 0 && o(c, d, a) * o(c, d, b) < 0
}

/** Would appending `next` to the open outline make its new edge cross an earlier one? */
export function wouldSelfIntersect(ring: [number, number][], next: [number, number]): boolean {
  if (ring.length < 2) return false
  const last = ring[ring.length - 1]
  // Skip the edge that shares `last` with the new segment.
  for (let i = 0; i < ring.length - 2; i++) {
    if (crosses(last, next, ring[i], ring[i + 1])) return true
  }
  return false
}

export const formatHa = (ha: number) =>
  ha < 0.1 ? `${Math.round(ha * 10_000).toLocaleString('vi-VN')} m²` : `${ha.toLocaleString('vi-VN', { maximumFractionDigits: 2 })} ha`
