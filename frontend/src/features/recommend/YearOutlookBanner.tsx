import { PHASE_VI, type YearOutlook } from '../../shared/decision/yearOutlook'
import './outlook.css'

const nf = (n: number) => n.toLocaleString('vi-VN', { maximumFractionDigits: 0 })

/** "Mùa khô tới sẽ giống năm nào": ENSO analog years. A statistical signal, never a forecast. */
export function YearOutlookBanner({ yo, compact = false, action }: { yo: YearOutlook; compact?: boolean; action?: React.ReactNode }) {
  const r = yo.dry_season_rain
  const phase = yo.enso ? PHASE_VI[yo.enso.phase] ?? yo.enso.phase : null
  if (compact) {
    return (
      <p className="yo yo--compact" role="note">
        {phase && <span className="yo__chip" data-phase={yo.enso!.phase}>{phase}</span>}
        <span>{yo.headline_vi}</span>
        <span className="yo__fine">Tín hiệu thống kê, không phải dự báo.</span>
      </p>
    )
  }
  return (
    <section className="yo" aria-labelledby="yo-title">
      <div className="yo__head">
        {phase && (
          <span className="yo__chip" data-phase={yo.enso!.phase}>
            {phase}
          </span>
        )}
        <p className="yo__kicker">Mùa khô tới</p>
      </div>
      <h2 id="yo-title" className="yo__title">
        {yo.headline_vi}
      </h2>
      <dl className="yo__facts">
        {yo.analog_labels_vi.length > 0 && (
          <div>
            <dt>Giống các năm</dt>
            <dd>{yo.analog_labels_vi.join(' · ')}</dd>
          </div>
        )}
        {r.analog_median_mm !== null && r.all_years_median_mm !== null && (
          <div>
            <dt>Mưa mùa khô (T12–T4) ở ruộng này</dt>
            <dd>
              Những năm đó {nf(r.analog_median_mm)} mm · bình thường {nf(r.all_years_median_mm)} mm
              {r.ratio !== null && <small> ({nf(r.ratio * 100)}% so với bình thường)</small>}
            </dd>
          </div>
        )}
      </dl>
      <p className="yo__note">
        <strong>Đây là tín hiệu thống kê, không phải dự báo.</strong> {yo.skill.note_vi}
      </p>
      <p className="yo__src">
        Nguồn: {[yo.enso && `${yo.enso.source}, ONI ${yo.enso.value.toLocaleString('vi-VN')} °C (tháng ${yo.enso.centered_month})`, ...r.sources].filter(Boolean).join(' · ')}
      </p>
      {action}
    </section>
  )
}
