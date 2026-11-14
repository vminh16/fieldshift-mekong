import { useState, type FormEvent } from 'react'
import type { DecisionPackage, PlanRequest, Priority } from '../../../../contracts/types'

export const PRIORITY_VI: Record<Priority, string> = {
  avoid_crop_failure: 'Tránh mất mùa', save_water: 'Tiết kiệm nước', soil_health: 'Cải thiện đất',
  supplemental_income: 'Thêm thu nhập', minimal_change: 'Ít thay đổi',
}
const DEFAULT_PRIORITIES: Priority[] = ['avoid_crop_failure', 'save_water', 'soil_health']
export function requestOf(d: DecisionPackage): Partial<PlanRequest> {
  return (d.request as Partial<PlanRequest> | undefined) ?? {}
}
export function PlanPreferences({ decision, busy, onApply }: {
  decision: DecisionPackage; busy: boolean; onApply: (settings: Partial<PlanRequest>) => void
}) {
  const request = requestOf(decision)
  const [priorities, setPriorities] = useState<Priority[]>(request.priorities ?? DEFAULT_PRIORITIES)
  const [maxChanged, setMaxChanged] = useState(request.constraints?.max_changed_seasons ?? 1)
  const [cap, setCap] = useState(request.constraints?.irrigation_cap_mm?.toString() ?? '')
  const move = (i: number, offset: number) => setPriorities((old) => {
    const next = [...old]
    ;[next[i], next[i + offset]] = [next[i + offset], next[i]]
    return next
  })
  const submit = (event: FormEvent) => {
    event.preventDefault()
    onApply({ ...request, priorities, constraints: { ...request.constraints, max_changed_seasons: maxChanged, irrigation_cap_mm: cap === '' ? null : Number(cap) } })
  }
  return <details className="plan-prefs">
    <summary>Ưu tiên & giới hạn của bạn</summary>
    <form onSubmit={submit}>
      <fieldset disabled={busy}>
        <legend>Ưu tiên theo thứ tự từ trên xuống</legend>
        <p className="plan-prefs__note">Chọn ít nhất một mục; dùng nút Lên / Xuống để đổi thứ tự. Engine sẽ tính lại theo lựa chọn này.</p>
        <ol className="plan-prefs__list">{priorities.map((p, i) => <li key={p}>
          <span>{PRIORITY_VI[p]}</span>
          <div><button type="button" aria-label={`Đưa ${PRIORITY_VI[p]} lên`} disabled={i === 0} onClick={() => move(i, -1)}>Lên</button>
            <button type="button" aria-label={`Đưa ${PRIORITY_VI[p]} xuống`} disabled={i === priorities.length - 1} onClick={() => move(i, 1)}>Xuống</button>
            <button type="button" aria-label={`Bỏ ưu tiên ${PRIORITY_VI[p]}`} disabled={priorities.length === 1} onClick={() => setPriorities((old) => old.filter((v) => v !== p))}>Bỏ</button></div>
        </li>)}</ol>
        <div className="plan-prefs__add">{(Object.keys(PRIORITY_VI) as Priority[]).filter((p) => !priorities.includes(p)).map((p) => <button key={p} type="button" onClick={() => setPriorities((old) => [...old, p])}>+ {PRIORITY_VI[p]}</button>)}</div>
        {priorities.includes('supplemental_income') && <p className="plan-prefs__note">“Thêm thu nhập” dùng ước lượng nhóm (heuristic), chưa phải mô hình lợi nhuận.</p>}
        <div className="plan-prefs__constraints">
          <label>Đổi tối đa bao nhiêu vụ?<select value={maxChanged} onChange={(e) => setMaxChanged(Number(e.target.value))}>{[0, 1, 2, 3].map((n) => <option value={n} key={n}>{n} vụ</option>)}</select></label>
          <label>Trần nước tưới mỗi vụ (mm)<input type="number" min="0" max="3000" step="any" inputMode="decimal" placeholder="Không đặt trần" value={cap} onChange={(e) => setCap(e.target.value)} /><small>Để trống nếu chưa biết; 1 mm = 10 m³/ha.</small></label>
        </div>
        <button className="btn btn--primary btn--sm" type="submit">{busy ? 'Đang tính lại…' : 'Áp dụng & tính lại'}</button>
      </fieldset>
    </form>
  </details>
}
