import { normalize, searchGazetteer } from './mekongProvinces'
import type { Place, Precision } from './types'

/**
 * Place search = local Mekong gazetteer (instant, offline, knows former
 * province names) + a worldwide geocoder for everything else.
 *
 * Default geocoder: Photon (komoot), built on OpenStreetMap — free, no key,
 * CORS-enabled. What the user types is sent to that service. Override with
 * VITE_GEOCODER_URL, or set it to "off" to search the gazetteer only.
 */
const RAW_URL = import.meta.env.VITE_GEOCODER_URL as string | undefined
const GEOCODER_URL = RAW_URL === 'off' ? null : RAW_URL || 'https://photon.komoot.io/api/'

interface PhotonFeature {
  geometry: { coordinates: [number, number] }
  properties: {
    osm_id: number
    osm_type: string
    type?: string
    name?: string
    street?: string
    housenumber?: string
    city?: string
    district?: string
    county?: string
    state?: string
    country?: string
    extent?: [number, number, number, number] // minLon, maxLat, maxLon, minLat
  }
}

const PRECISION_BY_TYPE: Record<string, { precision: Precision; zoom: number }> = {
  country: { precision: 'country', zoom: 5 },
  state: { precision: 'province', zoom: 7.5 },
  county: { precision: 'district', zoom: 10 },
  city: { precision: 'city', zoom: 11.5 },
  locality: { precision: 'district', zoom: 13 },
  district: { precision: 'district', zoom: 13 },
  street: { precision: 'street', zoom: 15.5 },
  house: { precision: 'address', zoom: 17 },
}

/** Zoom that fits a bounding box into roughly half the viewport. */
function zoomForExtent([minLon, maxLat, maxLon, minLat]: [number, number, number, number]): number {
  const avail = Math.max(320, window.innerWidth * 0.45)
  const lonSpan = Math.max(0.002, Math.abs(maxLon - minLon))
  const latSpan = Math.max(0.002, Math.abs(maxLat - minLat)) / Math.cos((((maxLat + minLat) / 2) * Math.PI) / 180)
  const z = Math.log2((avail * 360) / (256 * Math.max(lonSpan, latSpan * 1.3)))
  return Math.min(16.5, Math.max(3, z))
}

function toPlace(f: PhotonFeature): Place {
  const p = f.properties
  const [lng, lat] = f.geometry.coordinates
  const kind = PRECISION_BY_TYPE[p.type ?? ''] ?? { precision: 'district' as Precision, zoom: 12 }
  const name = p.name ?? ([p.street, p.housenumber].filter(Boolean).join(' ') || 'Không tên')
  const context = [p.district, p.city, p.county, p.state, p.country]
    .filter((x, i, arr): x is string => Boolean(x) && x !== name && arr.indexOf(x) === i)
    .slice(-3)
    .join(', ')
  return {
    id: `osm-${p.osm_type}${p.osm_id}`,
    name,
    context,
    lat,
    lng,
    zoom: p.extent ? zoomForExtent(p.extent) : kind.zoom,
    precision: kind.precision,
    source: 'geocoder',
  }
}

export async function searchPlaces(query: string, signal?: AbortSignal): Promise<Place[]> {
  const q = query.trim()
  if (!q) return []
  const local = searchGazetteer(q)
  if (!GEOCODER_URL || q.length < 2) return local

  const url = new URL(GEOCODER_URL)
  url.searchParams.set('q', q)
  url.searchParams.set('limit', '6')
  // No location bias: ranking by prominence keeps "Paris" → Paris, France.
  // Mekong provinces still come first via the local gazetteer above.

  const res = await fetch(url, { signal, headers: { Accept: 'application/json' } })
  if (!res.ok) throw new Error(`Geocoder HTTP ${res.status}`)
  const data = (await res.json()) as { features: PhotonFeature[] }
  // Drop remote hits that duplicate a gazetteer province.
  const localNames = new Set(local.map((p) => normalize(p.name)))
  const seen = new Set<string>()
  const remote = data.features
    .map(toPlace)
    .filter((p) => !localNames.has(normalize(p.name)) && !seen.has(p.id) && Boolean(seen.add(p.id)))
  return [...local, ...remote]
}

export const hasOnlineGeocoder = Boolean(GEOCODER_URL)

/** Name for a clicked point (country / province / city), or null over open sea. */
export async function reverseGeocode(lat: number, lng: number, signal?: AbortSignal): Promise<Place | null> {
  if (!GEOCODER_URL) return null
  const url = new URL(GEOCODER_URL.replace(/\/api\/?$/, '/reverse'))
  url.searchParams.set('lat', lat.toFixed(5))
  url.searchParams.set('lon', lng.toFixed(5))
  url.searchParams.set('limit', '1')
  url.searchParams.set('radius', '30')
  const res = await fetch(url, { signal, headers: { Accept: 'application/json' } })
  if (!res.ok) return null
  const data = (await res.json()) as { features: PhotonFeature[] }
  const f = data.features[0]
  if (!f) return null
  const p = f.properties
  // A click on a spinning globe means "this area", so name it by the broader unit.
  const name = p.state ?? p.county ?? p.city ?? p.country ?? p.name ?? 'Vị trí đã chọn'
  const context = [p.country].filter((x): x is string => Boolean(x) && x !== name).join(', ')
  return { ...toPlace(f), name, context, lat, lng }
}
