/**
 * Browser GPS (Geolocation API) with messages a farmer can act on.
 * The position never leaves the device: it is only used to move the map and place points.
 */
export interface GpsFix {
  lat: number
  lng: number
  /** 68% radius in metres, as reported by the device. */
  accuracy: number
  at: number
}

export type GpsError = 'unsupported' | 'denied' | 'unavailable' | 'timeout' | 'insecure'

export const GPS_ERROR_MSG: Record<GpsError, string> = {
  unsupported: 'Trình duyệt này không hỗ trợ định vị.',
  insecure: 'Định vị chỉ chạy trên trang HTTPS.',
  denied: 'Bạn đã chặn quyền định vị. Bật lại trong cài đặt trình duyệt (biểu tượng ổ khoá cạnh địa chỉ trang).',
  unavailable: 'Chưa bắt được tín hiệu vị trí. Ra chỗ thoáng hoặc bật GPS trên điện thoại rồi thử lại.',
  timeout: 'Định vị quá lâu. Thử lại, hoặc bật GPS/chế độ vị trí chính xác cao.',
}

/** Good enough to place a paddy corner. Phone GPS in the open is usually 3–10 m. */
export const PRECISE_M = 25
/** Beyond this the fix is probably Wi-Fi/cell based — fine for "show my area", not for corners. */
export const COARSE_M = 150

const OPTIONS: PositionOptions = { enableHighAccuracy: true, timeout: 15_000, maximumAge: 5_000 }

function mapError(e: GeolocationPositionError): GpsError {
  if (e.code === e.PERMISSION_DENIED) return 'denied'
  if (e.code === e.TIMEOUT) return 'timeout'
  return 'unavailable'
}

const toFix = (p: GeolocationPosition): GpsFix => ({ lat: p.coords.latitude, lng: p.coords.longitude, accuracy: p.coords.accuracy, at: p.timestamp })

function preflight(): GpsError | null {
  if (!('geolocation' in navigator)) return 'unsupported'
  if (!window.isSecureContext) return 'insecure'
  return null
}

export function locateOnce(): Promise<GpsFix> {
  const bad = preflight()
  if (bad) return Promise.reject(bad)
  return new Promise((resolve, reject) => navigator.geolocation.getCurrentPosition((p) => resolve(toFix(p)), (e) => reject(mapError(e)), OPTIONS))
}

/** Keeps the fix fresh while the user walks the field. Returns a stop function. */
export function watchPosition(onFix: (f: GpsFix) => void, onError: (e: GpsError) => void): () => void {
  const bad = preflight()
  if (bad) {
    onError(bad)
    return () => undefined
  }
  const id = navigator.geolocation.watchPosition((p) => onFix(toFix(p)), (e) => onError(mapError(e)), OPTIONS)
  return () => navigator.geolocation.clearWatch(id)
}

export const formatAccuracy = (m: number) => (m < 1000 ? `±${Math.round(m)} m` : `±${(m / 1000).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} km`)

/** Accuracy circle as a polygon (metres → degrees on the local sphere). */
export function accuracyCircle(fix: GpsFix, steps = 64): GeoJSON.Feature<GeoJSON.Polygon> {
  const dLat = fix.accuracy / 111_320
  const dLng = dLat / Math.cos((fix.lat * Math.PI) / 180)
  const ring: [number, number][] = []
  for (let i = 0; i <= steps; i++) {
    const a = (i / steps) * Math.PI * 2
    ring.push([fix.lng + dLng * Math.cos(a), fix.lat + dLat * Math.sin(a)])
  }
  return { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [ring] } }
}
