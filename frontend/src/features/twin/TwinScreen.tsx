import { useEffect, useMemo, useRef, useState } from 'react'
import type { DecisionPackage, Option, Twin } from '../../../../contracts/types'
import { AppShell } from '../shell/AppShell'
import { href, navigate } from '../../shared/router'
import { getField, useActiveFieldId, useFields } from '../../shared/fields/store'
import { CROP_SHORT, STATUS_VI } from '../../shared/decision/source'
import { yearOutlookOf } from '../../shared/decision/yearOutlook'
import { openTwin, type ChainSpec, type TwinSource } from '../../shared/twin/source'
import { ApiError } from '../../shared/api/client'
import { YearOutlookBanner } from '../recommend/YearOutlookBanner'
import { ChainPicker } from './ChainPicker'
import { FieldScene3D } from './scene/FieldScene3D'
import { TwinTimeline, saltRisk, stressRisk } from './TwinTimeline'
import { WhatIfPanel, describe, toOverride, type Assumptions } from './WhatIfPanel'
import './twin.css'

interface Side {
  twin: Twin | null
  chain: Option | null
  busy: boolean
  error: string | null
}
const EMPTY: Side = { twin: null, chain: null, busy: true, error: null }

const KIND_VI: Record<string, string> = {
  CLIMATOLOGY: 'Lịch sử',
  STRESS_TEST: 'Thử thách',
  FORECAST: 'Dự báo (chưa kiểm định)',
  CLIMATE_PROJECTION: 'Kịch bản khí hậu',
}
const nf = (n: number) => n.toLocaleString('vi-VN', { maximumFractionDigits: 0 })
const dmy = (s: string) => new Date(s).toLocaleDateString('vi-VN')
const chainLabel = (o: Option | null) => (o ? o.seasons.map((s) => CROP_SHORT[s.crop] ?? s.crop).join(' – ') : '…')
const yearLabel = (y: number) => `${y}–${String((y + 1) % 100).padStart(2, '0')}`

interface Preset {
  id: 'analog' | 'normal' | 'wet'
  label: string
  hint: string
  scenario: string
  year: number | null
}

/** The three weather years a farmer asks about. Analog = ENSO analog when the engine sends it, else the dry stress test. */
function presetsOf(d: DecisionPackage): Preset[] {
  const yo = yearOutlookOf(d)
  const sc = (id: string) => d.scenarios.find((s) => s.scenario_id === id)
  const out: Preset[] = []
  const analogId = yo?.scenario_id && sc(yo.scenario_id) ? yo.scenario_id : sc('sc_dry') ? 'sc_dry' : null
  if (analogId) {
    out.push({
      id: 'analog',
      label: yo?.analog_labels_vi[0] ? `Năm tương tự (${yo.analog_labels_vi[0]})` : 'Năm khô hạn',
      hint: yo ? 'Theo tín hiệu ENSO, không phải dự báo' : (sc(analogId)?.name ?? ''),
      scenario: analogId,
      year: yo?.analog_years[0] ?? null,
    })
  }
  if (sc('sc_clim')) out.push({ id: 'normal', label: 'Năm bình thường', hint: 'Năm giữa của 2001–2025', scenario: 'sc_clim', year: null })
  if (sc('sc_wet_ref')) out.push({ id: 'wet', label: 'Năm mưa nhiều', hint: sc('sc_wet_ref')!.name, scenario: 'sc_wet_ref', year: null })
  return out
}

