import type { Season } from '../../../../contracts/types'
import { CROP_SHORT, cropTone } from '../../shared/decision/source'

const nf = (n: number) => n.toLocaleString('vi-VN', { maximumFractionDigits: 0 })
const day = (iso: string) => {
  const d = new Date(iso)
  return `${d.getDate()}/${d.getMonth() + 1}`
}
const t = (iso: string) => new Date(iso).getTime()

// ---------- rotation ribbon ----------
export interface RibbonRow {
  key: string
  label: string
  seasons: Season[]
  emphasis?: boolean
}

/** Crops laid on a shared calendar. Position = real sow→harvest dates, so gaps between crops are visible. */
export function RotationRibbon({ rows }: { rows: RibbonRow[] }) {
  const all = rows.flatMap((r) => r.seasons)
  const start = new Date(Math.min(...all.map((s) => t(s.sow))))
  start.setDate(1)
  const end = new Date(Math.max(...all.map((s) => t(s.harvest))))
  end.setMonth(end.getMonth() + 1, 1)
  const span = end.getTime() - start.getTime()
  const pct = (ms: number) => `${((ms - start.getTime()) / span) * 100}%`

  const months: Date[] = []
  for (const m = new Date(start); m < end; m.setMonth(m.getMonth() + 1)) months.push(new Date(m))

  return (
    <div className="ribbon" role="img" aria-label={rows.map((r) => `${r.label}: ${r.seasons.map((s) => CROP_SHORT[s.crop] ?? s.crop_name_vi).join(' – ')}`).join('. ')}>
      <div className="ribbon__axis" aria-hidden="true">
        {months.map((m, i) => (
          <span key={m.toISOString()} style={{ left: pct(m.getTime()) }} data-minor={i % 2 === 1 || undefined}>
            {m.getMonth() === 0 || i === 0 ? `Th${m.getMonth() + 1}/${String(m.getFullYear()).slice(2)}` : `Th${m.getMonth() + 1}`}
          </span>
        ))}
      </div>
      {rows.map((r) => (
        <div key={r.key} className="ribbon__row" data-emphasis={r.emphasis || undefined}>
          <span className="ribbon__label">{r.label}</span>
          <div className="ribbon__track">
            {r.seasons.map((s) => {
              const name = CROP_SHORT[s.crop] ?? s.crop_name_vi
              const tip = `${s.window_name_vi}: ${name} · gieo ${day(s.sow)}, thu ${day(s.harvest)}`
              return (
                <span
                  key={s.index}
                  className="ribbon__band"
                  data-tone={cropTone(s.crop)}
                  style={{ left: pct(t(s.sow)), width: `calc(${((t(s.harvest) - t(s.sow)) / span) * 100}% - 2px)` }}
                  tabIndex={0}
                  data-tip={tip}
                  aria-label={tip}
                >
                  <span className="ribbon__crop">{name}</span>
                  {r.emphasis && <span className="ribbon__dates">{day(s.sow)} – {day(s.harvest)}</span>}
                </span>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

// ---------- horizontal comparison bars ----------
export interface Bar {
  label: string
  value: number
  tone: 'base' | 'pick'
}

export function CompareBars({ bars, unit }: { bars: Bar[]; unit: string }) {
  const max = Math.max(...bars.map((b) => b.value)) || 1
  return (
    <div className="hbars">
      {bars.map((b) => (
        <div key={b.label} className="hbars__row">
          <span className="hbars__label">{b.label}</span>
          <span className="hbars__track">
            <span
              className="hbars__bar"
              data-tone={b.tone}
              style={{ width: `${(b.value / max) * 100}%` }}
              tabIndex={0}
              data-tip={`${b.label}: ${nf(b.value)} ${unit} ≈ ${nf(b.value * 10)} m³/ha`}
            />
          </span>
          <span className="hbars__value">
            {nf(b.value)} <small>{unit}</small>
          </span>
        </div>
      ))}
    </div>
  )
}

// ---------- paired vertical bars (normal vs dry year) ----------
export interface PairGroup {
  label: string
  base: number
  pick: number
}

export function PairedBars({ groups, unit, baseLabel, pickLabel }: { groups: PairGroup[]; unit: string; baseLabel: string; pickLabel: string }) {
  const max = Math.max(...groups.flatMap((g) => [g.base, g.pick])) || 1
  return (
    <div className="vbars">
      <div className="vbars__plot">
        {groups.map((g) => (
          <div key={g.label} className="vbars__group">
            {(
              [
                ['base', g.base, baseLabel],
                ['pick', g.pick, pickLabel],
              ] as const
            ).map(([tone, v, who]) => (
              <span key={tone} className="vbars__col">
                <span className="vbars__value">{nf(v)}</span>
                <span className="vbars__bar" data-tone={tone} style={{ height: `${(v / max) * 100}%` }} tabIndex={0} data-tip={`${g.label} · ${who}: ${nf(v)} ${unit}`} />
              </span>
            ))}
          </div>
        ))}
      </div>
      <div className="vbars__axis">
        {groups.map((g) => (
          <span key={g.label}>{g.label}</span>
        ))}
      </div>
    </div>
  )
}

// ---------- year dot strip (quantile-dotplot style) ----------
export interface DotRow {
  label: string
  tone: 'base' | 'pick'
  points: { year: number | null; value: number }[]
}

/** One dot per simulated weather year, stacked in bins on a shared axis: the spread is the message. */
export function YearDots({ rows, unit }: { rows: DotRow[]; unit: string }) {
  const values = rows.flatMap((r) => r.points.map((p) => p.value))
  const lo = Math.min(...values)
  const hi = Math.max(...values)
  const BINS = 26
  const w = (hi - lo) / BINS || 1
  const x = (v: number) => ((v - lo) / (hi - lo || 1)) * 100
  const ticks = [lo, (lo + hi) / 2, hi]

  return (
    <div className="dots">
      {rows.map((r) => {
        const stacks = new Map<number, number>()
        return (
          <div key={r.label} className="dots__row">
            <span className="dots__label">{r.label}</span>
            <div className="dots__plot">
              {[...r.points]
                .sort((a, b) => a.value - b.value)
                .map((p, i) => {
                  const bin = Math.min(BINS - 1, Math.floor((p.value - lo) / w))
                  const level = stacks.get(bin) ?? 0
                  stacks.set(bin, level + 1)
                  const tip = `${p.year ?? 'Năm'}: ${nf(p.value)} ${unit}`
                  return (
                    <span
                      key={i}
                      className="dots__dot"
                      data-tone={r.tone}
                      style={{ left: `${x(lo + (bin + 0.5) * w)}%`, bottom: `${level * 9}px` }}
                      tabIndex={0}
                      data-tip={tip}
                      aria-label={tip}
                    />
                  )
                })}
            </div>
          </div>
        )
      })}
      <div className="dots__axis" aria-hidden="true">
        {ticks.map((v) => (
          <span key={v} style={{ left: `${x(v)}%` }}>
            {nf(Math.round(v / 10) * 10)}
          </span>
        ))}
      </div>
    </div>
  )
}
