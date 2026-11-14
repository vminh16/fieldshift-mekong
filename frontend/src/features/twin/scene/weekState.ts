import type { TwinWeek } from '../../../../../contracts/types'
import { cropTone } from '../../../shared/decision/source'
import type { FieldState } from './FieldScene'

/** Canopy development per FAO-56 stage — drawing only, never shown as a number. */
const GROWTH: Record<string, number> = { initial: 0.22, development: 0.58, mid: 1, late: 0.92 }
const lerp = (a: number, b: number, t: number) => a + (b - a) * t

function at(w: TwinWeek | undefined) {
  const crop = w?.crop ? cropTone(w.crop) : null
  return {
    crop,
    growth: crop && w?.stage ? (GROWTH[w.stage as string] ?? 0.5) : 0,
    ripe: w?.stage === 'late' ? 1 : 0,
    pondMm: w?.ponding_mm.value ?? 0,
    rootM: crop ? (w?.root_depth_m.value ?? 0) : 0,
    wet: w?.root_zone_water.value ?? 0,
    saltSeason: Boolean(w?.salinity?.in_salinity_season),
  }
}

/**
 * Scene state at a fractional week `pos`: engine values of the two surrounding weeks, blended.
 * Only the picture is blended; labels and indicators always show the engine's own week values.
 */
export function stateAt(series: TwinWeek[], pos: number): FieldState {
  const i = Math.max(0, Math.min(series.length - 1, Math.floor(pos)))
  const f = Math.min(1, Math.max(0, pos - i))
  const a = at(series[i])
  const b = at(series[i + 1] ?? series[i])
  if (a.crop !== b.crop) return f < 0.5 ? a : b
  return {
    crop: a.crop,
    growth: lerp(a.growth, b.growth, f),
    ripe: lerp(a.ripe, b.ripe, f),
    pondMm: lerp(a.pondMm, b.pondMm, f),
    rootM: lerp(a.rootM, b.rootM, f),
    wet: lerp(a.wet, b.wet, f),
    saltSeason: f < 0.5 ? a.saltSeason : b.saltSeason,
  }
}