export function TwinScreen({ fieldId, sequenceId }: { fieldId: string | null; sequenceId: string | null }) {
  const fields = useFields()
  const activeId = useActiveFieldId()
  const field = getField(fieldId) ?? fields.find((f) => f.id === activeId) ?? null

  const [source, setSource] = useState<TwinSource | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [specA, setSpecA] = useState<ChainSpec | null>(null)
  const [specB, setSpecB] = useState<ChainSpec | null>(null)
  const [preset, setPreset] = useState<Preset['id'] | 'custom'>('normal')
  const [scenario, setScenario] = useState('sc_clim')
  const [member, setMember] = useState<number | null>(null)
  // Weather year the preset wants; resolved to a member once the scenario's members are known.
  const [wantYear, setWantYear] = useState<number | null>(null)
  const [a, setA] = useState<Side>(EMPTY)
  const [b, setB] = useState<Side>(EMPTY)
  const [pos, setPos] = useState(0)
  const index = Math.floor(pos)
  const [playing, setPlaying] = useState(false)
  const [show3d, setShow3d] = useState(false)
  const [assume, setAssume] = useState<Assumptions | null>(null)
  const [history, setHistory] = useState<Assumptions[]>([])
  const override = useMemo(() => (assume ? toOverride(assume) : null), [assume])
  const overrideKey = override ? JSON.stringify(override) : ''

  const applyPreset = (p: Preset) => {
    setPreset(p.id)
    setScenario(p.scenario)
    setWantYear(p.year)
    setMember(null)
    setPlaying(false)
  }

  useEffect(() => {
    if (!field) return
    let live = true
    setSource(null)
    setNotice(null)
    openTwin(field).then(({ source, notice }) => {
      if (!live) return
      setSource(source)
      setNotice(notice)
      setAssume(null)
      setHistory([])
      setPos(0)
      const d = source.decision
      const ps = presetsOf(d)
      const first = ps.find((p) => p.id === 'analog') ?? ps.find((p) => p.id === 'normal')
      if (first) applyPreset(first)
      setSpecA({ kind: 'engine', sequenceId: d.baseline.sequence_id })
      const wanted = d.options.find((o) => o.sequence_id === sequenceId) ?? d.options[0]
      setSpecB({ kind: 'engine', sequenceId: (wanted ?? d.baseline).sequence_id })
    })
    return () => {
      live = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [field?.id])

  // Side A fixes the weather year, so both sides always share one member.
  useEffect(() => {
    if (!source || !specA) return
    let live = true
    setA((s) => ({ ...s, busy: true, error: null }))
    source
      .load(specA, scenario, member, override)
      .then(({ twin, chain }) => {
        if (!live) return
        if (member === null) {
          const m = wantYear !== null ? twin.members.find((x) => x.year === wantYear)?.member : undefined
          if (m !== undefined && m !== twin.member) return setMember(m)
          setMember(twin.member)
        }
        setA({ twin, chain, busy: false, error: null })
      })
      .catch((e) => live && setA({ twin: null, chain: null, busy: false, error: errorText(e) }))
    return () => {
      live = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source, specA, scenario, member, overrideKey])

  useEffect(() => {
    if (!source || !specB || member === null) return
    let live = true
    setB((s) => ({ ...s, busy: true, error: null }))
    source
      .load(specB, scenario, member, override)
      .then(({ twin, chain }) => live && setB({ twin, chain, busy: false, error: null }))
      .catch((e) => live && setB({ twin: null, chain: null, busy: false, error: errorText(e) }))
    return () => {
      live = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source, specB, scenario, member, overrideKey])

  const weeks = Math.max(a.twin?.series.length ?? 0, b.twin?.series.length ?? 0)

  // Play: 3 weeks per second on requestAnimationFrame; stops at the end.
  const raf = useRef(0)
  useEffect(() => {
    if (!playing) return
    let last = performance.now()
    const step = (now: number) => {
      const dt = Math.min(0.1, (now - last) / 1000)
      last = now
      let done = false
      setPos((p) => {
        const next = p + dt * 3
        if (next >= weeks - 1) {
          done = true
          return weeks - 1
        }
        return next
      })
      if (done) setPlaying(false)
      else raf.current = requestAnimationFrame(step)
    }
    raf.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf.current)
  }, [playing, weeks])

  if (!field) {
    return (
      <AppShell>
        <div className="tw-empty">
          <h1>Chưa có thửa ruộng</h1>
          <p>Khoanh một thửa để mô phỏng luân canh trên chính thửa đó.</p>
          <a className="btn btn--primary" href={href('/ruong/moi')}>
            Khoanh thửa ruộng
          </a>
        </div>
      </AppShell>
    )
  }

  const d = source?.decision
  const locked = source?.mode === 'mock'
  const yo = yearOutlookOf(d)
  const presets = d ? presetsOf(d) : []
  const members = a.twin?.members ?? []
  const seasonNames = (d?.windows ?? []).map((w) => w.name_vi.split(' /')[0])
  const labelA = sideName(specA, a.chain, d)
  const labelB = sideName(specB, b.chain, d)
  const year = a.twin ? (a.twin.analog_year ?? members.find((m) => m.member === a.twin!.member)?.year ?? null) : null
  const ready = a.twin && b.twin && !a.busy && !b.busy
  const runAssumptions = (x: Assumptions | null) => {
    setAssume(x)
    setMember(null)
    setPos(0)
    setPlaying(false)
    if (x && toOverride(x)) setHistory((h) => [x, ...h.filter((y) => JSON.stringify(y) !== JSON.stringify(x))].slice(0, 5))
  }

  return (
    <AppShell>
      <div className="tw">
        <header className="tw-head">
          <div>
            <label className="tw-head__field">
              <span className="visually-hidden">Thửa ruộng</span>
              <select value={field.id} onChange={(e) => navigate('/mo-phong', { thua: e.target.value })}>
                {fields.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </select>
            </label>
            <h1 className="tw-q">
              Nếu mùa khô tới giống <span className="tw-q__year">{override ? 'giả định của bạn' : year ? `năm ${yearLabel(year)}` : '…'}</span>, phương án của bạn ra sao?
            </h1>
          </div>
          <div className="tw-presets" role="group" aria-label="Chọn năm thời tiết">
            {presets.map((p) => (
              <button
                key={p.id}
                type="button"
                className="tw-preset"
                aria-pressed={preset === p.id && !override}
                disabled={locked || Boolean(override) || a.busy}
                onClick={() => applyPreset(p)}
              >
                <strong>{p.label}</strong>
                <span>{p.hint}</span>
              </button>
            ))}
          </div>
        </header>

        {yo && <YearOutlookBanner yo={yo} compact />}
        {notice && (
          <p className="tw-notice" role="status">
            {notice}
          </p>
        )}
        {assume && override && (
          <div className="tw-assume" role="status">
            <span className="tw-assume__tag">Giả định do bạn đặt</span>
            <span>{describe(assume, seasonNames).join(' · ')}</span>
            <button type="button" className="tw-assume__edit" disabled={a.busy || b.busy} onClick={() => runAssumptions(null)}>
              Bỏ
            </button>
          </div>
        )}

        {!d || !specA || !specB ? (
          <div className="tw-loading" aria-busy="true">
            Engine đang chuẩn bị mô phỏng…
          </div>
        ) : (
          <>
            <section className="tw-answer" aria-live="polite" data-busy={!ready || undefined}>
              {a.error || b.error ? (
                <p className="rec-error">{a.error ?? b.error}</p>
              ) : ready ? (
                <Conclusion a={a} b={b} labelA={labelA} labelB={labelB} seasonNames={seasonNames} />
              ) : (
                <p className="tw-answer__main">Engine đang mô phỏng…</p>
              )}
            </section>

            {a.twin && b.twin && (
              <TwinTimeline
                a={{ key: 'a', label: labelA, series: a.twin.series, events: a.twin.events }}
                b={{ key: 'b', label: labelB, series: b.twin.series, events: b.twin.events }}
                index={Math.min(index, weeks - 1)}
                onIndex={(i) => {
                  setPlaying(false)
                  setPos(i)
                }}
                playing={playing}
                onTogglePlay={() => {
                  if (!playing && index >= weeks - 1) setPos(0)
                  setPlaying(!playing)
                }}
              />
            )}

            <div className="tw-tools">
              <button type="button" className="btn btn--ghost btn--sm" aria-expanded={show3d} onClick={() => setShow3d(!show3d)}>
                {show3d ? 'Ẩn ruộng 3D' : 'Xem ruộng 3D'}
              </button>
              <a className="btn btn--ghost btn--sm" href={href('/de-xuat', { thua: field.id })}>
                Xem đề xuất
              </a>
            </div>

            {show3d && (
              <div className="tw-3d">
                {[
                  ['A', a, labelA],
                  ['B', b, labelB],
                ].map(([tag, side, label]) => {
                  const s = (side as Side).twin?.series ?? []
                  return (
                    <figure key={tag as string}>
                      <figcaption>
                        <span className="tw-side__tag" data-series={(tag as string).toLowerCase()}>
                          {tag as string}
                        </span>{' '}
                        {label as string}
                      </figcaption>
                      {s.length ? <FieldScene3D series={s} pos={Math.min(pos, s.length - 1)} /> : <div className="scene3d scene3d--empty" />}
                    </figure>
                  )
                })}
              </div>
            )}

            <details className="tw-adv">
              <summary>Nâng cao: chọn kịch bản, năm, chuỗi khác hoặc tự đặt giả định</summary>
              <div className="tw-adv__body">
                <div className="tw-head__controls">
                  <label className="tw-ctl">
                    <span>Kịch bản thời tiết</span>
                    <select
                      value={override ? 'sc_whatif' : scenario}
                      disabled={locked || Boolean(override)}
                      onChange={(e) => {
                        setPreset('custom')
                        setScenario(e.target.value)
                        setWantYear(null)
                        setMember(null)
                      }}
                    >
                      {override && <option value="sc_whatif">Giả định của bạn</option>}
                      {d.scenarios.map((s) => (
                        <option key={s.scenario_id} value={s.scenario_id}>
                          {KIND_VI[s.kind] ?? s.kind}: {s.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="tw-ctl">
                    <span>Năm thời tiết</span>
                    <select
                      value={member ?? ''}
                      disabled={!members.length || locked}
                      onChange={(e) => {
                        setPreset('custom')
                        setMember(Number(e.target.value))
                      }}
                    >
                      {members.map((m) => (
                        <option key={m.member} value={m.member}>
                          {m.year ? yearLabel(m.year) : `Năm ${m.member + 1}`}
                          {m.label_vi && m.label_vi !== 'Năm tham chiếu' ? ` · ${m.label_vi}` : ''} · {nf(m.irrigation_mm)} mm
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="tw-adv__chains">
                  {(
                    [
                      ['A', specA, setSpecA, a.busy],
                      ['B', specB, setSpecB, b.busy],
                    ] as const
                  ).map(([tag, spec, set, busy]) => (
                    <div key={tag} className="tw-adv__chain">
                      <span className="tw-side__tag" data-series={tag.toLowerCase()}>
                        {tag}
                      </span>
                      <ChainPicker decision={d} value={spec} onChange={set} locked={locked} busy={busy} />
                    </div>
                  ))}
                </div>
                <WhatIfPanel
                  seasonNames={seasonNames}
                  applied={assume}
                  history={history}
                  busy={a.busy || b.busy}
                  locked={locked}
                  onRun={(x) => runAssumptions(x)}
                  onClear={() => runAssumptions(null)}
                />
              </div>
            </details>

            <p className="tw-foot">
              Mọi số do engine tính cho cùng kịch bản và cùng năm thời tiết ở hai bên · {locked ? 'Dữ liệu mẫu' : `Lần chạy ${dmy(d.generated_at)}`}
            </p>
          </>
        )}
      </div>
    </AppShell>
  )
}

/** One answer, derived only from the two twin responses (totals, weekly flags, events). */
function Conclusion({ a, b, labelA, labelB, seasonNames }: { a: Side; b: Side; labelA: string; labelB: string; seasonNames: string[] }) {
  const ta = a.twin!
  const tb = b.twin!
  const total = (t: Twin) => t.members.find((m) => m.member === t.member)?.irrigation_mm ?? t.series[t.series.length - 1]?.irrigation_cum.value ?? null
  const totA = total(ta)
  const totB = total(tb)
  const salt = (t: Twin) => t.series.filter(saltRisk).length
  const stress = (t: Twin) => t.series.filter(stressRisk).length
  const harvest1 = (t: Twin) => t.events.find((e) => e.type === 'harvest' && e.season_index === 1)
  const saltStart = (tb.events.length ? tb : ta).events.find((e) => e.type === 'salinity_season_start')
  const infeasible = b.chain?.decision_status === 'NOT_FEASIBLE'
  const hard = b.chain?.rules.find((r) => r.severity === 'HARD')
  const status = b.chain ? STATUS_VI[b.chain.decision_status] : null

  let main = ''
  if (totA !== null && totB !== null) {
    const diff = totB - totA
    main =
      Math.abs(diff) < 1
        ? `${labelB} cần nước tưới như ${labelA.toLowerCase()}: ${nf(totB)} mm cả 3 vụ.`
        : `${labelB} cần ${nf(totB)} mm nước tưới cả 3 vụ, ${diff < 0 ? 'ít' : 'nhiều'} hơn ${labelA.toLowerCase()} ${nf(Math.abs(diff))} mm (≈ ${nf(Math.abs(diff) * 10)} m³/ha).`
  }
  const facts: string[] = []
  const sa = salt(ta)
  const sb = salt(tb)
  if (sa || sb) facts.push(sa === sb ? `Cả hai có ${sb} tuần cây trong ruộng giữa mùa mặn.` : `Cây trong ruộng giữa mùa mặn: B ${sb} tuần, A ${sa} tuần.`)
  const hb = harvest1(tb)
  const ha = harvest1(ta)
  const saltSeason = [...ta.series, ...tb.series].some((w) => w.salinity?.in_salinity_season)
  if (hb && saltStart && saltSeason) {
    const days = Math.round((new Date(saltStart.date).getTime() - new Date(hb.date).getTime()) / 86400000)
    const rel = days > 0 ? `${days} ngày trước khi mùa mặn bắt đầu` : days < 0 ? `${-days} ngày sau khi mùa mặn bắt đầu` : 'đúng ngày mùa mặn bắt đầu'
    facts.push(
      `B thu hoạch vụ ${seasonNames[0] ?? '1'} ngày ${dmy(hb.date)}, ${rel} (${dmy(saltStart.date)})${ha && ha.date !== hb.date ? `; A thu ngày ${dmy(ha.date)}` : ''}.`,
    )
  }
  const xa = stress(ta)
  const xb = stress(tb)
  if (xa || xb) facts.push(`Tuần có rủi ro stress (thiếu nước, nóng): B ${xb}, A ${xa}.`)

  return (
    <>
      {infeasible && <p className="tw-answer__bad">B không làm được: {hard?.reason ?? 'vi phạm ràng buộc cứng'}. Số nước tưới dưới đây không phải là tiết kiệm.</p>}
      <p className="tw-answer__main">{main}</p>
      {facts.length > 0 && (
        <ul className="tw-answer__facts">
          {facts.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      )}
      <p className="tw-answer__chains">
        <span>
          <span className="tw-side__tag" data-series="a">
            A
          </span>{' '}
          {labelA} · {chainLabel(a.chain)}
        </span>
        <span>
          <span className="tw-side__tag" data-series="b">
            B
          </span>{' '}
          {labelB} · {chainLabel(b.chain)}
          {status && (
            <span className="tw-answer__status" data-tone={status.tone}>
              {status.text}
            </span>
          )}
        </span>
      </p>
    </>
  )
}

function sideName(spec: ChainSpec | null, chain: Option | null, d: { baseline: Option } | undefined) {
  if (!spec) return '…'
  if (spec.kind === 'custom') return `Tự chọn: ${spec.crops.map((c) => CROP_SHORT[c] ?? c).join(' – ')}`
  if (d && spec.sequenceId === d.baseline.sequence_id) return 'Cách đang làm'
  return chain?.strategy_name_vi ?? chainLabel(chain)
}

function errorText(e: unknown) {
  if (e instanceof ApiError && e.code === 'PLAN_INPUT_INVALID') return `Engine không chạy được chuỗi này: ${e.message}`
  if (e instanceof ApiError && e.unreachable) return 'Mất kết nối engine.'
  return e instanceof Error ? e.message : 'Không mô phỏng được.'
}
