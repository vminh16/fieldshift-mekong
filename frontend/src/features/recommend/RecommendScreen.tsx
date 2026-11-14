import { useEffect, useState } from 'react'
import { AppShell } from '../shell/AppShell'
import { href, navigate } from '../../shared/router'
import { formatHa } from '../../shared/geo/area'
import { nearestProvince } from '../../shared/geo/mekongProvinces'
import { getField, useActiveFieldId, useFields, type LocalField } from '../../shared/fields/store'
import {
  CONFIDENCE_VI, CROP_SHORT, SOIL_INDICATOR, STATUS_VI, UNKNOWN_VI, confidenceOf, cropTone, loadDecision,
  type DecisionPackage, type DecisionResult, type Option,
} from '../../shared/decision/source'
import { readChoice, refreshPlan, writeChoice } from '../../shared/decision/plans'
import { yearOutlookOf } from '../../shared/decision/yearOutlook'
import { YearOutlookBanner } from './YearOutlookBanner'
import { FieldProfileStep } from './FieldProfileStep'
import { CompareBars, PairedBars, RotationRibbon } from './charts'
import { ParcelMiniMap } from './ParcelMiniMap'
import { SeasonTimeline } from './SeasonTimeline'
import { CROP_PHOTO } from '../../shared/decision/photos'
import './recommend.css'

/* ---------- plain-language helpers (format engine output; never decide anything) ---------- */
const nf = (n: number) => n.toLocaleString('vi-VN', { maximumFractionDigits: 0 })
const crop = (c: string) => CROP_SHORT[c] ?? c
const windowName = (w: string) => w.split(' /')[0]
const PRIORITY: Record<string, string> = {
  avoid_crop_failure: 'tránh mất mùa',
  save_water: 'tiết kiệm nước',
  soil_health: 'cải thiện đất',
  supplemental_income: 'thêm thu nhập',
  minimal_change: 'ít thay đổi',
}
function headline(pick: Option, base: Option) {
  const changed = pick.seasons.filter((s, i) => s.crop !== base.seasons[i]?.crop)
  if (changed.length === 0) return { main: `Giữ ${crop(base.seasons[0].crop).toLowerCase()} cả 3 vụ`, sub: '' }
  const first = changed[0]
  const was = crop(base.seasons[first.index - 1]?.crop ?? 'rice').toLowerCase()
  const main =
    first.crop === 'fallow_cover'
      ? `Vụ ${windowName(first.window_name_vi)} cho đất nghỉ, trồng cây phủ đất`
      : `Vụ ${windowName(first.window_name_vi)} trồng ${crop(first.crop)} thay ${was}`
  const kept = pick.seasons.filter((s, i) => s.crop === base.seasons[i]?.crop)
  const sub = changed.length > 1 ? `Đổi ${changed.length} vụ so với hiện nay.` : kept.length ? `${kept.length === 2 ? 'Hai' : 'Các'} vụ còn lại giữ ${crop(kept[0].crop).toLowerCase()} như cũ.` : ''
  return { main, sub }
}

const harvests = (o: Option) => o.seasons.filter((s) => s.crop !== 'fallow_cover').length
const waterPct = (o: Option, base: Option) => {
  const d = o.delta_vs_baseline.sc_clim?.irrigation_need?.value
  const b = base.metrics.sc_clim?.irrigation_need.value
  return d != null && b ? Math.round((d / b) * 100) : null
}

