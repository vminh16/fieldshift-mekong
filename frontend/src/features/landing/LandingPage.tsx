import { useRef, useState } from 'react'
import { EarthGlobe, type EarthGlobeHandle } from '../globe/EarthGlobe'
import { LocationSearch } from '../location-search/LocationSearch'
import { Starfield } from './Starfield'
import {
  MEKONG_PROVINCES,
  MEKONG_REGION,
  isNearDelta,
  nearestProvince,
  type Place,
} from '../../shared/geo/mekongProvinces'
import { PRECISION_LABEL } from '../../shared/geo/types'
import { reverseGeocode } from '../../shared/geo/geocode'
import './landing.css'

const STEPS = ['Định vị thửa ruộng', 'Khai báo điều kiện canh tác', 'So sánh phương án luân canh']

export function LandingPage() {
  const globe = useRef<EarthGlobeHandle>(null)
  const [selected, setSelected] = useState<Place | null>(null)

  const locate = (place: Place) => {
    setSelected(place)
    globe.current?.flyTo(place)
  }

  const onSurfaceClick = (lat: number, lng: number) => {
    const hit = nearestProvince(lat, lng, 0.6)
    if (hit) return locate(hit)
    if (isNearDelta(lat, lng)) return locate(MEKONG_REGION)
    // Anywhere else: fly there right away, name it once the geocoder answers.
    const id = `pt-${lat.toFixed(3)},${lng.toFixed(3)}`
    locate({ id, name: 'Vị trí đã chọn', context: 'Đang xác định địa danh…', lat, lng, zoom: 7, precision: 'region', source: 'geocoder' })
    reverseGeocode(lat, lng)
      .then((p) =>
        setSelected((cur) =>
          cur?.id === id ? { ...cur, name: p?.name ?? 'Vùng biển / chưa rõ tên', context: p?.context ?? '' } : cur,
        ),
      )
      .catch(() => setSelected((cur) => (cur?.id === id ? { ...cur, context: '' } : cur)))
  }

  const backToGlobe = () => {
    setSelected(null)
    globe.current?.reset()
  }

  return (
    <div className="landing">
      <Starfield />
      <EarthGlobe
        ref={globe}
        places={MEKONG_PROVINCES}
        selected={selected}
        onPlaceClick={locate}
        onSurfaceClick={onSurfaceClick}
        onRegionClick={() => locate(MEKONG_REGION)}
      />
      <div className="landing__veil" aria-hidden="true" />

      <header className="topbar">
        <a className="brand" href="/" aria-label="FieldShift Mekong — trang chủ">
          <svg className="brand__mark" viewBox="0 0 32 32" aria-hidden="true">
            <path d="M16 28V15M16 15c0-5.5-4.2-8.5-9.5-8.5 0 5.5 4.2 8.5 9.5 8.5Zm0 0c0-5.5 4.2-8.5 9.5-8.5 0 5.5-4.2 8.5-9.5 8.5Z" />
          </svg>
          <span className="brand__text">
            <span className="brand__name">FieldShift Mekong</span>
            <span className="brand__tag">Hỗ trợ quyết định luân canh</span>
          </span>
        </a>
        <nav className="topnav" aria-label="Điều hướng chính">
          <a href="#gioi-thieu">Giới thiệu</a>
          <a href="#phuong-phap">Phương pháp</a>
          <a href="#du-lieu">Dữ liệu NASA</a>
        </nav>
      </header>

      <main className="hero">
        <p className="eyebrow">Dữ liệu quan sát Trái Đất · Đồng bằng sông Cửu Long</p>
        <h1 className="hero__title">
          Bắt đầu từ
          <span className="hero__accent">thửa ruộng của bạn.</span>
        </h1>
        <p className="hero__lead">
          Định vị thửa ruộng để so sánh các phương án luân canh cho những vụ tới — dựa trên dữ liệu NASA về
          mưa, nhiệt, độ ẩm đất, cùng điều kiện đất, nước và nguồn lực thực tế của nông hộ.
        </p>
        <LocationSearch onLocate={locate} />
      </main>

      {selected && (
        <aside className="place-card" aria-live="polite" aria-label="Khu vực đã chọn">
          <p className="place-card__kicker">Khu vực đã chọn</p>
          <h2 className="place-card__name">{selected.name}</h2>
          <p className="place-card__unit">
            {selected.context}
          </p>
          <dl className="place-card__meta">
            <div>
              <dt>Toạ độ tâm</dt>
              <dd>
                {Math.abs(selected.lat).toFixed(2)}° {selected.lat >= 0 ? 'B' : 'N'},{' '}
                {Math.abs(selected.lng).toFixed(2)}° {selected.lng >= 0 ? 'Đ' : 'T'}
              </dd>
            </div>
            <div>
              <dt>Độ chính xác</dt>
              <dd>
                {PRECISION_LABEL[selected.precision]}
              </dd>
            </div>
          </dl>
          <div className="place-card__actions">
            <button type="button" className="btn btn--primary" disabled title="Bước tiếp theo đang được thiết kế">
              Khoanh thửa ruộng
            </button>
            <button type="button" className="btn btn--ghost" onClick={backToGlobe}>
              Về toàn cầu
            </button>
          </div>
        </aside>
      )}

      <footer className="steps" aria-label="Các bước sử dụng">
        <ol>
          {STEPS.map((s, i) => (
            <li key={s} className={i === 0 ? 'is-current' : undefined} aria-current={i === 0 ? 'step' : undefined}>
              <span className="steps__num">{String(i + 1).padStart(2, '0')}</span>
              {s}
            </li>
          ))}
        </ol>
      </footer>
    </div>
  )
}
