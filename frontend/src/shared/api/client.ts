/**
 * Thin fetch wrapper for the FieldShift API (contracts/API_CONTRACT.md).
 * Types come straight from contracts/types.ts so the frontend cannot drift from the backend contract.
 */
import type { CropId, DecisionPackage, Field, FieldProfile, Observation, PlanRequest, ScenarioOverride, Trigger, Twin } from '../../../../contracts/types'

import type { SourceInventory } from './auditTypes'

export type { CropId, DecisionPackage, Field, FieldProfile, Observation, ScenarioOverride, Twin }

export interface ObservationWrite {
  variable: 'canal_ecw' | 'drainage' | 'season_closed'
  value?: number
  value_text?: string
  unit?: string
  observed_at: string
  evidence_kind: 'OBSERVED_FIELD' | 'REPORTED_BY_FARMER'
  note?: string
}
export type FiredTrigger = Trigger & { sequence_id: string; observation_id: string; observed_at: string; value: number | string }
export interface PlanStatus { decision_id: string; status: 'OK' | 'REPLAN_REQUIRED'; fired: FiredTrigger[] }
export interface CatalogCrop { id: CropId; name_vi: string; allowed_windows: string[] }

export const API_BASE: string = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
  ) {
    super(message)
  }
  /** True when the server could not be reached at all (offline, API not started, CORS). */
  get unreachable() {
    return this.status === 0
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}/v1${path}`, {
      ...init,
      headers: { Accept: 'application/json', ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...init?.headers },
    })
  } catch {
    throw new ApiError(0, 'UNREACHABLE', 'Không kết nối được máy chủ FieldShift.')
  }
  if (res.status === 204) return undefined as T
  const body = await res.json().catch(() => null)
  if (!res.ok) {
    const d = body?.detail
    const code = typeof d === 'object' && d && 'code' in d ? String(d.code) : `HTTP_${res.status}`
    const msg = typeof d === 'object' && d && 'message' in d ? String(d.message) : Array.isArray(d) ? 'Dữ liệu gửi lên không hợp lệ.' : `Lỗi máy chủ (${res.status}).`
    throw new ApiError(res.status, code, msg)
  }
  return body as T
}

export interface FieldWrite {
  name: string
  lat: number
  lon: number
  area_ha: number | null
  geometry: GeoJSON.Feature | null
}

export const api = {
  listFields: () => request<Field[]>('/fields'),
  createField: (body: FieldWrite) => request<Field>('/fields', { method: 'POST', body: JSON.stringify(body) }),
  patchField: (id: string, body: Partial<FieldWrite> & { profile?: Partial<FieldProfile> }) =>
    request<Field>(`/fields/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteField: (id: string) => request<void>(`/fields/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  getField: (id: string) => request<Field>(`/fields/${encodeURIComponent(id)}`),
  addObservation: (fieldId: string, body: ObservationWrite) =>
    request<Observation>(`/fields/${encodeURIComponent(fieldId)}/observations`, { method: 'POST', body: JSON.stringify(body) }),
  sources: () => request<SourceInventory>('/sources'),
  crops: () => request<{ crops: CatalogCrop[] }>('/crops'),
  planStatus: (id: string) => request<PlanStatus>(`/plans/${encodeURIComponent(id)}/status`),
  exportUrl: (id: string) => `${API_BASE}/v1/plans/${encodeURIComponent(id)}/export`,

  listFieldPlans: (fieldId: string) =>
    request<{ decision_id: string; kind: 'PLAN' | 'WHAT_IF' | 'REPLAN'; parent_id: string | null; created_at: string }[]>(
      `/fields/${encodeURIComponent(fieldId)}/plans`,
    ),
  getPlan: (id: string) => request<DecisionPackage>(`/plans/${encodeURIComponent(id)}`),
  createPlan: (fieldId: string, settings: Partial<Omit<PlanRequest, 'field_id'>> = {}) => request<DecisionPackage>('/plans', { method: 'POST', body: JSON.stringify({ horizon_seasons: 3, ...settings, field_id: fieldId }) }),
  /** Simulate a user-chosen chain: returns a WHAT_IF child whose `baseline` is that chain. */
  evaluateChain: (decisionId: string, crops: CropId[], opts: { sow_timing?: string[]; override?: ScenarioOverride } = {}) =>
    request<DecisionPackage>(`/plans/${encodeURIComponent(decisionId)}/evaluate`, { method: 'POST', body: JSON.stringify({ crops, ...opts }) }),
  twin: (decisionId: string, sequenceId: string, scenarioId: string, member: number | null) => {
    // aligned: one shared weekly calendar, so two chains (even from different decisions) line up week by week.
    const q = new URLSearchParams({ sequence_id: sequenceId, scenario_id: scenarioId, aligned: 'true' })
    if (member !== null) q.set('member', String(member))
    return request<Twin>(`/plans/${encodeURIComponent(decisionId)}/twin?${q}`)
  },
}
