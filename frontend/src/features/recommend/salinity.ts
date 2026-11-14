import type { Season, Twin } from '../../../../contracts/types'
import type { OptionWithExposure, SalinityWindow } from '../../shared/api/auditTypes'
const DAY = 86_400_000

/** Exact boundaries supplied by the same API trajectory used by the simulation. */
export function salinityWindowOf(twin: Twin): SalinityWindow | null {
  const start = twin.events.find((e) => e.type === 'salinity_season_start')?.date
  const end = twin.events.find((e) => e.type === 'salinity_season_end' && (!start || e.date >= start))?.date
  return start && end ? { start, end } : null
}

/** Crop calendar overlap is exposure to a regional window, never observed salt concentration. */
export function exposureDays(option: OptionWithExposure, window: SalinityWindow | null): number | null {
  const reported = option.salinity_exposure_days?.option // engine's own count for this chain
  if (typeof reported === 'number' && Number.isFinite(reported)) return reported
  if (!window) return null
  const lo = Date.parse(window.start), hi = Date.parse(window.end)
  return option.seasons.filter((s) => s.crop !== 'fallow_cover').reduce((sum, s) =>
    sum + Math.max(0, Math.round((Math.min(Date.parse(s.harvest), hi) - Math.max(Date.parse(s.sow), lo)) / DAY) + 1), 0)
}

/** Only the days between harvest and next sow: no claim about whether soil is actually bare. */
export function calendarGaps(seasons: Season[]): SalinityWindow[] {
  const sorted = [...seasons].sort((a, b) => a.sow.localeCompare(b.sow))
  return sorted.slice(1).flatMap((s, i) => {
    const previous = sorted[i]
    const start = new Date(Date.parse(previous.harvest) + DAY).toISOString().slice(0, 10)
    const end = new Date(Date.parse(s.sow) - DAY).toISOString().slice(0, 10)
    return start <= end ? [{ start, end }] : []
  })
}
