// FieldShift-Mekong API v1 — TypeScript types (hand-written from contracts/fixtures; see API_CONTRACT.md).
// Backend changes are additive only: keep `[key: string]: unknown` tolerance where noted.

export type Label = 'Đo tại ruộng' | 'Ước lượng vùng' | 'Dự kiến' | 'Kịch bản' | 'Giả định mặc định' | 'Chưa biết' | string
export type Origin =
  | 'measured_at_field' | 'reported_by_farmer' | 'estimated_from_regional_data'
  | 'inferred_by_model' | 'assumed_scenario' | 'assumed_default' | 'unknown' | string

export interface Measure<T = number> {
  value: T | null
  unit?: string
  origin: Origin
  label: Label
  evidence_ids?: string[]
  reason?: string // present when value === null
  [key: string]: unknown
}

export type CropId = 'rice' | 'maize' | 'soybean' | 'mungbean' | 'sesame' | 'peanut' | 'watermelon' | 'fallow_cover'
export type Priority = 'save_water' | 'avoid_crop_failure' | 'soil_health' | 'supplemental_income' | 'minimal_change'
export type DecisionStatus =
  | 'RECOMMEND_FOR_CONSIDERATION' | 'CONDITIONAL_PENDING_CHECK' | 'NOT_FEASIBLE' | 'INSUFFICIENT_EVIDENCE'
export type ScenarioKind = 'CLIMATOLOGY' | 'STRESS_TEST' | 'FORECAST' | 'CLIMATE_PROJECTION' | string
export type Severity = 'HARD' | 'SOFT' | 'UNKNOWN_REQUIRES_CHECK'

export interface FieldProfile {
  /** null = chưa khai báo → engine dùng baseline GIẢ ĐỊNH (gate G2 fail) */
  baseline?: CropId[] | null
  /** null = chưa khai báo → state.irrigation.origin = 'assumed_default' (tính như 'full') */
  irrigation?: 'full' | 'canal_limited' | 'rainfed' | null
  drainage?: 'good' | 'poor' | 'unknown' | null
  coastal_salinity_risk: boolean
  equipment: string[]
  history: unknown[]
  cache_key?: string | null
}
export interface Field {
  id: string; name: string; region_id: string; lat: number; lon: number
  geometry: unknown | null; area_ha: number | null; profile: FieldProfile
  created_at: string; updated_at: string; observations?: Observation[]
}
export interface Observation {
  id: string; field_id: string; variable: 'canal_ecw' | 'soil_ph' | 'drainage' | 'rain_mm' | 'season_closed' | string
  value: number | null; value_text?: string | null; unit?: string | null; observed_at: string
  evidence_kind: 'OBSERVED_FIELD' | 'REPORTED_BY_FARMER'; note?: string | null
}

export interface PlanRequest {
  field_id: string
  as_of?: string
  horizon_seasons?: 1 | 2 | 3
  baseline?: CropId[] | null
  priorities?: Priority[]
  constraints?: {
    no_new_machinery?: boolean; budget_level?: 'low' | 'medium' | 'high' | null
    irrigation?: FieldProfile['irrigation'] | null; irrigation_cap_mm?: number | null
    max_changed_seasons?: number; max_fallow_seasons?: number
  }
}
// Matches apps/api ScenarioOverride (openapi.json). Negative salinity shift = salinity arrives earlier.
export interface ScenarioOverride {
  rain_delta_pct?: number | null; temp_delta_c?: number | null; salinity_onset_shift_weeks?: number | null
  /** {"2": -10} = season 2 sown 10 days earlier */
  sow_shift_days?: Record<string, number>; irrigation_cap_mm?: number | null
}

