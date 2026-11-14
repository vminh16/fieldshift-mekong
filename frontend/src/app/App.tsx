import { lazy, Suspense } from 'react'
import { useRoute } from '../shared/router'

// One chunk per screen: the globe (three.js) and the maps (MapLibre) load only where they are used.
const LandingPage = lazy(() => import('../features/landing/LandingPage').then((m) => ({ default: m.LandingPage })))
const FieldsWorkspace = lazy(() => import('../features/fields/FieldsWorkspace').then((m) => ({ default: m.FieldsWorkspace })))
const PlannedScreen = lazy(() => import('../features/shell/PlannedScreen').then((m) => ({ default: m.PlannedScreen })))
const RecommendScreen = lazy(() => import('../features/recommend/RecommendScreen').then((m) => ({ default: m.RecommendScreen })))
const TrackScreen = lazy(() => import('../features/track/TrackScreen').then((m) => ({ default: m.TrackScreen })))
const TwinScreen = lazy(() => import('../features/twin/TwinScreen').then((m) => ({ default: m.TwinScreen })))

export function App() {
  return (
    <Suspense fallback={<div className="route-loading" aria-busy="true" aria-label="Đang tải" />}>
      <Routes />
    </Suspense>
  )
}

function Routes() {
  const route = useRoute()
  const { path } = route

  if (path === '/') return <LandingPage />
  // One workspace for browsing, drawing and editing parcels, so the map survives mode changes.
  if (path === '/ruong' || path.startsWith('/ruong/')) return <FieldsWorkspace route={route} />

  if (path === '/de-xuat') return <RecommendScreen fieldId={route.params.get('thua')} />
  if (path === '/mo-phong') return <TwinScreen fieldId={route.params.get('thua')} sequenceId={route.params.get('chuoi')} />
  if (path === '/theo-doi') return <TrackScreen fieldId={route.params.get('thua')} />
  if (path === '/nguon')
    return (
      <PlannedScreen
        title="Dữ liệu NASA"
        icon="database"
        lead="Mỗi con số trong ứng dụng ghi rõ nguồn, độ phân giải và giới hạn của nó."
        items={['NASA POWER, GPM IMERG, SMAP, NASADEM — trạng thái và thời điểm cập nhật', 'Khác nhau giữa đo tại ruộng, ước lượng vùng và kịch bản', 'Giới hạn: ô lưới vệ tinh không phải số đo tại thửa']}
      />
    )

  return <LandingPage />
}
