/**
 * Data for the field simulation (Digital Twin, SOLUTION_DESIGN §11).
 * The twin only READS engine trajectories: every number on screen comes from GET /plans/{id}/twin.
 *
 * - Engine chains (current practice, engine options) are sliced from the field's latest plan.
 * - A user-chosen chain is run by POST /plans/{id}/evaluate → WHAT_IF child; its `baseline` is the chain.
 * - If the API is unreachable, a captured engine run (contracts/fixtures) keeps the screen usable,
 *   with chain choice locked because nothing new can be simulated offline.
 */
import { api, ApiError, type CropId, type DecisionPackage, type Twin } from '../api/client'
import type { LocalField } from '../fields/store'

export type ChainSpec =
  | { kind: 'engine'; sequenceId: string }
  | { kind: 'custom'; crops: CropId[] }

export interface TwinSource {
  mode: 'engine' | 'mock'
  decision: DecisionPackage
  /** Loads one side. `member` null = the engine's default (median year). */
  load: (spec: ChainSpec, scenarioId: string, member: number | null) => Promise<{ twin: Twin; chain: DecisionPackage['baseline'] }>
}

const childCache = new Map<string, Promise<DecisionPackage>>()

const planCache = new Map<string, Promise<DecisionPackage>>()

/** Latest PLAN for the field, creating one if none exists. One request per field even if asked twice. */
function latestPlan(fieldId: string): Promise<DecisionPackage> {
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

function engineSource(decision: DecisionPackage): TwinSource {
  const chains = [decision.baseline, ...decision.options]
  return {
    mode: 'engine',
    decision,
    async load(spec, scenarioId, member) {
      if (spec.kind === 'engine') {
        const chain = chains.find((c) => c.sequence_id === spec.sequenceId) ?? decision.baseline
        return { twin: await api.twin(decision.decision_id, chain.sequence_id, scenarioId, member), chain }
      }
      const key = `${decision.decision_id}:${spec.crops.join('-')}`
      if (!childCache.has(key)) {
        const p = api.evaluateChain(decision.decision_id, spec.crops)
        p.catch(() => childCache.delete(key))
        childCache.set(key, p)
      }
      const child = await childCache.get(key)!
      return { twin: await api.twin(child.decision_id, child.baseline.sequence_id, scenarioId, member), chain: child.baseline }
    },
  }
}

async function mockSource(): Promise<TwinSource> {
  const [plan, compare] = await Promise.all([
    import('../../../../contracts/fixtures/plan_cantho.json'),
    import('../../../../contracts/fixtures/twin_compare_cantho.json'),
  ])
  const decision = (plan.default ?? plan) as unknown as DecisionPackage
  const pair = (compare.default ?? compare) as unknown as { baseline: Twin; option: Twin }
  const chains = [decision.baseline, ...decision.options]
  return {
    mode: 'mock',
    decision,
    async load(spec) {
      const twin = spec.kind === 'engine' && spec.sequenceId === pair.option.sequence_id ? pair.option : pair.baseline
      return { twin, chain: chains.find((c) => c.sequence_id === twin.sequence_id) ?? decision.baseline }
    },
  }
}

/** Engine when the parcel is on the server and the API answers; otherwise the captured mock. */
export async function openTwin(field: LocalField): Promise<{ source: TwinSource; notice: string | null }> {
  if (field.pending) return { source: await mockSource(), notice: 'Thửa chưa đồng bộ lên máy chủ — đang hiện dữ liệu mẫu.' }
  try {
    return { source: engineSource(await latestPlan(field.id)), notice: null }
  } catch (e) {
    const why =
      e instanceof ApiError && e.unreachable
        ? 'Chưa kết nối được engine — đang hiện dữ liệu mẫu (Cần Thơ).'
        : e instanceof ApiError && e.code === 'NASA_POWER_UNAVAILABLE'
          ? 'Engine chưa lấy được dữ liệu NASA cho thửa này — đang hiện dữ liệu mẫu.'
          : `Engine báo lỗi (${e instanceof Error ? e.message : 'không rõ'}) — đang hiện dữ liệu mẫu.`
    return { source: await mockSource(), notice: why }
  }
}
