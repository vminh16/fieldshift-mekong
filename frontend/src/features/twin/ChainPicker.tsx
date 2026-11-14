import { useEffect, useState } from 'react'
import type { CropId, DecisionPackage, Option } from '../../../../contracts/types'
import { CROP_SHORT } from '../../shared/decision/source'
import type { ChainSpec } from '../../shared/twin/source'

const CROPS = Object.keys(CROP_SHORT) as CropId[]
const chainText = (o: Option) => o.seasons.map((s) => CROP_SHORT[s.crop] ?? s.crop).join(' – ')
const windowName = (w: string) => w.split(' /')[0]

/** Pick what one side simulates: today's chain, an engine option, or any chain the user builds. */
export function ChainPicker({
  decision,
  value,
  onChange,
  locked,
  busy,
}: {
  decision: DecisionPackage
  value: ChainSpec
  onChange: (s: ChainSpec) => void
  locked: boolean
  busy: boolean
}) {
  const [draft, setDraft] = useState<CropId[]>(() => (value.kind === 'custom' ? value.crops : decision.baseline.seasons.map((s) => s.crop)))
  const [building, setBuilding] = useState(value.kind === 'custom')
  useEffect(() => {
    if (value.kind === 'custom') setDraft(value.crops)
  }, [value])

  const selectValue = building ? 'custom' : value.kind === 'engine' ? value.sequenceId : 'custom'
  const names = decision.windows.map((w) => windowName(w.name_vi))

  return (
    <div className="chain-pick">
      <label className="chain-pick__select">
        <span className="visually-hidden">Chuỗi luân canh</span>
        <select
          value={selectValue}
          disabled={locked || busy}
          onChange={(e) => {
            if (e.target.value === 'custom') return setBuilding(true)
            setBuilding(false)
            onChange({ kind: 'engine', sequenceId: e.target.value })
          }}
        >
          <option value={decision.baseline.sequence_id}>Đang làm · {chainText(decision.baseline)}</option>
          <optgroup label="Engine đề xuất">
            {decision.options.map((o) => (
              <option key={o.sequence_id} value={o.sequence_id}>
                {o.strategy_name_vi ?? 'Phương án'} · {chainText(o)}
              </option>
            ))}
          </optgroup>
          <option value="custom">Tự chọn chuỗi…</option>
        </select>
      </label>

      {building && !locked && (
        <form
          className="chain-pick__build"
          onSubmit={(e) => {
            e.preventDefault()
            onChange({ kind: 'custom', crops: draft })
          }}
        >
          {draft.map((c, i) => (
            <label key={i}>
              <span>{names[i] ?? `Vụ ${i + 1}`}</span>
              <select
                value={c}
                aria-label={`Cây vụ ${names[i] ?? i + 1}`}
                disabled={busy}
                onChange={(e) => {
                  const next = [...draft]
                  next[i] = e.target.value as CropId
                  setDraft(next)
                }}
              >
                {CROPS.map((id) => (
                  <option key={id} value={id}>
                    {CROP_SHORT[id]}
                  </option>
                ))}
              </select>
            </label>
          ))}
          <button type="submit" className="btn btn--primary btn--sm" disabled={busy}>
            {busy ? 'Đang mô phỏng…' : 'Mô phỏng'}
          </button>
        </form>
      )}
    </div>
  )
}
