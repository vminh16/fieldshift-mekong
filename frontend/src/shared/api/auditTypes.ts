import type { Option } from '../../../../contracts/types'

// TODO: switch these additive types to contracts/types.ts after the backend contract is merged.
export type SourceUse = 'DECISION' | 'EVIDENCE' | 'CONTEXT' | 'NOT_USED'
export interface DataSource {
  id: string
  name: string
  provider: string
  is_nasa: boolean
  use: SourceUse
  used_for_vi: string
  variables: string[]
  spatial_resolution: string
  time_range: string | null
  latency: string | null
  limitations_vi: string[]
  url: string | null
  in_challenge_list: boolean
}
export interface SourceInventory {
  sources: unknown[]
  generated_at?: string
  nasa_used_count?: number
  challenge_sources_used?: string[]
}
export type OptionWithExposure = Option & {
  salinity_exposure_days?: { typical: number; early_onset: number }
}
export interface SalinityWindow { start: string; end: string }

export function isDataSource(value: unknown): value is DataSource {
  if (!value || typeof value !== 'object') return false
  const s = value as Record<string, unknown>
  return ['id', 'name', 'provider', 'used_for_vi', 'spatial_resolution'].every((k) => typeof s[k] === 'string')
    && typeof s.is_nasa === 'boolean'
    && ['DECISION', 'EVIDENCE', 'CONTEXT', 'NOT_USED'].includes(String(s.use))
    && Array.isArray(s.limitations_vi) && s.limitations_vi.every((v) => typeof v === 'string')
}
