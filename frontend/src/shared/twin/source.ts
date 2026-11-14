/**
 * Data for the field simulation (Digital Twin, SOLUTION_DESIGN §11).
 * The twin only READS engine trajectories: every number on screen comes from GET /plans/{id}/twin.
 *
 * - Engine chains (current practice, engine options) are sliced from the field's latest plan.
 * - A user-chosen chain is run by POST /plans/{id}/evaluate → WHAT_IF child; its `baseline` is the chain.
 * - If the API is unreachable, a captured engine run (contracts/fixtures) keeps the screen usable,
 *   with chain choice locked because nothing new can be simulated offline.
 */
import { api, ApiError, type CropId, type DecisionPackage, type ScenarioOverride, type Twin } from '../api/client'
import type { LocalField } from '../fields/store'
import { latestPlan } from '../decision/plans'

export type ChainSpec =
  | { kind: 'engine'; sequenceId: string }
  | { kind: 'custom'; crops: CropId[] }

export interface TwinSource {
  mode: 'engine' | 'mock'
  decision: DecisionPackage
  /**
   * Loads one side. `member` null = the engine's default (median year).
   * With `override`, the chain is re-run under the user's assumptions and read from scenario `sc_whatif`.
   */
  load: (
    spec: ChainSpec,
    scenarioId: string,
    member: number | null,
    override?: ScenarioOverride | null,
  ) => Promise<{ twin: Twin; chain: DecisionPackage['baseline'] }>
}

const childCache = new Map<string, Promise<DecisionPackage>>()

function engineSource(decision: DecisionPackage): TwinSource {
  const chains = [decision.baseline, ...decision.options]
  return {
    mode: 'engine',
    decision,
    async load(spec, scenarioId, member, override) {
      const engineChain = spec.kind === 'engine' ? (chains.find((c) => c.sequence_id === spec.sequenceId) ?? decision.baseline) : null
      if (engineChain && !override) {
        return { twin: await api.twin(decision.decision_id, engineChain.sequence_id, scenarioId, member), chain: engineChain }
      }
      // Custom chain, or any chain under user assumptions: run it through /evaluate (a WHAT_IF child).
      const crops = engineChain ? engineChain.seasons.map((s) => s.crop) : (spec as { crops: CropId[] }).crops
      const sow_timing = engineChain?.seasons.map((s) => s.sow_timing)
      const key = `${decision.decision_id}:${crops.join('-')}:${sow_timing?.join('-') ?? ''}:${override ? JSON.stringify(override) : ''}`
      if (!childCache.has(key)) {
        const p = api.evaluateChain(decision.decision_id, crops, { sow_timing, ...(override ? { override } : {}) })
        p.catch(() => childCache.delete(key))
        childCache.set(key, p)
      }
      const child = await childCache.get(key)!
      const twin = await api.twin(child.decision_id, child.baseline.sequence_id, override ? 'sc_whatif' : scenarioId, member)
      // Keep the engine option's name; the child's baseline carries none.
      return { twin, chain: { ...child.baseline, strategy_name_vi: engineChain?.strategy_name_vi ?? null, strategy_tag: engineChain?.strategy_tag ?? null } }
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
