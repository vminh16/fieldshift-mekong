import type { Option } from '../../../../contracts/types'

export type { DataSource, SourceUse } from '../../../../contracts/types'
import type { DataSource } from '../../../../contracts/types'

export interface SourceInventory {
  sources: unknown[]
  generated_at?: string
  nasa_used_count?: number
  challenge_sources_used?: string[]
}
export type OptionWithExposure = Option & {
  salinity_exposure_days?: { option: number; baseline: number }
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
