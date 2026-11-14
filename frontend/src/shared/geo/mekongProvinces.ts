/**
 * Gazetteer for the Mekong Delta (ĐBSCL).
 *
 * Since 1 July 2025 the 13 former delta provinces were merged into 6 units
 * (Nghị quyết 202/2025/QH15). Users still search by the familiar former names,
 * so every former province is kept as its own entry and points to the unit it
 * now belongs to. Coordinates are approximate centroids — good enough to fly
 * the camera, NOT a parcel location.
 */
import type { Place } from './types'

export type { Place }

type Seed = [id: string, name: string, currentUnit: string, lat: number, lng: number]

const SEEDS: Seed[] = [
  ['an-giang', 'An Giang', 'An Giang', 10.52, 105.13],
  ['kien-giang', 'Kiên Giang', 'An Giang', 9.95, 105.2],
  ['can-tho', 'Cần Thơ', 'TP. Cần Thơ', 10.08, 105.6],
  ['hau-giang', 'Hậu Giang', 'TP. Cần Thơ', 9.78, 105.62],
  ['soc-trang', 'Sóc Trăng', 'TP. Cần Thơ', 9.6, 105.97],
  ['dong-thap', 'Đồng Tháp', 'Đồng Tháp', 10.56, 105.65],
  ['tien-giang', 'Tiền Giang', 'Đồng Tháp', 10.36, 106.3],
  ['vinh-long', 'Vĩnh Long', 'Vĩnh Long', 10.15, 105.98],
  ['ben-tre', 'Bến Tre', 'Vĩnh Long', 10.12, 106.45],
  ['tra-vinh', 'Trà Vinh', 'Vĩnh Long', 9.82, 106.3],
  ['bac-lieu', 'Bạc Liêu', 'Cà Mau', 9.3, 105.62],
  ['ca-mau', 'Cà Mau', 'Cà Mau', 9.05, 105.05],
  ['long-an', 'Long An', 'Tây Ninh', 10.68, 106.2],
]

export const MEKONG_PROVINCES: Place[] = SEEDS.map(([id, name, currentUnit, lat, lng]) => {
  const isFormer = currentUnit.replace('TP. ', '') !== name
  return {
    id,
    name,
    context: isFormer ? `Tỉnh cũ · nay thuộc ${currentUnit}, Việt Nam` : `${currentUnit}, Việt Nam`,
    lat,
    lng,
    zoom: 9.6,
    precision: 'province',
    source: 'gazetteer',
  }
})

export const MEKONG_REGION: Place = {
  id: 'mekong-region',
  name: 'Đồng bằng sông Cửu Long',
  context: '13 tỉnh cũ · 6 đơn vị hành chính hiện hành',
  lat: 9.95,
  lng: 105.75,
  zoom: 8.2,
  precision: 'region',
  source: 'gazetteer',
}

export const SUGGESTED_IDS = ['soc-trang', 'tra-vinh', 'an-giang', 'ca-mau']

/** Lower-case, strip Vietnamese diacritics so "soc trang" matches "Sóc Trăng". */
export function normalize(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'd')
    .replace(/^(tinh|thanh pho|tp\.?)\s+/, '')
    .trim()
}

export function searchGazetteer(query: string): Place[] {
  const q = normalize(query)
  if (!q) return []
  return MEKONG_PROVINCES.filter((p) => {
    const n = normalize(p.name)
    return n.startsWith(q) || n.includes(q)
  })
}

/** Nearest province to a clicked point, if the click is inside the delta. */
export function nearestProvince(lat: number, lng: number, maxDeg = 0.45): Place | null {
  let best: Place | null = null
  let bestD = Infinity
  for (const p of MEKONG_PROVINCES) {
    const d = Math.hypot(p.lat - lat, (p.lng - lng) * Math.cos((lat * Math.PI) / 180))
    if (d < bestD) {
      bestD = d
      best = p
    }
  }
  return bestD <= maxDeg ? best : null
}

/** Roughly southern Vietnam — a click here from far away means "the delta". */
export function isNearDelta(lat: number, lng: number): boolean {
  return lat > 7 && lat < 13 && lng > 103 && lng < 108.5
}
