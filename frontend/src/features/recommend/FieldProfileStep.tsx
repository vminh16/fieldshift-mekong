import { useEffect, useState } from 'react'
import type { CropId, DecisionPackage, FieldProfile } from '../../../../contracts/types'
import { api, type CatalogCrop } from '../../shared/api/client'
import { CROP_SHORT } from '../../shared/decision/source'
import { saveProfile, type LocalField } from '../../shared/fields/store'

const IRRIGATION: [NonNullable<FieldProfile['irrigation']>, string][] = [
  ['full', 'Đủ nước quanh năm'],
  ['canal_limited', 'Kênh có lúc thiếu'],
  ['rainfed', 'Nhờ nước mưa'],
]
const DRAINAGE: [NonNullable<FieldProfile['drainage']>, string][] = [
  ['good', 'Tốt (rút hết trong 1 ngày)'],
  ['poor', 'Kém (đọng nước lâu)'],
  ['unknown', 'Chưa rõ'],
]
const EQUIPMENT: [string, string][] = [
  ['may_bom', 'Máy bơm'],
  ['may_cay', 'Máy cày / xới'],
  ['may_gieo', 'Máy gieo hạt'],
  ['may_gat', 'Máy gặt'],
]
const ASSUMED = 'Giả định mặc định'

/**
 * "Xác nhận tình trạng ruộng": what the engine otherwise assumes. Unanswered items stay null so the
 * engine labels them `assumed_default` instead of pretending the farmer said so.
 */
export function FieldProfileStep({ field, decision, busy, onSaved }: { field: LocalField; decision: DecisionPackage; busy: boolean; onSaved: () => void }) {
  const p = field.profile
  const windows = decision.windows
  const [open, setOpen] = useState(false)
  const [catalog, setCatalog] = useState<CatalogCrop[] | null>(null)
  const [baseline, setBaseline] = useState<(CropId | '')[]>(() => windows.map((_, i) => p?.baseline?.[i] ?? ''))
  const [irrigation, setIrrigation] = useState(p?.irrigation ?? null)
  const [drainage, setDrainage] = useState(p?.drainage ?? null)
  const [coastal, setCoastal] = useState(Boolean(p?.coastal_salinity_risk))
  const [equipment, setEquipment] = useState<string[]>(p?.equipment ?? [])
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open && !catalog) api.crops().then((c) => setCatalog(c.crops), () => setCatalog([]))
  }, [open, catalog])

  const missing = [
    !p?.baseline && 'cây đang trồng (giả định lúa 3 vụ)',
    !p?.irrigation && 'nguồn nước tưới (giả định đủ nước)',
    (!p?.drainage || p.drainage === 'unknown') && 'thoát nước (chưa rõ)',
  ].filter(Boolean) as string[]
  const cropsFor = (windowId: string) => {
    const allowed = catalog?.filter((c) => c.allowed_windows.includes(windowId)).map((c) => c.id)
    return allowed?.length ? allowed : (Object.keys(CROP_SHORT) as CropId[])
  }
  const fullBaseline = baseline.every(Boolean)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await saveProfile(field.id, {
        // Partly answered chains are not sent: the engine needs one crop per season.
        baseline: fullBaseline ? (baseline as CropId[]) : null,
        irrigation,
        drainage,
        coastal_salinity_risk: coastal,
        equipment,
      })
      setOpen(false)
      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không lưu được.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="step" aria-labelledby="step-title">
      <div className="step__bar">
        <div>
          <h2 id="step-title" className="step__title">
            Xác nhận tình trạng ruộng
          </h2>
          <p className="step__sum">
            {missing.length ? (
              <>
                <span className="step__assumed">{ASSUMED}</span> cho {missing.join(', ')}.
              </>
            ) : (
              'Đã khai báo đủ. Đề xuất dựa trên thông tin bạn xác nhận.'
            )}
          </p>
        </div>
        <button type="button" className="btn btn--ghost btn--sm" aria-expanded={open} aria-controls="step-form" disabled={field.pending} onClick={() => setOpen(!open)}>
          {open ? 'Đóng' : missing.length ? 'Trả lời' : 'Sửa'}
        </button>
      </div>

      {open && (
        <form id="step-form" className="step__form" onSubmit={submit}>
          <fieldset>
            <legend>Đang trồng gì mỗi vụ?</legend>
            <div className="step__seasons">
              {windows.map((w, i) => (
                <label key={w.id}>
                  <span>{w.name_vi.split(' /')[0]}</span>
                  <select
                    value={baseline[i]}
                    onChange={(e) => {
                      const next = [...baseline]
                      next[i] = e.target.value as CropId | ''
                      setBaseline(next)
                    }}
                  >
                    <option value="">Chưa trả lời</option>
                    {cropsFor(w.id).map((c) => (
                      <option key={c} value={c}>
                        {CROP_SHORT[c] ?? c}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
            {!fullBaseline && <p className="step__hint">Chọn đủ {windows.length} vụ; nếu không, engine giả định lúa liên tục.</p>}
          </fieldset>

          <Choice legend="Nước tưới" name="irr" value={irrigation} options={IRRIGATION} onChange={setIrrigation} />
          <Choice legend="Thoát nước sau mưa lớn" name="drain" value={drainage} options={DRAINAGE} onChange={setDrainage} />

          <fieldset>
            <legend>Nguy cơ mặn</legend>
            <label className="step__check">
              <input type="checkbox" checked={coastal} onChange={(e) => setCoastal(e.target.checked)} />
              Ruộng ven biển, có lúc nước kênh bị mặn
            </label>
          </fieldset>

          <fieldset>
            <legend>Máy móc sẵn có</legend>
            <div className="step__row">
              {EQUIPMENT.map(([id, label]) => (
                <label key={id} className="step__check">
                  <input
                    type="checkbox"
                    checked={equipment.includes(id)}
                    onChange={(e) => setEquipment(e.target.checked ? [...equipment, id] : equipment.filter((x) => x !== id))}
                  />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>

          <div className="step__foot">
            <button type="submit" className="btn btn--primary" disabled={saving || busy}>
              {saving ? 'Đang lưu…' : 'Lưu và tính lại đề xuất'}
            </button>
            <p className="step__hint">Câu nào để trống, engine dùng giả định mặc định và ghi rõ trên kết quả.</p>
            {error && (
              <p className="rec-error" role="alert">
                {error}
              </p>
            )}
          </div>
        </form>
      )}
    </section>
  )
}

function Choice<T extends string>({ legend, name, value, options, onChange }: { legend: string; name: string; value: T | null; options: [T, string][]; onChange: (v: T | null) => void }) {
  return (
    <fieldset>
      <legend>
        {legend} {value === null && <span className="step__assumed">{ASSUMED}</span>}
      </legend>
      <div className="step__row">
        {options.map(([id, label]) => (
          <label key={id} className="step__radio">
            <input type="radio" name={name} checked={value === id} onChange={() => onChange(id)} />
            {label}
          </label>
        ))}
        {value !== null && (
          <button type="button" className="step__clear" onClick={() => onChange(null)}>
            Bỏ chọn
          </button>
        )}
      </div>
    </fieldset>
  )
}
