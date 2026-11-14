/**
 * Thin fetch wrapper for the FieldShift API (contracts/API_CONTRACT.md).
 * Types come straight from contracts/types.ts so the frontend cannot drift from the backend contract.
 */
import type { CropId, DecisionPackage, Field, FieldProfile, Twin } from '../../../../contracts/types'

export type { CropId, DecisionPackage, Field, FieldProfile, Twin }

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

  listFieldPlans: (fieldId: string) =>
    request<{ decision_id: string; kind: 'PLAN' | 'WHAT_IF' | 'REPLAN'; parent_id: string | null; created_at: string }[]>(
      `/fields/${encodeURIComponent(fieldId)}/plans`,
    ),
  getPlan: (id: string) => request<DecisionPackage>(`/plans/${encodeURIComponent(id)}`),
  createPlan: (fieldId: string) => request<DecisionPackage>('/plans', { method: 'POST', body: JSON.stringify({ field_id: fieldId, horizon_seasons: 3 }) }),
  /** Simulate a user-chosen chain: returns a WHAT_IF child whose `baseline` is that chain. */
  evaluateChain: (decisionId: string, crops: CropId[]) =>
    request<DecisionPackage>(`/plans/${encodeURIComponent(decisionId)}/evaluate`, { method: 'POST', body: JSON.stringify({ crops }) }),
  twin: (decisionId: string, sequenceId: string, scenarioId: string, member: number | null) => {
    const q = new URLSearchParams({ sequence_id: sequenceId, scenario_id: scenarioId })
    if (member !== null) q.set('member', String(member))
    return request<Twin>(`/plans/${encodeURIComponent(decisionId)}/twin?${q}`)
  },
}
