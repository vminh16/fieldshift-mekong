import type { TwinEvent, TwinWeek } from '../../../../contracts/types'
import { CROP_SHORT, cropTone } from '../../shared/decision/source'

const nf = (n: number) => n.toLocaleString('vi-VN', { maximumFractionDigits: 0 })
const dm = (s: string) => new Date(s).toLocaleDateString('vi-VN', { day: 'numeric', month: 'numeric' })
const cum = (w: TwinWeek | undefined) => w?.irrigation_cum.value ?? null
const WEEK = 7 * 86400000

/** A crop is in the field (cover crop excluded) during the salinity season, per the twin series. */
export const saltRisk = (w: TwinWeek) => Boolean(w.crop && w.crop !== 'fallow_cover' && w.salinity?.in_salinity_season)
/** Weeks the engine marks with medium/high stress risk. */
export const stressRisk = (w: TwinWeek) => w.stress_risk === 'HIGH' || w.stress_risk === 'MEDIUM'

interface Run {
  crop: string
  season: number
  from: number
  to: number
}
function runs(series: TwinWeek[]): Run[] {
  const out: Run[] = []
  series.forEach((w, i) => {
    const last = out[out.length - 1]
    if (!w.crop) return
    // Consecutive rice seasons must stay separate bands: split on the season, not only the crop.
    if (last && last.season === w.season_index && last.to === i - 1) last.to = i
    else out.push({ crop: w.crop, season: w.season_index, from: i, to: i })
  })
  return out
}

interface Lane {
  key: 'a' | 'b'
  label: string
  series: TwinWeek[]
  events: TwinEvent[]
}

/**
 * The main element of the simulation: cumulative irrigation for A and B on one week axis, the
 * salinity season, each chain's crops with sow/harvest markers, and weeks the series flags as risky.
 */
