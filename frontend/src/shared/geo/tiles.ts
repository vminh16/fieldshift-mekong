/** Raster sources shared by every MapLibre view (landing map, parcel drawing, parcel thumbnail). */
export const IMAGERY_TILES =
  (import.meta.env.VITE_IMAGERY_TILE_URL as string | undefined) ??
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
export const LABEL_TILES =
  'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}'
export const IMAGERY_ATTRIBUTION = 'Ảnh vệ tinh: Esri, Maxar, Earthstar Geographics'