export interface Gate { gate: string; passed: boolean; message: string }
export interface Scenario {
  scenario_id: string; kind: ScenarioKind; name: string
  probability: null; probability_semantics: string; assumptions: string[]
  quality_flags?: string[]; issue_time?: string; source?: string
  [key: string]: unknown
}
export interface Season {
  index: number; window: string; window_name_vi: string; crop: CropId; crop_name_vi: string
  sow_timing: string; sow: string; harvest: string
}
export interface ScenarioMetrics {
  irrigation_need: Measure; irrigation_need_bad_year: Measure; water_stress_days: Measure
  heat_stress_days_sensitive_stage: Measure; yield: Measure; profit: Measure
  [key: string]: Measure
}
export interface DistributionPoint {
  member: number; year: number | null; member_label?: string
  irrigation_mm: number; water_stress_days: number; heat_stress_days: number
}
export interface Rule {
  rule_id: string; severity: Severity; season_index: number | null; reason: string
  how_to_resolve?: string; inputs_used?: string[]; evidence?: string[]
}
export interface Trigger {
  condition: string; variable: string; op: 'gt' | 'lt' | 'eq' | string; threshold: number | string
  unit: string | null; season_index: number; measure: string; action: string
}
export interface Option {
  sequence_id: string; is_baseline: boolean
  strategy_tag:
    | 'save_water' | 'low_risk' | 'soil_support' | 'balanced'
    | 'third_season_rest' | 'salinity_avoidance' | null
  strategy_name_vi: string | null; summary_vi?: string
  decision_status: DecisionStatus
  seasons: Season[]
  metrics: Record<string, ScenarioMetrics>
  delta_vs_baseline: Record<string, Record<string, { value: number | null; unit: string }>>
  distribution?: Record<string, DistributionPoint[]>
  /** Σ season_value_weight × crop value_index; team heuristic [B], not yield/profit */
  production_value_index: number
  /** Calendar overlap counts for every option; no salinity measurement implied. */
  salinity_exposure_days: { option: number; baseline: number }
  /** salinity_avoidance only: overlap days removed vs the standard-sow baseline */
  salinity_overlap_avoided_days?: { typical: number; early_onset: number }
  soil_benefit: { claim_type: 'POTENTIAL_QUALITATIVE'; value: null; indicators: string[] }
  rules: Rule[]
  reasons: { text: string; evidence_ids?: string[]; claim_type?: 'POTENTIAL_QUALITATIVE' }[]
  risks: { code: string; severity: Severity; season_index: number | null; text: string }[]
  triggers: Trigger[]
  checklist: string[]
}
export interface Evidence {
  kind: string; source: string; spatial_scale?: string; resolution?: string
  time_scope?: [string, string] | null; status?: string; limitations?: string[]; quality_flags?: string[]
  [key: string]: unknown
}
export type EnsoPhase = 'EL_NINO_STRONG' | 'EL_NINO' | 'NEUTRAL' | 'LA_NINA' | 'LA_NINA_STRONG'
/** ENSO-conditioned analog years (association, never a rainfall/salinity forecast). */
export interface YearOutlook {
  status: 'OK' | 'UNAVAILABLE'            // UNAVAILABLE -> hide banner; engine behaves as before
  reason?: string | null                  // 'ONI_NOT_AVAILABLE_AT_AS_OF' | 'TOO_FEW_ANALOG_YEARS'
  enso: {
    index: 'ONI'
    centered_month: string                // 'YYYY-MM', latest 3-month window ended before as_of's month
    value: number
    phase: EnsoPhase
    source: string
  } | null
  analog_years: number[]                  // dry-season START years (2015 = 2015–16)
  analog_labels_vi: string[]
  dry_season_rain: {                      // Dec–Apr totals at this field's site, mm
    analog_median_mm: number | null
    all_years_median_mm: number | null
    ratio: number | null
    sources: string[]
  }
  skill: { correlation_r: number | null; n_years: number; note_vi: string }
  headline_vi: string
  scenario_id: string | null              // 'sc_enso_analog' when present in scenarios[]
  evidence_ids: string[]
}
export interface DecisionPackage {
  decision_id: string; parent_id: string | null; kind: 'PLAN' | 'WHAT_IF' | 'REPLAN'
  field_id: string; as_of: string; generated_at: string; versions: Record<string, string>
  field_state: Record<string, unknown> & { canal_ecw: Measure; data_last_date: string }
  gates: Gate[]
  windows: { id: string; name_vi: string; sow_from: string; sow_to: string }[]
  scenarios: Scenario[]
  year_outlook: YearOutlook
  salinity_window: { start: string; end: string; typical_start: string; typical_end: string; adjusted: boolean; kind: string; evidence_ids: string[] }
  source_conflicts: { status: string; policy: string; note_vi?: string; evidence_ids: string[]; [key: string]: unknown }[]
  baseline: Option
  options: Option[]
  excluded: { sequence_id: string; crops: CropId[]; rule_id: string; severity: 'HARD'; reason: string }[]
  stats: Record<string, unknown>
  evidence: Record<string, Evidence>
  notes: string[]; disclaimer: string
  history: { crop: CropId; sow: string; harvest: string; note?: string }[]
  changed_since_parent?: Observation[]
  [key: string]: unknown
}
export interface PlanStatus { decision_id: string; status: 'OK' | 'REPLAN_REQUIRED'; fired: unknown[] }

// Digital Twin
export interface TwinWeek {
  date: string; season_index: number; crop: CropId; stage: string
  root_depth_m: Measure; root_zone_water: Measure; ponding_mm: Measure
  rain_week: Measure; irrigation_week: Measure; irrigation_cum: Measure
  salinity: Measure & { in_salinity_season: boolean }
  [key: string]: unknown
}
export interface TwinEvent {
  date: string; type: 'sow' | 'harvest' | 'salinity_season_start' | 'salinity_season_end'
  season_index: number | null; crop: CropId | null
}
export interface Twin {
  decision_id: string; sequence_id: string; scenario_id: string; member: number; analog_year: number | null
  members: { member: number; year: number | null; irrigation_mm: number; label_vi: string }[]
  step: 'week'; events: TwinEvent[]; series: TwinWeek[]
}
export interface TwinCompare { baseline: Twin; option: Twin }
export interface ApiError { detail: { code: string; message: string } | unknown }

export type SourceUse = 'DECISION' | 'EVIDENCE' | 'CONTEXT' | 'NOT_USED'
export interface DataSource {
  id: string; name: string; provider: string; is_nasa: boolean; use: SourceUse
  used_for_vi: string; variables: string[]; spatial_resolution: string
  time_range: string | null; latency: string | null; limitations_vi: string[]
  url: string | null; in_challenge_list: boolean
}
export interface SourcesResponse {
  sources: DataSource[]; generated_at: string; nasa_used_count: number; challenge_sources_used: string[]
}
