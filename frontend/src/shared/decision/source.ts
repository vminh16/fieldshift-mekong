/**
 * Where the rotation recommendation comes from: the parcel's latest engine PLAN (shared with the
 * simulation). The captured engine runs in contracts/fixtures are only a fallback when the engine
 * cannot answer, and are labelled as sample data on screen.
 */
import type { DecisionPackage, Option } from '../../../../contracts/types'
import type { LocalField } from '../fields/store'
import { ApiError } from '../api/client'
import { latestPlan } from './plans'

export type { DecisionPackage, Option }

export interface DecisionResult {
  decision: DecisionPackage
  source: 'mock' | 'engine'
  /** Why the mock is shown, when it is. */
  notice?: string
}

const FIXTURES = {
  cantho: { lat: 10.03, lng: 105.78, load: () => import('../../../../contracts/fixtures/plan_cantho.json') },
  soctrang: { lat: 9.55, lng: 106.2, load: () => import('../../../../contracts/fixtures/plan_soctrang.json') },
}

async function mock(field: LocalField, notice: string): Promise<DecisionResult> {
  // Coastal parcels (salinity season matters) get the Sóc Trăng run, inland ones the Cần Thơ run.
  const coastal = Boolean(field.profile?.coastal_salinity_risk) || field.centroid.lng > 105.9
  const pick = field.id === 'fld_cantho' ? FIXTURES.cantho : field.id === 'fld_soctrang' || coastal ? FIXTURES.soctrang : FIXTURES.cantho
  const mod = await pick.load()
  return { decision: (mod.default ?? mod) as unknown as DecisionPackage, source: 'mock', notice }
}

/** The engine's latest plan for the parcel; the captured fixtures only when the engine cannot answer. */
export async function loadDecision(field: LocalField): Promise<DecisionResult> {
  if (field.pending) return mock(field, 'Thửa chưa đồng bộ lên máy chủ — đang hiện dữ liệu mẫu.')
  try {
    return { decision: await latestPlan(field.id), source: 'engine' }
  } catch (e) {
    const offline = e instanceof ApiError && e.unreachable
    return mock(field, offline ? 'Chưa kết nối được engine — đang hiện dữ liệu mẫu.' : `Engine báo lỗi (${e instanceof Error ? e.message : 'không rõ'}) — đang hiện dữ liệu mẫu.`)
  }
}

/** Short crop names for tight labels; the API's crop_name_vi can be long ("Bỏ hóa / cây phủ đất"). */
export const CROP_SHORT: Record<string, string> = {
  rice: 'Lúa',
  maize: 'Ngô',
  soybean: 'Đậu nành',
  mungbean: 'Đậu xanh',
  sesame: 'Mè',
  peanut: 'Đậu phộng',
  watermelon: 'Dưa hấu',
  fallow_cover: 'Cây phủ đất',
}

/** Crop family → colour slot. Validated (dataviz validator, dark surface #121513): CVD ΔE ≥ 8.4, normal ≥ 19.8. */
export function cropTone(crop: string): 'rice' | 'legume' | 'cover' | 'other' {
  if (crop === 'rice') return 'rice'
  if (crop === 'mungbean' || crop === 'soybean' || crop === 'peanut') return 'legume'
  if (crop === 'fallow_cover') return 'cover'
  return 'other'
}

/** Soil indicator codes from the engine → plain words. Qualitative potential, never a score. */
export const SOIL_INDICATOR: Record<string, string> = {
  breaks_rice_pest_cycle: 'Cắt vòng sâu bệnh của lúa',
  legume_n_fixation_potential: 'Cây họ đậu có thể bổ sung đạm',
  residue_return: 'Trả tàn dư về đất',
  crop_diversity_2: '2 loại cây trong năm',
  root_diversity: 'Rễ cây khác nhau, đất tơi hơn',
  ground_cover: 'Che phủ đất mùa khô',
}
