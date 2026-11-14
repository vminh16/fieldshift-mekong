import type { TwinWeek } from '../../../../contracts/types'
import { CROP_SHORT, cropTone } from '../../shared/decision/source'

const nf = (n: number) => n.toLocaleString('vi-VN', { maximumFractionDigits: 0 })
const cum = (w: TwinWeek | undefined) => w?.irrigation_cum.value ?? null

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

/**
 * Shared week axis for both sides: cumulative irrigation lines (the running cost of each chain),
 * salinity season band, each chain's crops, and the scrubber that drives both cross-sections.
 */
export function TwinTimeline({
  a,
  b,
  labelA,
  labelB,
  totalA,
  totalB,
  infeasible = false,
  index,
  onIndex,
  playing,
  onTogglePlay,
}: {
  a: TwinWeek[]
  b: TwinWeek[]
  labelA: string
  labelB: string
  /** Engine's whole-horizon irrigation for the selected weather year (Twin.members[].irrigation_mm). */
  totalA: number | null
  totalB: number | null
  /** A side whose chain the engine marked NOT_FEASIBLE: its water total is not a saving. */
  infeasible?: boolean
  index: number
  onIndex: (i: number) => void
  playing: boolean
  onTogglePlay: () => void
}) {
  const n = Math.max(a.length, b.length)
  const max = Math.max(1, ...[...a, ...b].map((w) => cum(w) ?? 0))
  const x = (i: number) => (n > 1 ? (i / (n - 1)) * 100 : 0)
  const path = (s: TwinWeek[]) =>
    s
      .map((w, i) => [i, cum(w)] as const)
      .filter(([, v]) => v !== null)
      .map(([i, v], k) => `${k ? 'L' : 'M'}${x(i).toFixed(2)} ${(100 - (v! / max) * 92).toFixed(2)}`)
      .join('')
  const salt = (a.length >= b.length ? a : b).map((w) => Boolean(w.salinity?.in_salinity_season))
  const saltFrom = salt.indexOf(true)
  const saltTo = salt.lastIndexOf(true)
  const ref = a.length >= b.length ? a : b
  const months = ref
    .map((w, i) => ({ d: new Date(w.date), i }))
    .filter(({ d }, k, arr) => k === 0 || d.getMonth() !== arr[k - 1].d.getMonth())

  const ca = cum(a[Math.min(index, a.length - 1)])
  const cb = cum(b[Math.min(index, b.length - 1)])
  const date = ref[index] ? new Date(ref[index].date) : null

  return (
    <section className="tw-time" aria-label="Diễn biến theo tuần">
      <div className="tw-time__head">
        <button type="button" className="tw-play" onClick={onTogglePlay} aria-label={playing ? 'Tạm dừng' : 'Phát'}>
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
        <div className="tw-time__when">
          <strong>Tuần {index + 1}</strong>
          <span>{date?.toLocaleDateString('vi-VN', { day: 'numeric', month: 'numeric', year: 'numeric' })}</span>
        </div>
        <dl className="tw-time__read" aria-label="Nước tưới cả 3 vụ trong năm thời tiết này">
          <div>
            <dt>
              <i data-series="a" />
              {labelA}
            </dt>
            <dd>{totalA !== null ? `${nf(totalA)} mm` : '—'}</dd>
          </div>
          <div>
            <dt>
              <i data-series="b" />
              {labelB}
            </dt>
            <dd>{totalB !== null ? `${nf(totalB)} mm` : '—'}</dd>
          </div>
          {totalA !== null && totalB !== null && (
            <div className="tw-time__diff" data-good={(!infeasible && totalB < totalA) || undefined}>
              <dt>Chênh lệch cả 3 vụ</dt>
              <dd>
                {infeasible ? (
                  <span className="tw-time__na">Không so — có chuỗi không khả thi</span>
                ) : (
                  <>
                    {totalB <= totalA ? '−' : '+'}
                    {nf(Math.abs(totalB - totalA))} mm
                  </>
                )}
              </dd>
            </div>
          )}
        </dl>
      </div>

      <div className="tw-chart">
        <p className="tw-chart__title">
          Nước tưới cộng dồn trong từng vụ · Dự kiến
          <span>
            Tuần này: {labelA} {ca !== null ? `${nf(ca)} mm` : '—'} · {labelB} {cb !== null ? `${nf(cb)} mm` : '—'}
          </span>
        </p>
        <div className="tw-chart__plot">
          {saltFrom >= 0 && (
            <span className="tw-chart__salt" style={{ left: `${x(saltFrom)}%`, width: `${x(saltTo) - x(saltFrom)}%` }}>
              Mùa mặn
            </span>
          )}
          <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
            <path className="tw-line tw-line--a" d={path(a)} vectorEffect="non-scaling-stroke" />
            <path className="tw-line tw-line--b" d={path(b)} vectorEffect="non-scaling-stroke" />
          </svg>
          <span className="tw-chart__cursor" style={{ left: `${x(index)}%` }} />
        </div>
        <div className="tw-bands">
          {[
            ['a', a, labelA],
            ['b', b, labelB],
          ].map(([key, s, label]) => (
            <div key={key as string} className="tw-bands__row" aria-label={`Lịch vụ ${label as string}`}>
              {runs(s as TwinWeek[]).map((r) => (
                <span key={r.from} data-tone={cropTone(r.crop)} style={{ left: `${x(r.from)}%`, width: `${Math.max(x(r.to) - x(r.from), 1.5)}%` }}>
                  {CROP_SHORT[r.crop] ?? r.crop}
                </span>
              ))}
            </div>
          ))}
        </div>
        <div className="tw-months" aria-hidden="true">
          {months.map(({ d, i }) => (
            <span key={i} style={{ left: `${x(i)}%` }}>
              T{d.getMonth() + 1}
            </span>
          ))}
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
          aria-valuetext={date ? `Tuần ${index + 1}, ${date.toLocaleDateString('vi-VN')}` : undefined}
        />
      </div>
    </section>
  )
}
