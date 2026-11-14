import type { DecisionPackage, EnsoPhase, YearOutlook } from '../../../../contracts/types'

export type { EnsoPhase, YearOutlook }

export const PHASE_VI: Record<EnsoPhase, string> = {
  EL_NINO_STRONG: 'El Niño mạnh',
  EL_NINO: 'El Niño',
  NEUTRAL: 'Trung tính',
  LA_NINA: 'La Niña',
  LA_NINA_STRONG: 'La Niña mạnh',
}

/** The package's outlook when usable; null hides every outlook UI (absent or status !== 'OK'). */
export function yearOutlookOf(d: DecisionPackage | undefined | null): YearOutlook | null {
  if (!d) return null
  const yo = d.year_outlook as YearOutlook | undefined // older snapshots lack it
  // Dev-only layout check: add `mau_enso=1` to the hash query. Dropped from production builds.
  if (import.meta.env.DEV && !yo && window.location.hash.includes('mau_enso=1')) return DEV_SAMPLE
  return yo && yo.status === 'OK' ? yo : null
}

/** Hand-made sample for layout only (dev server). Not data: numbers are illustrative. */
const DEV_SAMPLE: YearOutlook = {
  status: 'OK',
  enso: { index: 'ONI', centered_month: '2026-09', value: 1.6, phase: 'EL_NINO_STRONG', source: 'NOAA PSL ONI (ERSSTv5)' },
  analog_years: [2015, 2023, 2009],
  analog_labels_vi: ['2015–16', '2023–24', '2009–10'],
  dry_season_rain: { analog_median_mm: 120, all_years_median_mm: 260, ratio: 0.46, sources: ['NASA GPM IMERG V07 Final monthly', 'NASA POWER PRECTOTCORR'] },
  skill: { correlation_r: -0.5, n_years: 24, note_vi: '[MẪU GIAO DIỆN] Tín hiệu thống kê, không phải dự báo; có năm El Niño vẫn mưa nhiều.' },
  headline_vi: '[MẪU GIAO DIỆN] Mùa khô tới có thể giống 2015–16: mưa ít hơn bình thường.',
  scenario_id: 'sc_enso_analog',
  evidence_ids: [],
}
