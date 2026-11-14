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

/** Run a fresh PLAN (after the field profile or observations changed); later reads get this one. */
export function refreshPlan(fieldId: string): Promise<DecisionPackage> {
  const p = api.createPlan(fieldId)
  p.catch(() => planCache.delete(fieldId))
  planCache.set(fieldId, p)
  return p
}

/* ---------- the farmer's local choice (the API has no "accept plan" endpoint yet) ---------- */
const CHOICE_KEY = 'fieldshift.choice.v1'
export function readChoice(fieldId: string): string | null {
  try {
    return (JSON.parse(localStorage.getItem(CHOICE_KEY) ?? '{}') as Record<string, string>)[fieldId] ?? null
  } catch {
    return null
  }
}
export function writeChoice(fieldId: string, seq: string | null) {
  try {
    const all = JSON.parse(localStorage.getItem(CHOICE_KEY) ?? '{}') as Record<string, string>
    if (seq) all[fieldId] = seq
    else delete all[fieldId]
    localStorage.setItem(CHOICE_KEY, JSON.stringify(all))
  } catch {
    /* storage blocked */
  }
}