export function TwinTimeline({
  a,
  b,
  index,
  onIndex,
  playing,
  onTogglePlay,
}: {
  a: Lane
  b: Lane
  index: number
  onIndex: (i: number) => void
  playing: boolean
  onTogglePlay: () => void
}) {
  const ref = a.series.length >= b.series.length ? a.series : b.series
  const n = ref.length
  const max = Math.max(1, ...[...a.series, ...b.series].map((w) => cum(w) ?? 0))
  const x = (i: number) => (n > 1 ? (i / (n - 1)) * 100 : 0)
  const t0 = n ? new Date(ref[0].date).getTime() : 0
  const xDate = (d: string) => Math.max(0, Math.min(100, x((new Date(d).getTime() - t0) / WEEK)))
  const y = (v: number) => 100 - (v / max) * 92
  const path = (s: TwinWeek[]) =>
    s
      .map((w, i) => [i, cum(w)] as const)
      .filter(([, v]) => v !== null)
      .map(([i, v], k) => `${k ? 'L' : 'M'}${x(i).toFixed(2)} ${y(v!).toFixed(2)}`)
      .join('')
  const events = a.events.length ? a.events : b.events
  const saltStart = events.find((e) => e.type === 'salinity_season_start')
  const saltEnd = events.find((e) => e.type === 'salinity_season_end')
  // Fall back to the weekly flag if the events are missing.
  const flags = ref.map((w) => Boolean(w.salinity?.in_salinity_season))
  // Inland parcels: the engine sends season events but no week is flagged, so no band.
  const hasSalt = flags.some(Boolean)
  const sFrom = !hasSalt ? null : saltStart ? xDate(saltStart.date) : flags.indexOf(true) >= 0 ? x(flags.indexOf(true)) : null
  const sTo = !hasSalt ? null : saltEnd ? xDate(saltEnd.date) : flags.lastIndexOf(true) >= 0 ? x(flags.lastIndexOf(true)) : null
  const months = ref
    .map((w, i) => ({ d: new Date(w.date), i }))
    .filter(({ d }, k, arr) => k === 0 || d.getMonth() !== arr[k - 1].d.getMonth())
  const date = ref[index] ? new Date(ref[index].date) : null
  const ca = cum(a.series[Math.min(index, a.series.length - 1)])
  const cb = cum(b.series[Math.min(index, b.series.length - 1)])

  return (
    <section className="tw-time" aria-label="Diễn biến theo tuần">
      <div className="tw-time__head">
        <button type="button" className="tw-play" onClick={onTogglePlay} aria-label={playing ? 'Tạm dừng' : 'Phát theo tuần'}>
          {playing ? (
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M8 5v14M16 5v14" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M8 5.5v13l10.5-6.5L8 5.5Z" />
            </svg>
          )}
        </button>
        <p className="tw-time__when">
          <strong>{date?.toLocaleDateString('vi-VN')}</strong>
          <span>
            Nước tưới đến tuần này: <i data-series="a" /> {ca !== null ? `${nf(ca)} mm` : '—'} · <i data-series="b" /> {cb !== null ? `${nf(cb)} mm` : '—'}
          </span>
        </p>
        <ul className="tw-key" aria-label="Chú thích">
          {hasSalt && (
            <>
              <li>
                <i className="tw-key__salt" /> Mùa mặn
              </li>
              <li>
                <i className="tw-key__risk" /> Cây trong ruộng giữa mùa mặn
              </li>
            </>
          )}
          <li>
            <i className="tw-key__stress" /> Tuần rủi ro stress
          </li>
        </ul>
      </div>

      <div className="tw-chart">
        <div className="tw-lane tw-lane--plot">
          <div className="tw-lane__label tw-axis">
            <span>{nf(max)} mm</span>
            <span>0</span>
          </div>
          <div className="tw-chart__plot">
            {sFrom !== null && sTo !== null && (
              <span className="tw-chart__salt" style={{ left: `${sFrom}%`, width: `${Math.max(sTo - sFrom, 0.5)}%` }}>
                Mùa mặn{saltStart && saltEnd ? ` ${dm(saltStart.date)}–${dm(saltEnd.date)}` : ''}
              </span>
            )}
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="Nước tưới cộng dồn của A và B">
              <path className="tw-line tw-line--a" d={path(a.series)} vectorEffect="non-scaling-stroke" />
              <path className="tw-line tw-line--b" d={path(b.series)} vectorEffect="non-scaling-stroke" />
            </svg>
            <span className="tw-chart__end" data-series="a" style={{ top: `${y(cum(a.series[a.series.length - 1]) ?? 0)}%` }}>
              A {nf(cum(a.series[a.series.length - 1]) ?? 0)}
            </span>
            <span className="tw-chart__end" data-series="b" style={{ top: `${y(cum(b.series[b.series.length - 1]) ?? 0)}%` }}>
              B {nf(cum(b.series[b.series.length - 1]) ?? 0)}
            </span>
            <span className="tw-chart__cursor" style={{ left: `${x(index)}%` }} />
          </div>
        </div>

        {[a, b].map((lane) => (
          <div key={lane.key} className="tw-lane">
            <div className="tw-lane__label">
              <span className="tw-side__tag" data-series={lane.key}>
                {lane.key.toUpperCase()}
              </span>
              <span className="tw-lane__name">{lane.label}</span>
            </div>
            <div className="tw-bands__row" aria-label={`Lịch vụ ${lane.label}`}>
              {runs(lane.series).map((r) => (
                <span key={r.from} className="tw-band" data-tone={cropTone(r.crop)} style={{ left: `${x(r.from)}%`, width: `${Math.max(x(r.to + 1) - x(r.from), 1.5)}%` }}>
                  {CROP_SHORT[r.crop] ?? r.crop}
                </span>
              ))}
              {lane.series.map((w, i) =>
                saltRisk(w) ? <span key={`r${i}`} className="tw-risk" style={{ left: `${x(i)}%`, width: `${x(1)}%` }} title={`Tuần ${dm(w.date)}: cây trong ruộng giữa mùa mặn`} /> : null,
              )}
              {lane.series.map((w, i) => (stressRisk(w) ? <span key={`s${i}`} className="tw-stress" style={{ left: `${x(i + 0.5)}%` }} title={`Tuần ${dm(w.date)}: rủi ro stress`} /> : null))}
              {lane.events
                .filter((e) => e.type === 'sow' || e.type === 'harvest')
                .map((e) => (
                  <span
                    key={`${e.type}${e.date}`}
                    className="tw-ev"
                    data-type={e.type}
                    style={{ left: `${xDate(e.date)}%` }}
                    title={`${e.type === 'sow' ? 'Gieo' : 'Thu hoạch'} ${CROP_SHORT[e.crop ?? ''] ?? ''} ${dm(e.date)}`}
                  />
                ))}
            </div>
          </div>
        ))}

        <div className="tw-lane">
          <div className="tw-lane__label" />
          <div className="tw-months" aria-hidden="true">
            {months.map(({ d, i }) => (
              <span key={i} style={{ left: `${x(i)}%` }}>
                T{d.getMonth() + 1}
                {d.getMonth() === 0 || i === 0 ? <small> {d.getFullYear()}</small> : null}
              </span>
            ))}
          </div>
        </div>
        <input
          className="tw-scrub"
          type="range"
          min={0}
          max={Math.max(0, n - 1)}
          step={1}
          value={index}
          onChange={(e) => onIndex(Number(e.target.value))}
          aria-label="Chọn tuần"
          aria-valuetext={date ? date.toLocaleDateString('vi-VN') : undefined}
        />
      </div>
    </section>
  )
}
