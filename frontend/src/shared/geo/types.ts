export type Precision = 'country' | 'region' | 'province' | 'city' | 'district' | 'street' | 'address'

export interface Place {
  id: string
  name: string
  /** Second line under the name: admin hierarchy, country, merger note… */
  context: string
  lat: number
  lng: number
  /** Web-map zoom level to land on (fractional). */
  zoom: number
  precision: Precision
  source: 'gazetteer' | 'geocoder'
}

export const PRECISION_LABEL: Record<Precision, string> = {
  country: 'Cấp quốc gia',
  region: 'Cấp vùng',
  province: 'Ước lượng cấp tỉnh',
  city: 'Cấp thành phố',
  district: 'Cấp quận/huyện',
  street: 'Cấp đường phố',
  address: 'Theo địa chỉ',
}
