import { useEffect, useState } from 'react'
import type { DecisionPackage, Observation } from '../../../../contracts/types'
import { AppShell } from '../shell/AppShell'
import { href, navigate } from '../../shared/router'
import { api, type ObservationWrite, type PlanStatus } from '../../shared/api/client'
import { getField, useActiveFieldId, useFields } from '../../shared/fields/store'
import { latestPlan, readChoice, refreshPlan } from '../../shared/decision/plans'
import { CROP_SHORT } from '../../shared/decision/source'
import '../recommend/recommend.css'
import './track.css'

const today = () => new Date().toLocaleDateString('sv-SE') // YYYY-MM-DD, local
const PER_MILLE = 0.64 // 1 dS/m ≈ 0,64 ‰ (g/L)
const VAR_VI: Record<string, string> = { canal_ecw: 'Mặn nước kênh', drainage: 'Thoát nước', season_closed: 'Đóng vụ', soil_ph: 'pH đất', rain_mm: 'Mưa' }
const TEXT_VI: Record<string, string> = { good: 'Tốt', poor: 'Kém' }

/** Theo dõi vụ: enter field measurements, see whether the plan still holds, share a one-page summary. */
export function TrackScreen({ fieldId }: { fieldId: string | null }) {
  const fields = useFields()
  const activeId = useActiveFieldId()
  const field = getField(fieldId) ?? fields.find((f) => f.id === activeId) ?? null
  const [plan, setPlan] = useState<DecisionPackage | null>(null)
  const [status, setStatus] = useState<PlanStatus | null>(null)
  const [obs, setObs] = useState<Observation[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const refresh = async (d: DecisionPackage) => {
    const [s, f] = await Promise.all([api.planStatus(d.decision_id), api.getField(d.field_id)])
    setStatus(s)
    setObs([...(f.observations ?? [])].reverse())
  }

  useEffect(() => {
    if (!field || field.pending) return
    let live = true
    setPlan(null)
    setStatus(null)
    setError(null)
    latestPlan(field.id)
      .then(async (d) => {
        if (!live) return
        setPlan(d)
        await refresh(d)
      })
      .catch(() => live && setError('Chưa tải được kế hoạch của thửa này.'))
    return () => {
      live = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [field?.id])

  if (!field) {
    return (
      <AppShell>
        <div className="rec-empty">
          <h1>Chưa có thửa ruộng</h1>
          <a className="btn btn--primary" href={href('/ruong/moi')}>
            Khoanh thửa ruộng
          </a>
        </div>
      </AppShell>
    )
  }

  const send = async (body: ObservationWrite) => {
    if (!plan) return
    setBusy(true)
    setError(null)
    try {
      await api.addObservation(field.id, body)
      await refresh(plan)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Không gửi được.')
    } finally {
      setBusy(false)
    }
  }

  const replan = async () => {
    setBusy(true)
    try {
      await refreshPlan(field.id)
      navigate('/de-xuat', { thua: field.id })
    } catch {
      setError('Engine chưa lập lại được kế hoạch.')
      setBusy(false)
    }
  }

  return (
    <AppShell>
      <div className="rec track">
        <header className="rec-bar">
          <label className="rec-bar__switch">
            <span className="visually-hidden">Thửa ruộng</span>
            <select value={field.id} onChange={(e) => navigate('/theo-doi', { thua: e.target.value })}>
              {fields.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
            </select>
          </label>
          <span className="rec-bar__meta">Theo dõi vụ</span>
        </header>

        {field.pending && <p className="rec-notice">Thửa chưa đồng bộ lên máy chủ — cần kết nối để ghi số đo.</p>}
        {error && (
          <p className="rec-error" role="alert">
            {error}
          </p>
        )}
        {!plan && !error && !field.pending && <div className="rec-skeleton" aria-busy="true">Đang tải kế hoạch…</div>}

        {plan && (
          <>
            <StatusPanel plan={plan} status={status} fieldId={field.id} busy={busy} onReplan={replan} />
            <Entry plan={plan} busy={busy} onSend={send} />
            {obs.length > 0 && (
              <section aria-labelledby="obs-title">
                <h2 id="obs-title" className="rec-h2">
                  Đã ghi
                </h2>
                <ul className="obs-list">
                  {obs.slice(0, 8).map((o) => (
                    <li key={o.id}>
                      <span>{new Date(o.observed_at).toLocaleDateString('vi-VN')}</span>
                      <span>{VAR_VI[o.variable] ?? o.variable}</span>
                      <strong>
                        {o.value !== null ? `${o.value.toLocaleString('vi-VN')} ${o.unit ?? ''}` : (TEXT_VI[o.value_text ?? ''] ?? o.value_text ?? '—')}
                      </strong>
                      <span className="obs-list__kind">{o.evidence_kind === 'OBSERVED_FIELD' ? 'Đo tại ruộng' : 'Nông dân báo'}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        )}
      </div>
    </AppShell>
  )
}

function StatusPanel({ plan, status, fieldId, busy, onReplan }: { plan: DecisionPackage; status: PlanStatus | null; fieldId: string; busy: boolean; onReplan: () => void }) {
  const chosen = readChoice(fieldId) ?? plan.options[0]?.sequence_id
  const chains = [plan.baseline, ...plan.options]
  const name = (seq: string) => {
    const c = chains.find((o) => o.sequence_id === seq)
    if (!c) return seq
    return `${c.is_baseline ? 'Đang làm' : (c.strategy_name_vi ?? 'Phương án')} (${c.seasons.map((s) => CROP_SHORT[s.crop] ?? s.crop).join(' – ')})`
  }
  const fired = status?.fired ?? []
  const mine = fired.filter((f) => f.sequence_id === chosen)
  const shown = mine.length ? mine : fired
  const others = new Set(fired.filter((f) => f.sequence_id !== chosen).map((f) => f.sequence_id)).size

  return (
    <section className="track-status" data-state={status?.status ?? 'loading'} aria-live="polite" aria-labelledby="ts-title">
      <div className="track-status__head">
        <div>
          <p className="answer__kicker">Kế hoạch lập ngày {new Date(plan.as_of).toLocaleDateString('vi-VN')}</p>
          <h1 id="ts-title" className="track-status__title">
            {!status ? 'Đang kiểm tra…' : status.status === 'OK' ? 'Kế hoạch vẫn dùng được' : 'Cần lập lại kế hoạch'}
          </h1>
          {status?.status === 'OK' && <p className="track-status__sub">Chưa có số đo nào vượt ngưỡng cảnh báo.</p>}
        </div>
        <div className="track-status__actions">
          {status?.status === 'REPLAN_REQUIRED' && (
            <button type="button" className="btn btn--primary" disabled={busy} onClick={onReplan}>
              Lập lại kế hoạch
            </button>
          )}
          <a className="btn btn--ghost" href={api.exportUrl(plan.decision_id)} target="_blank" rel="noreferrer">
            Bản tóm tắt 1 trang
          </a>
        </div>
      </div>
      {shown.length > 0 && (
        <ul className="fired">
          {shown.map((f) => (
            <li key={`${f.sequence_id}-${f.observation_id}-${f.season_index}-${f.condition}`}>
              <span className="fired__chain">{name(f.sequence_id)} · vụ {f.season_index}</span>
              <span>
                Đo được <strong>{typeof f.value === 'number' ? `${f.value.toLocaleString('vi-VN')} ${f.unit ?? ''}` : (TEXT_VI[f.value] ?? f.value)}</strong> ngày{' '}
                {new Date(f.observed_at).toLocaleDateString('vi-VN')} — vượt ngưỡng “{f.condition}”
              </span>
              <span className="fired__action">→ {f.action}</span>
            </li>
          ))}
        </ul>
      )}
      {mine.length > 0 && others > 0 && <p className="track-status__sub">{others} phương án khác cũng vượt ngưỡng.</p>}
    </section>
  )
}

function Entry({ plan, busy, onSend }: { plan: DecisionPackage; busy: boolean; onSend: (b: ObservationWrite) => void }) {
  const [date, setDate] = useState(today)
  const [kind, setKind] = useState<ObservationWrite['evidence_kind']>('OBSERVED_FIELD')
  const [ecw, setEcw] = useState('')
  const [drain, setDrain] = useState<'good' | 'poor'>('good')
  const [season, setSeason] = useState('1')
  const ecwNum = Number(ecw.replace(',', '.'))
  const ecwOk = ecw.trim() !== '' && Number.isFinite(ecwNum) && ecwNum >= 0 && ecwNum <= 60
  const base = { observed_at: date, evidence_kind: kind }

  return (
    <section className="entry" aria-labelledby="entry-title">
      <h2 id="entry-title" className="rec-h2">
        Ghi số đo
      </h2>
      <div className="entry__common">
        <label>
          <span>Ngày đo</span>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        </label>
        <label>
          <span>Ai đo</span>
          <select value={kind} onChange={(e) => setKind(e.target.value as ObservationWrite['evidence_kind'])}>
            <option value="OBSERVED_FIELD">Cán bộ đo tại ruộng</option>
            <option value="REPORTED_BY_FARMER">Nông dân báo</option>
          </select>
        </label>
      </div>
      {date < plan.as_of && (
        <p className="step__hint">Số đo trước ngày lập kế hoạch ({new Date(plan.as_of).toLocaleDateString('vi-VN')}) không được so với ngưỡng của kế hoạch này.</p>
      )}

      <div className="entry__grid">
        <form
          className="entry__card"
          onSubmit={(e) => {
            e.preventDefault()
            if (ecwOk) onSend({ ...base, variable: 'canal_ecw', value: ecwNum, unit: 'dS/m' })
          }}
        >
          <label>
            <span>Độ mặn nước kênh (ECw, dS/m)</span>
            <input inputMode="decimal" placeholder="vd. 1,5" value={ecw} onChange={(e) => setEcw(e.target.value)} aria-describedby="ecw-help" />
          </label>
          <p id="ecw-help" className="step__hint">
            {ecwOk ? `≈ ${(ecwNum * PER_MILLE).toLocaleString('vi-VN', { maximumFractionDigits: 2 })} ‰ · ` : ''}1 dS/m ≈ 0,64 ‰. Đo bằng bút EC cầm tay.
          </p>
          {ecw.trim() !== '' && !ecwOk && <p className="rec-error">Nhập số từ 0 đến 60.</p>}
          <button type="submit" className="btn btn--primary btn--sm" disabled={busy || !ecwOk}>
            Ghi độ mặn
          </button>
        </form>

        <form
          className="entry__card"
          onSubmit={(e) => {
            e.preventDefault()
            onSend({ ...base, variable: 'drainage', value_text: drain })
          }}
        >
          <label>
            <span>Thoát nước sau mưa lớn</span>
            <select value={drain} onChange={(e) => setDrain(e.target.value as 'good' | 'poor')}>
              <option value="good">Tốt — rút hết trong 1 ngày</option>
              <option value="poor">Kém — còn đọng nước sau 1 ngày</option>
            </select>
          </label>
          <button type="submit" className="btn btn--primary btn--sm" disabled={busy}>
            Ghi thoát nước
          </button>
        </form>

        <form
          className="entry__card"
          onSubmit={(e) => {
            e.preventDefault()
            const w = plan.windows[Number(season) - 1]
            onSend({ ...base, variable: 'season_closed', value: Number(season), value_text: w?.id, note: w ? `Đã thu hoạch vụ ${w.name_vi}` : undefined })
          }}
        >
          <label>
            <span>Đóng vụ (đã thu hoạch)</span>
            <select value={season} onChange={(e) => setSeason(e.target.value)}>
              {plan.windows.map((w, i) => (
                <option key={w.id} value={i + 1}>
                  Vụ {w.name_vi.split(' /')[0]}
                </option>
              ))}
            </select>
          </label>
          <button type="submit" className="btn btn--primary btn--sm" disabled={busy}>
            Ghi đóng vụ
          </button>
        </form>
      </div>
    </section>
  )
}