export function RecommendScreen({ fieldId }: { fieldId: string | null }) {
  const fields = useFields()
  const activeId = useActiveFieldId()
  const field = getField(fieldId) ?? fields.find((f) => f.id === activeId) ?? null
  const [result, setResult] = useState<DecisionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [replanning, setReplanning] = useState(false)

  // Profile saved → run a fresh plan so the answer reflects what the farmer just confirmed.
  const replan = () => {
    if (!field) return
    setReplanning(true)
    setError(null)
    refreshPlan(field.id)
      .then((decision) => setResult({ decision, source: 'engine' }))
      .catch(() => setError('Đã lưu, nhưng engine chưa tính lại được. Thử tải lại trang.'))
      .finally(() => setReplanning(false))
  }

  useEffect(() => {
    if (!field) return
    let live = true
    setResult(null)
    setError(null)
    loadDecision(field)
      .then((r) => live && setResult(r))
      .catch(() => live && setError('Không tải được đề xuất.'))
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
          <p>Khoanh một thửa để nhận đề xuất luân canh cho thửa đó.</p>
          <a className="btn btn--primary" href={href('/ruong/moi')}>
            Khoanh thửa ruộng
          </a>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="rec">
        <ParcelBar field={field} fields={fields} result={result} />
        {error && <p className="rec-error">{error}</p>}
        {result?.notice && (
          <p className="rec-notice" role="status">
            {result.notice}
          </p>
        )}
        {result && result.source === 'engine' && <FieldProfileStep field={field} decision={result.decision} busy={replanning} onSaved={replan} />}
        {replanning && (
          <p className="rec-notice" role="status">
            Đã lưu. Engine đang tính lại đề xuất…
          </p>
        )}
        {!result && !error && (
          <div className="rec-skeleton" aria-busy="true">
            <span>Engine đang tính đề xuất cho thửa này… lần đầu có thể mất khoảng nửa phút.</span>
          </div>
        )}
        {result && <Recommendation key={result.decision.decision_id} field={field} decision={result.decision} />}
      </div>
    </AppShell>
  )
}

function ParcelBar({ field, fields, result }: { field: LocalField; fields: LocalField[]; result: DecisionResult | null }) {
  const place = field.place_name || nearestProvince(field.centroid.lat, field.centroid.lng, 0.6)?.name || 'ĐBSCL'
  return (
    <header className="rec-bar">
      <label className="rec-bar__switch">
        <span className="visually-hidden">Thửa ruộng</span>
        <select value={field.id} onChange={(e) => navigate('/de-xuat', { thua: e.target.value })}>
          {fields.map((f) => (
            <option key={f.id} value={f.id}>
              {f.name}
            </option>
          ))}
        </select>
      </label>
      <span className="rec-bar__meta">
        {field.sample ? 'Ruộng mẫu' : field.area_ha !== null ? formatHa(field.area_ha) : 'Diện tích chưa biết'} · {place}
      </span>
      {result?.source === 'mock' && <span className="rec-tag">Dữ liệu mẫu</span>}
    </header>
  )
}

function Recommendation({ field, decision: d }: { field: LocalField; decision: DecisionPackage }) {
  const base = d.baseline
  const [shownId, setShownId] = useState(d.options[0]?.sequence_id)
  const [chosen, setChosen] = useState(() => readChoice(field.id))
  const [why, setWhy] = useState(false)
  const pick = d.options.find((o) => o.sequence_id === shownId) ?? d.options[0]
  if (!pick) return <p className="rec-error">Engine chưa tìm được chuỗi nào phù hợp hơn cách đang làm.</p>

  const isTop = pick.sequence_id === d.options[0].sequence_id
  const h = headline(pick, base)
  const pct = waterPct(pick, base)
  const dry = pick.delta_vs_baseline.sc_dry?.irrigation_need?.value ?? null
  const status = STATUS_VI[pick.decision_status]
  const conf = confidenceOf(pick)
  const saltDays = pick.salinity_overlap_avoided_days?.typical
  const yo = yearOutlookOf(d)
  const priorities = ((d.request as { priorities?: string[] } | undefined)?.priorities ?? []).map((p) => PRIORITY[p] ?? p)
  const tried = (d.stats as { generated?: number }).generated
  const isChosen = chosen === pick.sequence_id
  const baseName = new Set(base.seasons.map((s) => s.crop)).size === 1 ? `${crop(base.seasons[0].crop)} 3 vụ` : 'Cách đang làm'

  const choose = () => {
    const next = isChosen ? null : pick.sequence_id
    writeChoice(field.id, next)
    setChosen(next)
  }

  return (
    <>
      {yo && (
        <YearOutlookBanner
          yo={yo}
          action={
            <a className="btn btn--ghost btn--sm" href={href('/mo-phong', { thua: field.id, chuoi: d.options[0].sequence_id })}>
              Xem ruộng của bạn trong năm như vậy
            </a>
          }
        />
      )}

      {/* ---------- the answer ---------- */}
      <section className="answer" aria-labelledby="answer-title">
        <ParcelMiniMap field={field} />
        <div className="answer__head">
          <p className="answer__kicker">
            {isTop ? 'Engine đề xuất' : 'Lựa chọn khác'} · 3 vụ tới
            {isChosen && <span className="answer__chosen">Bạn đã chọn</span>}
          </p>
          {status && (
            <p className="status-badge" data-tone={status.tone}>
              {status.text}
            </p>
          )}
          <h1 id="answer-title" className="answer__title">
            {h.main}
          </h1>
          {h.sub && <p className="answer__sub">{h.sub}</p>}
        </div>

        <SeasonTimeline pick={pick.seasons} base={base.seasons} today={d.as_of} />

        <div className="answer__rest">
          <dl className="gains">
            {pct !== null && (
              <div>
                <dt>{pct < 0 ? 'Ít nước tưới hơn' : 'Nhiều nước tưới hơn'}</dt>
                <dd>{Math.abs(pct)}%</dd>
              </div>
            )}
            {dry !== null && (
              <div>
                <dt>Năm khô hạn, bớt</dt>
                <dd>
                  {nf(Math.abs(dry) * 10)}
                  <small> m³/ha</small>
                </dd>
              </div>
            )}
            {saltDays ? (
              <div>
                <dt>Né mùa mặn</dt>
                <dd>
                  {saltDays}
                  <small> ngày ít trùng hơn</small>
                </dd>
              </div>
            ) : null}
          </dl>

          {pick.soil_benefit.indicators.length > 0 && (
            <p className="soil-line">
              <span>Lợi ích cho đất (định tính):</span> {pick.soil_benefit.indicators.map((i) => SOIL_INDICATOR[i] ?? i).join(' · ')}
            </p>
          )}

          {conf && (
            <p className="conf-line">
              Độ tin cậy: <strong>{CONFIDENCE_VI[conf.level] ?? conf.level}</strong>
              {/^\d+\/\d+$/.test(conf.robust_scenarios) && <> · Tốt hơn cách đang làm ở {conf.robust_scenarios} kịch bản thời tiết</>}
              {conf.unknowns.length > 0 && <> · Còn thiếu: {conf.unknowns.map((u) => UNKNOWN_VI[u] ?? u).join(', ')}</>}
            </p>
          )}

          {(pick.checklist.length > 0 || pick.triggers.length > 0) && (
            <div className="todo">
              {pick.checklist.length > 0 && (
                <div className="conditions">
                  <p>Trước khi gieo, cần làm</p>
                  <ol>
                    {pick.checklist.map((c) => (
                      <li key={c}>{c}</li>
                    ))}
                  </ol>
                </div>
              )}
              {pick.triggers.length > 0 && (
                <div className="triggers">
                  <p>Khi nào phải đổi kế hoạch</p>
                  <ul>
                    {pick.triggers.map((t) => (
                      <li key={`${t.season_index}-${t.condition}`}>
                        <span>Nếu {t.condition}</span>
                        <span aria-hidden="true"> → </span>
                        <strong>{t.action}</strong>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {pick.summary_vi && <p className="answer__summary">{pick.summary_vi}</p>}

          <div className="answer__actions">
            <button type="button" className={isChosen ? 'btn btn--ghost' : 'btn btn--primary'} onClick={choose}>
              {isChosen ? 'Bỏ chọn' : 'Chọn chuỗi này'}
            </button>
            <a className="btn btn--ghost" href={href('/mo-phong', { thua: field.id, chuoi: pick.sequence_id })}>
              Mô phỏng trên ruộng
            </a>
            <button
              type="button"
              className="btn btn--ghost"
              aria-expanded={why}
              aria-controls="why"
              onClick={() => {
                setWhy(true)
                requestAnimationFrame(() => document.getElementById('why')?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
              }}
            >
              Vì sao đề xuất?
            </button>
          </div>
          {priorities.length > 0 && (
            <p className="answer__basis">
              Xếp theo ưu tiên của bạn: {priorities.join(' · ')}
              {tried ? ` · chọn từ ${tried} chuỗi đã thử` : ''}
            </p>
          )}
        </div>
      </section>

      {/* ---------- alternatives ---------- */}
      <section aria-labelledby="alt-title">
        <h2 id="alt-title" className="rec-h2">
          Lựa chọn khác
        </h2>
        <ul className="alts">
          {d.options
            .filter((o) => o.sequence_id !== pick.sequence_id)
            .map((o) => {
              const p = waterPct(o, base)
              return (
                <li key={o.sequence_id}>
                  <button type="button" className="alt" onClick={() => setShownId(o.sequence_id)}>
                    <AltPhoto option={o} base={base} />
                    <span className="alt__name">
                      {o.strategy_name_vi}
                      {o.sequence_id === d.options[0].sequence_id && <span className="alt__top">Engine đề xuất</span>}
                    </span>
                    <ChainStrip option={o} />
                    <span className="alt__facts">
                      {p !== null && <span>{`${p < 0 ? '−' : '+'}${Math.abs(p)}% nước`}</span>}
                      <span>{harvests(o)} vụ thu</span>
                      <span>{STATUS_VI[o.decision_status]?.text ?? o.decision_status}</span>
                      {confidenceOf(o) && <span>Tin cậy {(CONFIDENCE_VI[confidenceOf(o)!.level] ?? '').toLowerCase()}</span>}
                    </span>
                    <span className="alt__go">Xem</span>
                  </button>
                </li>
              )
            })}
          <li>
            <div className="alt alt--base">
              <AltPhoto option={base} base={base} />
              <span className="alt__name">Giữ như hiện nay</span>
              <ChainStrip option={base} />
              <span className="alt__facts">
                <span>Tốn nước tưới nhất</span>
                <span>Không phải thay đổi</span>
              </span>
              <span />
            </div>
          </li>
        </ul>
      </section>

      {/* ---------- explanation, on demand ---------- */}
      <Why open={why} onToggle={setWhy} d={d} pick={pick} base={base} baseName={baseName} />
    </>
  )
}

/** Photo of the crop that changes (or the current crop for "keep as is"). */
function AltPhoto({ option, base }: { option: Option; base: Option }) {
  const changed = option.seasons.find((s, i) => s.crop !== base.seasons[i]?.crop) ?? option.seasons[0]
  const photo = CROP_PHOTO[changed.crop]
  return photo ? <img className="alt__photo" src={photo.src} alt="" loading="lazy" /> : <span className="alt__photo" />
}

function ChainStrip({ option }: { option: Option }) {
  return (
    <span className="chain" aria-label={option.seasons.map((s) => crop(s.crop)).join(', ')}>
      {option.seasons.map((s) => (
        <span key={s.index} data-tone={cropTone(s.crop)}>
          {crop(s.crop)}
        </span>
      ))}
    </span>
  )
}

type Tab = 'water' | 'soil' | 'calendar' | 'sources'
const TABS: [Tab, string][] = [
  ['water', 'Nước tưới'],
  ['soil', 'Đất'],
  ['calendar', 'Lịch vụ'],
  ['sources', 'Nguồn & giới hạn'],
]

function Why({
  open,
  onToggle,
  d,
  pick,
  base,
  baseName,
}: {
  open: boolean
  onToggle: (o: boolean) => void
  d: DecisionPackage
  pick: Option
  base: Option
  baseName: string
}) {
  const [tab, setTab] = useState<Tab>('water')
  const irr = (o: Option, sc: string) => o.metrics[sc]?.irrigation_need.value ?? 0
  const pickName = pick.strategy_name_vi ?? 'Đề xuất'
  const hasDry = d.scenarios.some((s) => s.scenario_id === 'sc_dry')
  const failed = d.gates.filter((g) => !g.passed)
  const sources = [...new Set(pick.reasons.flatMap((r) => r.evidence_ids ?? []))].map((id) => d.evidence[id]?.source).filter(Boolean)
  const soilCols: [string, string[], 'pick' | 'base'][] = [
    [pickName, pick.soil_benefit.indicators, 'pick'],
    [baseName, base.soil_benefit.indicators, 'base'],
  ]

  return (
    <section id="why" className="why" aria-labelledby="why-title">
      <button type="button" className="why__toggle" aria-expanded={open} onClick={() => onToggle(!open)}>
        <h2 id="why-title" className="rec-h2">
          Vì sao đề xuất chuỗi này?
        </h2>
        <span aria-hidden="true">{open ? '−' : '+'}</span>
      </button>
      {open && (
        <div className="why__panel">
          <div className="tabs" role="tablist">
            {TABS.map(([id, label]) => (
              <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)}>
                {label}
              </button>
            ))}
          </div>

          {tab === 'water' && (
            <div className="why__grid">
              <div>
                <p className="why__lead">Cả 3 vụ, năm thời tiết bình thường</p>
                <CompareBars
                  unit="mm"
                  bars={[
                    { label: pickName, value: irr(pick, 'sc_clim'), tone: 'pick' },
                    { label: baseName, value: irr(base, 'sc_clim'), tone: 'base' },
                  ]}
                />
              </div>
              {hasDry && (
                <div>
                  <p className="why__lead">Năm thường so với năm khô hạn</p>
                  <PairedBars
                    unit="mm"
                    baseLabel={baseName}
                    pickLabel={pickName}
                    groups={[
                      { label: 'Năm thường', base: irr(base, 'sc_clim'), pick: irr(pick, 'sc_clim') },
                      { label: 'Năm khô hạn', base: irr(base, 'sc_dry'), pick: irr(pick, 'sc_dry') },
                    ]}
                  />
                  <ul className="legend legend--series">
                    <li>
                      <span className="legend__swatch" data-series="pick" />
                      {pickName}
                    </li>
                    <li>
                      <span className="legend__swatch" data-series="base" />
                      {baseName}
                    </li>
                  </ul>
                </div>
              )}
              <p className="why__note">Tính từ thời tiết 2001–2025 (NASA POWER) cho lịch gieo dự kiến. 1 mm nước tưới = 10 m³ trên 1 ha.</p>
            </div>
          )}

          {tab === 'soil' && (
            <div className="soil">
              {soilCols.map(([title, items, tone]) => (
                <div key={tone} className="soil__col" data-tone={tone}>
                  <p className="soil__title">
                    {title} <span>{items.length}</span>
                  </p>
                  <ul>
                    {items.map((i) => (
                      <li key={i}>{SOIL_INDICATOR[i] ?? i}</li>
                    ))}
                  </ul>
                </div>
              ))}
              <p className="why__note">Lợi ích tiềm năng, đánh giá định tính. Chưa có mô hình đất đã hiệu chỉnh nên không cho điểm.</p>
            </div>
          )}

          {tab === 'calendar' && (
            <>
              <RotationRibbon
                rows={[
                  { key: 'pick', label: pickName, seasons: pick.seasons, emphasis: true },
                  { key: 'base', label: baseName, seasons: base.seasons },
                ]}
              />
              <p className="why__note">Khoảng trống giữa các vụ là thời gian làm đất, phơi ruộng.</p>
            </>
          )}

          {tab === 'sources' && (
            <div className="sources">
              <ul>
                {pick.reasons.map((r) => (
                  <li key={r.text}>{r.text}</li>
                ))}
              </ul>
              {failed.length > 0 && (
                <div className="limits">
                  <p>Giới hạn của đề xuất</p>
                  <ul>
                    {failed.map((g) => (
                      <li key={g.gate}>{g.message.replace(/\s*→.*$/, '')}</li>
                    ))}
                  </ul>
                </div>
              )}
              <p className="why__note">
                Ảnh cây trồng: Wikimedia Commons —{' '}
                {Object.entries(CROP_PHOTO)
                  .filter(([c]) => [base, ...d.options].some((o) => o.seasons.some((s) => s.crop === c)))
                  .map(([c, ph], i) => (
                    <span key={c}>
                      {i > 0 && ', '}
                      <a href={ph.page} target="_blank" rel="noreferrer">
                        {CROP_SHORT[c] ?? c}
                      </a>{' '}
                      ({ph.author}, {ph.license})
                    </span>
                  ))}
                ; đã cắt và thu nhỏ.
              </p>
              <p className="why__note">
                Nguồn: {sources.join(' · ')}. {d.excluded.length} chuỗi bị loại vì không hợp lịch vụ hoặc ràng buộc của ruộng.
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
