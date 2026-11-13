import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { AppShell } from '../shell/AppShell'
import { ParcelMiniMap } from './ParcelMiniMap'
import { href, navigate } from '../../shared/router'
import { formatHa } from '../../shared/geo/area'
import { nearestProvince } from '../../shared/geo/mekongProvinces'
import { getField, useActiveFieldId, useFields, type LocalField } from '../../shared/fields/store'
import { CROP_SHORT, SOIL_INDICATOR, cropTone, loadDecision, type DecisionResult, type Option } from '../../shared/decision/source'
import { CompareBars, PairedBars, RotationRibbon, YearDots } from './charts'
import './recommend.css'

const isMonoculture = (o: Option) => new Set(o.seasons.map((s) => s.crop)).size === 1

export function RecommendScreen({ fieldId }: { fieldId: string | null }) {
  const fields = useFields()
  const activeId = useActiveFieldId()
  const field = getField(fieldId) ?? fields.find((f) => f.id === activeId) ?? null

  const [result, setResult] = useState<DecisionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pickId, setPickId] = useState<string | null>(null)
  const [showEvidence, setShowEvidence] = useState(false)

  useEffect(() => {
    if (!field) return
    let live = true
    setResult(null)
    setError(null)
    loadDecision(field)
      .then((r) => {
        if (!live) return
        setResult(r)
        setPickId(r.decision.options[0]?.sequence_id ?? null)
      })
      .catch(() => live && setError('Không tải được đề xuất.'))
    return () => {
      live = false
    }
    // Reload only when the parcel changes, not on every store update.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [field?.id])

  if (!field) {
    return (
      <AppShell>
        <div className="rec-empty">
          <h1>Chưa có thửa ruộng</h1>
          <p>Khoanh một thửa để engine đề xuất chuỗi luân canh cho thửa đó.</p>
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
        {error && <p className="rec-error">{error}</p>}
        {result && pickId ? (
          <Body
            parcel={<ParcelCard field={field} fields={fields} result={result} />}
            result={result}
            pickId={pickId}
            onPick={setPickId}
            showEvidence={showEvidence}
            onToggleEvidence={() => setShowEvidence(!showEvidence)}
          />
        ) : (
          <div className="rec-top">
            <ParcelCard field={field} fields={fields} result={null} />
            {!error && <Skeleton />}
          </div>
        )}
      </div>
    </AppShell>
  )
}

function ParcelCard({ field, fields, result }: { field: LocalField; fields: LocalField[]; result: DecisionResult | null }) {
  const place = field.place_name || nearestProvince(field.centroid.lat, field.centroid.lng, 0.6)?.name || 'ĐBSCL'
  return (
    <aside className="rec-card rec-parcel" aria-label="Thửa ruộng">
      <ParcelMiniMap field={field} />
      <label className="rec-parcel__switch">
        <span className="visually-hidden">Thửa ruộng</span>
        <select value={field.id} onChange={(e) => navigate('/mo-phong', { thua: e.target.value })}>
          {fields.map((f) => (
            <option key={f.id} value={f.id}>
              {f.name}
            </option>
          ))}
        </select>
      </label>
      <dl className="rec-parcel__facts">
        <div>
          <dt>Diện tích</dt>
          <dd>{field.sample ? 'Mẫu' : field.area_ha !== null ? formatHa(field.area_ha) : 'Chưa biết'}</dd>
        </div>
        <div>
          <dt>Vị trí</dt>
          <dd>{place}</dd>
        </div>
      </dl>
      {result && (
        <p className="rec-parcel__meta">
          Engine · {new Date(result.decision.generated_at).toLocaleDateString('vi-VN')}
          {result.source === 'mock' && <span className="rec-tag">Dữ liệu mẫu</span>}
        </p>
      )}
    </aside>
  )
}

function Body({
  parcel,
  result,
  pickId,
  onPick,
  showEvidence,
  onToggleEvidence,
}: {
  parcel: ReactNode
  result: DecisionResult
  pickId: string
  onPick: (id: string) => void
  showEvidence: boolean
  onToggleEvidence: () => void
}) {
  const d = result.decision
  const base = d.baseline
  const pick = d.options.find((o) => o.sequence_id === pickId) ?? d.options[0]
  const baseName = isMonoculture(base) ? `Độc canh ${(CROP_SHORT[base.seasons[0].crop] ?? '').toLowerCase()}` : 'Cách đang làm'
  const pickName = pick.strategy_name_vi ?? 'Đề xuất'

  // Only formatting here: every number below is an engine output for the same scenario.
  const clim = 'sc_clim'
  const dry = d.scenarios.some((s) => s.scenario_id === 'sc_dry') ? 'sc_dry' : null
  const irr = (o: Option, sc: string) => o.metrics[sc]?.irrigation_need.value ?? null
  const delta = pick.delta_vs_baseline[clim]?.irrigation_need?.value ?? null
  const baseIrr = irr(base, clim)
  const pickIrr = irr(pick, clim)
  const years = d.scenarios.find((s) => s.scenario_id === clim)?.name ?? 'Lịch sử'

  const failedGates = d.gates.filter((g) => !g.passed)
  const evidenceIds = useMemo(() => [...new Set(pick.reasons.flatMap((r) => r.evidence_ids ?? []))], [pick])

  return (
    <>
      {/* ---------- the parcel and its rotation, at a glance ---------- */}
      <div className="rec-top">
      {parcel}
      <section className="rec-card rec-hero" aria-labelledby="rec-hero-title">
        <div className="rec-hero__top">
          <h1 id="rec-hero-title">3 vụ tới</h1>
          <div className="rec-picks" role="tablist" aria-label="Phương án engine đề xuất">
            {d.options.map((o, i) => (
              <button key={o.sequence_id} role="tab" aria-selected={o.sequence_id === pick.sequence_id} onClick={() => onPick(o.sequence_id)}>
                {o.strategy_name_vi ?? `Phương án ${i + 1}`}
                {i === 0 && <span className="rec-picks__top">Xếp đầu</span>}
              </button>
            ))}
          </div>
        </div>
        <RotationRibbon
          rows={[
            { key: 'pick', label: pickName, seasons: pick.seasons, emphasis: true },
            { key: 'base', label: baseName, seasons: base.seasons },
          ]}
        />
        <div className="rec-hero__foot">
          <Legend options={[pick, base]} />
          <span className={`rec-status rec-status--${pick.decision_status === 'RECOMMEND_FOR_CONSIDERATION' ? 'ok' : 'check'}`}>
            {pick.decision_status === 'RECOMMEND_FOR_CONSIDERATION'
              ? 'Đáng cân nhắc'
              : pick.decision_status === 'CONDITIONAL_PENDING_CHECK'
                ? `Cần kiểm tra ${pick.checklist.length} điều trước khi gieo`
                : 'Chưa đủ bằng chứng'}
          </span>
        </div>
      </section>
      </div>

      {/* ---------- versus monoculture ---------- */}
      <div className="rec-grid">
        <section className="rec-card">
          <h2>Nước tưới cả 3 vụ</h2>
          {delta !== null && baseIrr ? (
            <p className="rec-hero-num" data-good={delta < 0 || undefined}>
              {delta < 0 ? '−' : '+'}
              {Math.round((Math.abs(delta) / baseIrr) * 100)}%
              <span>
                {delta < 0 ? 'ít hơn' : 'nhiều hơn'} {baseName.toLowerCase()}
              </span>
            </p>
          ) : null}
          {baseIrr !== null && pickIrr !== null && (
            <CompareBars
              unit="mm"
              bars={[
                { label: pickName, value: pickIrr, tone: 'pick' },
                { label: baseName, value: baseIrr, tone: 'base' },
              ]}
            />
          )}
          <p className="rec-note">Trung vị · {years}</p>
        </section>

        {dry && (
          <section className="rec-card">
            <h2>Khi gặp năm khô</h2>
            <PairedBars
              unit="mm"
              baseLabel={baseName}
              pickLabel={pickName}
              groups={[
                { label: 'Năm thường', base: irr(base, clim) ?? 0, pick: irr(pick, clim) ?? 0 },
                { label: 'Năm khô', base: irr(base, dry) ?? 0, pick: irr(pick, dry) ?? 0 },
              ]}
            />
            <SeriesKey base={baseName} pick={pickName} />
            <p className="rec-note">{d.scenarios.find((s) => s.scenario_id === dry)?.name}</p>
          </section>
        )}

        <section className="rec-card">
          <h2>24 kiểu năm có thể gặp</h2>
          <YearDots
            unit="mm"
            rows={[
              { label: pickName, tone: 'pick', points: (pick.distribution?.[clim] ?? []).map((p) => ({ year: p.year, value: p.irrigation_mm })) },
              { label: baseName, tone: 'base', points: (base.distribution?.[clim] ?? []).map((p) => ({ year: p.year, value: p.irrigation_mm })) },
            ]}
          />
          <p className="rec-note">Mỗi chấm = nước tưới 1 năm thời tiết · mm</p>
        </section>
      </div>

      <div className="rec-grid rec-grid--2">
        <section className="rec-card">
          <h2>Cho đất</h2>
          <div className="soil">
            <SoilColumn title={pickName} items={pick.soil_benefit.indicators} tone="pick" />
            <SoilColumn title={baseName} items={base.soil_benefit.indicators} tone="base" />
          </div>
          <p className="rec-note">Lợi ích tiềm năng, định tính — chưa có mô hình đất đã hiệu chỉnh</p>
        </section>

        <section className="rec-card">
          <h2>Trước khi gieo</h2>
          <ol className="todo">
            {pick.checklist.slice(0, 4).map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ol>
          {pick.triggers[0] && (
            <p className="rec-trigger">
              <strong>Nếu</strong> {pick.triggers[0].condition}
              <br />
              <strong>thì</strong> {pick.triggers[0].action}
            </p>
          )}
        </section>
      </div>

      {/* ---------- evidence ---------- */}
      <section className="rec-evidence">
        <div className="rec-evidence__line">
          <span>
            Dựa trên {evidenceIds.map((id) => d.evidence[id]?.source.split(' (')[0].split(':')[0]).filter(Boolean).join(' · ')}
          </span>
          <button type="button" className="btn btn--ghost btn--sm" aria-expanded={showEvidence} onClick={onToggleEvidence}>
            {showEvidence ? 'Thu gọn' : 'Bằng chứng'}
          </button>
        </div>
        {failedGates.length > 0 && <p className="rec-limits">Giới hạn: {failedGates.map((g) => g.message.replace(/\s*→.*$/, '')).join(' · ')}</p>}
        {showEvidence && (
          <div className="rec-evidence__more">
            <ul>
              {pick.reasons.map((r) => (
                <li key={r.text}>{r.text}</li>
              ))}
              {pick.risks.map((r) => (
                <li key={r.code} className="rec-risk">
                  {r.text}
                </li>
              ))}
            </ul>
            <p className="rec-note">
              {d.excluded.length} chuỗi khác đã bị loại vì vi phạm ràng buộc cứng · phiên bản {Object.values(d.versions).slice(0, 3).join(', ')}
            </p>
          </div>
        )}
      </section>
    </>
  )
}

function Legend({ options }: { options: Option[] }) {
  const tones = new Map<string, string>()
  for (const o of options) for (const s of o.seasons) if (!tones.has(cropTone(s.crop))) tones.set(cropTone(s.crop), CROP_SHORT[s.crop] ?? s.crop_name_vi)
  return (
    <ul className="legend">
      {[...tones].map(([tone, name]) => (
        <li key={tone}>
          <span className="legend__swatch" data-tone={tone} />
          {tone === 'legume' ? 'Cây họ đậu' : tone === 'other' ? 'Cây màu khác' : name}
        </li>
      ))}
    </ul>
  )
}

function SeriesKey({ base, pick }: { base: string; pick: string }) {
  return (
    <ul className="legend legend--series">
      <li>
        <span className="legend__swatch" data-series="pick" />
        {pick}
      </li>
      <li>
        <span className="legend__swatch" data-series="base" />
        {base}
      </li>
    </ul>
  )
}

function SoilColumn({ title, items, tone }: { title: string; items: string[]; tone: 'pick' | 'base' }) {
  return (
    <div className="soil__col" data-tone={tone}>
      <p className="soil__title">
        {title} <span>{items.length}</span>
      </p>
      {items.length ? (
        <ul>
          {items.map((i) => (
            <li key={i}>{SOIL_INDICATOR[i] ?? i}</li>
          ))}
        </ul>
      ) : (
        <p className="soil__none">Không có</p>
      )}
    </div>
  )
}

function Skeleton() {
  return (
    <div className="rec-skeleton" aria-busy="true" aria-label="Đang tải đề xuất">
      <span />
      <span />
      <span />
    </div>
  )
}
