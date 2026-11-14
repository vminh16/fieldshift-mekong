import { useEffect, useMemo, useRef, useState } from 'react'
import type { Measure, Option, Twin, TwinWeek } from '../../../../contracts/types'
import { AppShell } from '../shell/AppShell'
import { href, navigate } from '../../shared/router'
import { getField, useActiveFieldId, useFields } from '../../shared/fields/store'
import { CROP_SHORT } from '../../shared/decision/source'
import { openTwin, type ChainSpec, type TwinSource } from '../../shared/twin/source'
import { ApiError } from '../../shared/api/client'
import { ChainPicker } from './ChainPicker'
import { FieldScene3D } from './scene/FieldScene3D'
import { TwinTimeline } from './TwinTimeline'
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
const STRESS_VI: Record<string, string> = { LOW: 'Thấp', MEDIUM: 'Vừa', HIGH: 'Cao' }
const nf = (n: number, d = 0) => n.toLocaleString('vi-VN', { maximumFractionDigits: d })
const chainLabel = (o: Option | null) => (o ? o.seasons.map((s) => CROP_SHORT[s.crop] ?? s.crop).join(' – ') : '…')

export function TwinScreen({ fieldId, sequenceId }: { fieldId: string | null; sequenceId: string | null }) {
  const fields = useFields()
  const activeId = useActiveFieldId()
  const field = getField(fieldId) ?? fields.find((f) => f.id === activeId) ?? null

  const [source, setSource] = useState<TwinSource | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [specA, setSpecA] = useState<ChainSpec | null>(null)
  const [specB, setSpecB] = useState<ChainSpec | null>(null)
  const [scenario, setScenario] = useState('sc_clim')
  const [member, setMember] = useState<number | null>(null)
  const [a, setA] = useState<Side>(EMPTY)
  const [b, setB] = useState<Side>(EMPTY)
  // Fractional week position: playback glides, the scene eases between weeks.
  const [pos, setPos] = useState(0)
  const index = Math.floor(pos)
  const setIndex = (i: number) => setPos(i)
  const [playing, setPlaying] = useState(false)
  const [assume, setAssume] = useState<Assumptions | null>(null)
  const [history, setHistory] = useState<Assumptions[]>([])
  const [whatIfOpen, setWhatIfOpen] = useState(false)
  const override = useMemo(() => (assume ? toOverride(assume) : null), [assume])
  const overrideKey = override ? JSON.stringify(override) : ''

  // Open the field's latest decision (or the captured mock).
  useEffect(() => {
    if (!field) return
    let live = true
    setSource(null)
    setNotice(null)
    openTwin(field).then(({ source, notice }) => {
      if (!live) return
      setSource(source)
      setNotice(notice)
      setScenario('sc_clim')
      setMember(null)
      setIndex(0)
      setAssume(null)
      setHistory([])
      const d = source.decision
      setSpecA({ kind: 'engine', sequenceId: d.baseline.sequence_id })
      const wanted = d.options.find((o) => o.sequence_id === sequenceId) ?? d.options[0]
      setSpecB({ kind: 'engine', sequenceId: (wanted ?? d.baseline).sequence_id })
    })
    return () => {
      live = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [field?.id])

  // Side A fixes the weather year when none is chosen, so both sides always share one member.
  useEffect(() => {
    if (!source || !specA) return
    let live = true
    setA((s) => ({ ...s, busy: true, error: null }))
    source
      .load(specA, scenario, member, override)
      .then(({ twin, chain }) => {
        if (!live) return
        setA({ twin, chain, busy: false, error: null })
        if (member === null) setMember(twin.member)
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
  const members = a.twin?.members ?? []
  const scenarios = d?.scenarios ?? []
  const seasonNames = (d?.windows ?? []).map((w) => w.name_vi.split(' /')[0])
  const runAssumptions = (x: Assumptions | null) => {
    setAssume(x)
    setMember(null)
    setIndex(0)
    setPlaying(false)
    if (x && toOverride(x)) setHistory((h) => [x, ...h.filter((y) => JSON.stringify(y) !== JSON.stringify(x))].slice(0, 5))
  }
  const labelA = sideName(specA, a.chain, d)
  const labelB = sideName(specB, b.chain, d)

  return (
    <AppShell>
      <div className="tw">
        <header className="tw-head">
          <div>
            <p className="tw-head__kicker">Mô phỏng trên ruộng · 3 vụ tới</p>
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
          </div>
          <div className="tw-head__controls">
            <label className="tw-ctl">
              <span>Thời tiết giả định</span>
              <select
                value={override ? 'sc_whatif' : scenario}
                disabled={!d || locked || Boolean(override)}
                onChange={(e) => {
                  setScenario(e.target.value)
                  setMember(null)
                  setIndex(0)
                }}
              >
                {override && <option value="sc_whatif">Giả định của bạn</option>}
                {scenarios.map((s) => (
                  <option key={s.scenario_id} value={s.scenario_id}>
                    {KIND_VI[s.kind] ?? s.kind}: {s.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="tw-ctl">
              <span>Năm thời tiết</span>
              <select value={member ?? ''} disabled={!members.length || locked} onChange={(e) => setMember(Number(e.target.value))}>
                {members.map((m) => (
                  <option key={m.member} value={m.member}>
                    {m.label_vi === 'Năm tham chiếu' ? `Năm ${m.year ?? m.member + 1}` : `${m.label_vi}${m.year ? ` (${m.year})` : ''}`}
                  </option>
                ))}
              </select>
            </label>
            <button type="button" className="btn btn--ghost btn--sm tw-head__whatif" aria-expanded={whatIfOpen} aria-controls="whatif" onClick={() => setWhatIfOpen(!whatIfOpen)}>
              Thử nếu…
            </button>
          </div>
        </header>

        {assume && override && (
          <div className="tw-assume" role="status">
            <span className="tw-assume__tag">Giả định do bạn đặt</span>
            <span>{describe(assume, seasonNames).join(' · ')}</span>
            <button type="button" className="tw-assume__edit" onClick={() => setWhatIfOpen(true)}>
              Sửa
            </button>
            <button type="button" className="tw-assume__edit" disabled={a.busy || b.busy} onClick={() => runAssumptions(null)}>
              Bỏ
            </button>
          </div>
        )}

        {whatIfOpen && d && (
          <div id="whatif">
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
        )}

        {notice && (
          <p className="tw-notice" role="status">
            {notice}
          </p>
        )}

        {!d || !specA || !specB ? (
          <div className="tw-loading" aria-busy="true">
            Engine đang chuẩn bị mô phỏng…
          </div>
        ) : (
          <>
            <div className="tw-sides">
              <SideView
                tag="A"
                side={a}
                pos={pos}
                picker={<ChainPicker decision={d} value={specA} onChange={setSpecA} locked={locked} busy={a.busy} />}
              />
              <SideView
                tag="B"
                side={b}
                pos={pos}
                picker={<ChainPicker decision={d} value={specB} onChange={setSpecB} locked={locked} busy={b.busy} />}
              />
            </div>

            {a.twin && b.twin && (
              <TwinTimeline
                a={a.twin.series}
                b={b.twin.series}
                labelA={labelA}
                labelB={labelB}
                totalA={a.twin.members.find((m) => m.member === a.twin!.member)?.irrigation_mm ?? null}
                totalB={b.twin.members.find((m) => m.member === b.twin!.member)?.irrigation_mm ?? null}
                infeasible={a.chain?.decision_status === 'NOT_FEASIBLE' || b.chain?.decision_status === 'NOT_FEASIBLE'}
                index={Math.min(index, weeks - 1)}
                onIndex={(i) => {
                  setPlaying(false)
                  setIndex(i)
                }}
                playing={playing}
                onTogglePlay={() => {
                  if (!playing && index >= weeks - 1) setIndex(0)
                  setPlaying(!playing)
                }}
              />
            )}

            <p className="tw-foot">
              Mọi số do engine tính cho cùng kịch bản và cùng năm thời tiết ở hai bên · {locked ? 'Dữ liệu mẫu' : `Lần chạy ${new Date(d.generated_at).toLocaleDateString('vi-VN')}`} ·{' '}
              <a href={href('/de-xuat', { thua: field.id })}>Xem đề xuất</a>
            </p>
          </>
        )}
      </div>
    </AppShell>
  )
}

function sideName(spec: ChainSpec | null, chain: Option | null, d: { baseline: Option } | undefined) {
  if (!spec) return '…'
  if (spec.kind === 'custom') return `Tự chọn: ${spec.crops.map((c) => CROP_SHORT[c] ?? c).join(' – ')}`
  if (d && spec.sequenceId === d.baseline.sequence_id) return 'Đang làm'
  return chain?.strategy_name_vi ?? chainLabel(chain)
}

function errorText(e: unknown) {
  if (e instanceof ApiError && e.code === 'PLAN_INPUT_INVALID') return `Engine không chạy được chuỗi này: ${e.message}`
  if (e instanceof ApiError && e.unreachable) return 'Mất kết nối engine.'
  return e instanceof Error ? e.message : 'Không mô phỏng được.'
}

function SideView({ tag, side, pos, picker }: { tag: 'A' | 'B'; side: Side; pos: number; picker: React.ReactNode }) {
  const series = side.twin?.series ?? []
  const week: TwinWeek | undefined = series[Math.max(0, Math.min(series.length - 1, Math.floor(pos)))]
  const c = side.chain
  const hard = c?.rules.find((r) => r.severity === 'HARD')
  const checks = c?.rules.filter((r) => r.severity === 'UNKNOWN_REQUIRES_CHECK').length ?? 0
  return (
    <section className="tw-side" data-side={tag} aria-label={`Bên ${tag}`}>
      <div className="tw-side__top">
        <span className="tw-side__tag" data-series={tag === 'A' ? 'a' : 'b'}>
          {tag}
        </span>
        {picker}
      </div>
      <p className="tw-side__status" data-tone={c?.decision_status === 'NOT_FEASIBLE' ? 'bad' : checks ? 'warn' : 'ok'}>
        {side.error
          ? side.error
          : !c
            ? 'Đang mô phỏng…'
            : c.decision_status === 'NOT_FEASIBLE'
              ? `Không khả thi: ${hard?.reason ?? 'vi phạm ràng buộc cứng'}`
              : checks
                ? `Có điều kiện · cần kiểm tra ${checks} điều`
                : 'Khả thi với dữ liệu hiện có'}
      </p>
      <div className="tw-side__canvas" data-busy={side.busy || undefined}>
        {series.length ? <FieldScene3D series={series} pos={Math.min(pos, series.length - 1)} /> : <div className="scene3d scene3d--empty" />}
      </div>
      <dl className="tw-ind">
        <Ind label="Ẩm vùng rễ" m={week?.root_zone_water} fmt={(v) => `${Math.round(v * 100)}%`} empty="Đất trống" />
        <Ind
          label="Mặn nước kênh"
          m={week?.salinity}
          fmt={(v) => `${nf(v, 1)} dS/m`}
          empty="Chưa đo"
          extra={week?.salinity?.in_salinity_season ? 'Đang mùa mặn' : undefined}
        />
        <div>
          <dt>Rủi ro stress</dt>
          <dd>{week?.stress_risk ? (STRESS_VI[week.stress_risk as string] ?? String(week.stress_risk)) : '—'}</dd>
          <dd className="tw-ind__tag">Dự kiến</dd>
        </div>
        <Ind label="Tưới tuần này" m={week?.irrigation_week} fmt={(v) => `${nf(v)} mm`} empty="0 mm" extra={week?.rain_week?.value ? `Mưa ${nf(week.rain_week.value)} mm` : undefined} />
      </dl>
    </section>
  )
}

function Ind({ label, m, fmt, empty, extra }: { label: string; m: Measure | undefined; fmt: (v: number) => string; empty: string; extra?: string }) {
  const v = m?.value
  return (
    <div>
      <dt>{label}</dt>
      <dd>{v === null || v === undefined ? empty : fmt(v)}</dd>
      <dd className="tw-ind__tag">{extra ?? m?.label ?? '—'}</dd>
    </div>
  )
}
