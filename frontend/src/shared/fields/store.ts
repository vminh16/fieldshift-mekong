import { useSyncExternalStore } from 'react'

/**
 * Local-first list of the user's parcels.
 * The API's POST /v1/fields needs a full profile (baseline, irrigation, drainage…), which is
 * collected on the next screen; until then a parcel lives here and `api_id` stays null.
 * Browser storage can be unavailable (private mode) — the app then keeps parcels in memory.
 */
export type FieldStatus = 'draft' | 'planned' | 'replan_required'

export interface LocalField {
  id: string
  name: string
  /** [lng, lat] ring, not closed. null when the user only dropped a point. */
  ring: [number, number][] | null
  centroid: { lat: number; lng: number }
  /** Geodesic area of the drawn outline (estimate), or what the user typed for a point. */
  area_ha: number | null
  area_source: 'drawn' | 'reported' | null
  place_name: string
  status: FieldStatus
  api_id: string | null
  created_at: string
  updated_at: string
}

export type FieldInput = Pick<LocalField, 'name' | 'ring' | 'centroid' | 'area_ha' | 'area_source' | 'place_name'> & { id?: string }

const KEY = 'fieldshift.fields.v1'
const ACTIVE_KEY = 'fieldshift.activeField.v1'

function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}
function save(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* storage blocked: keep in memory only */
  }
}

let fields: LocalField[] = load(KEY, [])
let activeId: string | null = load(ACTIVE_KEY, null)
const listeners = new Set<() => void>()
const emit = () => listeners.forEach((l) => l())
const subscribe = (cb: () => void) => {
  listeners.add(cb)
  return () => listeners.delete(cb)
}

export function useFields(): LocalField[] {
  return useSyncExternalStore(subscribe, () => fields)
}

export function useActiveFieldId(): string | null {
  const list = useFields()
  const id = useSyncExternalStore(subscribe, () => activeId)
  return list.some((f) => f.id === id) ? id : (list[0]?.id ?? null)
}

export function getField(id: string | null): LocalField | undefined {
  return id ? fields.find((f) => f.id === id) : undefined
}

export function setActiveField(id: string) {
  activeId = id
  save(ACTIVE_KEY, id)
  emit()
}

export function upsertField(input: FieldInput): LocalField {
  const now = new Date().toISOString()
  const existing = getField(input.id ?? null)
  const field: LocalField = existing
    ? { ...existing, ...input, id: existing.id, updated_at: now }
    : { ...input, id: crypto.randomUUID(), status: 'draft', api_id: null, created_at: now, updated_at: now }
  fields = existing ? fields.map((f) => (f.id === field.id ? field : f)) : [...fields, field]
  save(KEY, fields)
  setActiveField(field.id)
  return field
}

export function removeField(id: string) {
  fields = fields.filter((f) => f.id !== id)
  save(KEY, fields)
  if (activeId === id) {
    activeId = fields[0]?.id ?? null
    save(ACTIVE_KEY, activeId)
  }
  emit()
}

export const FIELD_STATUS_LABEL: Record<FieldStatus, string> = {
  draft: 'Chưa khai báo điều kiện',
  planned: 'Đã có kế hoạch',
  replan_required: 'Cần tính lại',
}
