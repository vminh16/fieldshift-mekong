import { useEffect, useState } from 'react'
import type { ScenarioOverride } from '../../../../contracts/types'

/** What the farmer can change (SOLUTION_DESIGN §11.4). Values map 1:1 to the API's ScenarioOverride. */
export interface Assumptions {
  rain: number // % vs history, 0 = unchanged
  heat: number // °C added
  saltEarly: number // weeks earlier
  sow: number[] // days shift per season
  cap: number | null // mm per season, null = no limit
}

export const NO_ASSUMPTIONS = (seasons: number): Assumptions => ({ rain: 0, heat: 0, saltEarly: 0, sow: Array(seasons).fill(0), cap: null })

export function toOverride(a: Assumptions): ScenarioOverride | null {
  const sow: Record<string, number> = {}
  a.sow.forEach((d, i) => d && (sow[String(i + 1)] = d))
  const o: ScenarioOverride = {
    ...(a.rain ? { rain_delta_pct: a.rain } : {}),
    ...(a.heat ? { temp_delta_c: a.heat } : {}),
    ...(a.saltEarly ? { salinity_onset_shift_weeks: -a.saltEarly } : {}),
    ...(Object.keys(sow).length ? { sow_shift_days: sow } : {}),
    ...(a.cap !== null ? { irrigation_cap_mm: a.cap } : {}),
  }
  return Object.keys(o).length ? o : null
}

const fmtSigned = (n: number, unit: string) => `${n > 0 ? '+' : n < 0 ? '−' : ''}${Math.abs(n).toLocaleString('vi-VN')}${unit}`

/** Short human summary, e.g. "Mưa −30% · Mặn sớm 4 tuần". */
export function describe(a: Assumptions, seasonNames: string[]): string[] {
  const out: string[] = []
  if (a.rain) out.push(`Mưa ${fmtSigned(a.rain, '%')}`)
  if (a.heat) out.push(`Nóng ${fmtSigned(a.heat, ' °C')}`)
  if (a.saltEarly) out.push(`Mặn sớm ${a.saltEarly} tuần`)
  a.sow.forEach((d, i) => d && out.push(`Gieo ${seasonNames[i] ?? `vụ ${i + 1}`} ${d < 0 ? `sớm ${-d}` : `trễ ${d}`} ngày`))
  if (a.cap !== null) out.push(`Tưới tối đa ${a.cap.toLocaleString('vi-VN')} mm/vụ`)
  return out
}

const SOW_STEPS = [-14, -7, 0, 7, 14]
const CAPS: (number | null)[] = [null, 600, 400, 250]

export function WhatIfPanel({
  seasonNames,
  applied,
  history,
  busy,
  locked,
  onRun,
  onClear,
}: {
  seasonNames: string[]
  applied: Assumptions | null
  history: Assumptions[]
  busy: boolean
  locked: boolean
  onRun: (a: Assumptions) => void
  onClear: () => void
}) {
  const [draft, setDraft] = useState<Assumptions>(applied ?? NO_ASSUMPTIONS(seasonNames.length))
  useEffect(() => {
    setDraft(applied ?? NO_ASSUMPTIONS(seasonNames.length))
  }, [applied, seasonNames.length])
  const set = <K extends keyof Assumptions>(k: K, v: Assumptions[K]) => setDraft({ ...draft, [k]: v })
  const changed = JSON.stringify(draft) !== JSON.stringify(applied ?? NO_ASSUMPTIONS(seasonNames.length))
  const empty = toOverride(draft) === null

  return (
    <section className="whatif" aria-label="Thử nếu">
      <div className="whatif__grid">
        <label className="wi">
          <span className="wi__label">Mưa so với bình thường</span>
          <input type="range" min={-50} max={30} step={10} value={draft.rain} disabled={locked || busy} onChange={(e) => set('rain', Number(e.target.value))} />
          <span className="wi__value">{draft.rain ? fmtSigned(draft.rain, '%') : 'Như lịch sử'}</span>
        </label>
        <label className="wi">
          <span className="wi__label">Nóng hơn</span>
          <input type="range" min={0} max={3} step={0.5} value={draft.heat} disabled={locked || busy} onChange={(e) => set('heat', Number(e.target.value))} />
          <span className="wi__value">{draft.heat ? `+${draft.heat.toLocaleString('vi-VN')} °C` : 'Như lịch sử'}</span>
        </label>
        <label className="wi">
          <span className="wi__label">Mặn đến sớm</span>
          <input type="range" min={0} max={8} step={1} value={draft.saltEarly} disabled={locked || busy} onChange={(e) => set('saltEarly', Number(e.target.value))} />
          <span className="wi__value">{draft.saltEarly ? `${draft.saltEarly} tuần` : 'Đúng mùa'}</span>
        </label>
        <div className="wi">
          <span className="wi__label">Lịch gieo</span>
          <div className="wi__sow">
            {seasonNames.map((name, i) => (
              <label key={name}>
                <span>{name}</span>
                <select
                  value={draft.sow[i] ?? 0}
                  disabled={locked || busy}
                  aria-label={`Lịch gieo vụ ${name}`}
                  onChange={(e) => {
                    const sow = [...draft.sow]
                    sow[i] = Number(e.target.value)
                    set('sow', sow)
                  }}
                >
                  {SOW_STEPS.map((d) => (
                    <option key={d} value={d}>
                      {d === 0 ? 'Đúng lịch' : d < 0 ? `Sớm ${-d} ngày` : `Trễ ${d} ngày`}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </div>
        </div>
        <label className="wi">
          <span className="wi__label">Nước tưới tối đa mỗi vụ</span>
          <select value={draft.cap ?? ''} disabled={locked || busy} onChange={(e) => set('cap', e.target.value === '' ? null : Number(e.target.value))}>
            {CAPS.map((c) => (
              <option key={String(c)} value={c ?? ''}>
                {c === null ? 'Không giới hạn' : `${c.toLocaleString('vi-VN')} mm`}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="whatif__foot">
        <button type="button" className="btn btn--primary btn--sm" disabled={locked || busy || empty || !changed} onClick={() => onRun(draft)}>
          {busy ? 'Engine đang chạy…' : 'Chạy thử'}
        </button>
        {applied && (
          <button type="button" className="btn btn--ghost btn--sm" disabled={busy} onClick={onClear}>
            Bỏ giả định
          </button>
        )}
        <p className="whatif__note">
          {locked
            ? 'Cần kết nối engine để thử giả định.'
            : 'Engine tính lại cả hai bên với cùng giả định. Mỗi lần chạy là một bản thử mới; đề xuất gốc giữ nguyên.'}
        </p>
      </div>

      {history.length > 0 && (
        <div className="whatif__history">
          <span>Bản thử trước</span>
          <ul>
            {history.map((h, i) => (
              <li key={i}>
                <button type="button" disabled={busy} aria-pressed={JSON.stringify(h) === JSON.stringify(applied)} onClick={() => onRun(h)}>
                  {describe(h, seasonNames).join(' · ')}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}
