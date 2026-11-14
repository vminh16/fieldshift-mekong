import { api, type DecisionPackage } from '../api/client'

const planCache = new Map<string, Promise<DecisionPackage>>()

/**
 * The parcel's latest engine PLAN, created once if none exists. Shared by the recommendation and the
 * simulation so both screens always show the same decision (AC-09). One request per field.
 */
export function latestPlan(fieldId: string): Promise<DecisionPackage> {
  if (!planCache.has(fieldId)) {
    const p = (async () => {
      const plans = await api.listFieldPlans(fieldId)
      const last = [...plans].reverse().find((x) => x.kind === 'PLAN')
      return last ? api.getPlan(last.decision_id) : api.createPlan(fieldId)
    })()
    p.catch(() => planCache.delete(fieldId))
    planCache.set(fieldId, p)
  }
  return planCache.get(fieldId)!
}
