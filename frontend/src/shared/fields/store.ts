import { useSyncExternalStore } from 'react'
import { api, ApiError, type Field, type FieldProfile, type FieldWrite } from '../api/client'

/**
 * The user's parcels. The API (GET/POST/PATCH/DELETE /v1/fields) is the source of truth;
 * localStorage only caches the last list so the map opens instantly and survives a dead connection.
 * A parcel created while the API is unreachable is kept locally (`pending`) and pushed on the next sync.
 */
export type FieldStatus = 'draft' | 'planned' | 'replan_required'
export type SyncState = 'loading' | 'online' | 'offline'

export interface LocalField {
  /** API id (`fld_…`), or `local_…` while not yet on the server. */
  id: string
  name: string
  /** [lng, lat] ring, not closed. null when only a point is known. */
  ring: [number, number][] | null
  centroid: { lat: number; lng: number }
  area_ha: number | null
  area_source: 'drawn' | 'reported' | 'sample' | null
  place_name: string
  status: FieldStatus
  /** Seeded demo parcel with cached NASA data (no outline, placeholder area). */
  sample: boolean
  pending: boolean
  profile: FieldProfile | null
  created_at: string
  updated_at: string
}

export type FieldInput = Pick<LocalField, 'name' | 'ring' | 'centroid' | 'area_ha' | 'area_source' | 'place_name'> & { id?: string }

const KEY = 'fieldshift.fields.v2'
const LEGACY_KEY = 'fieldshift.fields.v1'
const ACTIVE_KEY = 'fieldshift.activeField.v1'

function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}
function save(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* storage blocked: memory only */
  }
}

// Parcels drawn before the API was wired in become pending creates.
function initial(): LocalField[] {
  const cached = load<LocalField[] | null>(KEY, null)
  if (cached) return cached
  const legacy = load<Partial<LocalField>[]>(LEGACY_KEY, [])
  return legacy.map((f) => ({
    ...(f as LocalField),
    id: `local_${f.id}`,
    sample: false,
    pending: true,
    profile: null,
    status: 'draft',
  }))
}

let fields: LocalField[] = initial()
let activeId: string | null = load(ACTIVE_KEY, null)
let sync: SyncState = 'loading'
const listeners = new Set<() => void>()
const emit = () => listeners.forEach((l) => l())
const subscribe = (cb: () => void) => {
  listeners.add(cb)
  return () => listeners.delete(cb)
}
function commit(next: LocalField[]) {
  fields = next
  save(KEY, fields)
  emit()
}

// ---------- mapping to/from the API ----------
interface ParcelProps {
  place_name?: string
  area_source?: LocalField['area_source']
}

function toWrite(input: FieldInput): FieldWrite {
  const props: ParcelProps = { place_name: input.place_name, area_source: input.area_source }
  return {
    name: input.name,
    lat: input.centroid.lat,
    lon: input.centroid.lng,
    area_ha: input.area_ha,
    // The API stores geometry as-is; we keep a GeoJSON Feature so the outline and its labels travel together.
    geometry: {
      type: 'Feature',
      geometry: input.ring ? { type: 'Polygon', coordinates: [[...input.ring, input.ring[0]]] } : { type: 'Point', coordinates: [input.centroid.lng, input.centroid.lat] },
      properties: props,
    },
  }
}

function fromApi(f: Field, prev?: LocalField): LocalField {
  const g = f.geometry as GeoJSON.Feature | null
  const props = (g?.properties ?? {}) as ParcelProps
  const ring = g?.geometry?.type === 'Polygon' ? (g.geometry.coordinates[0].slice(0, -1) as [number, number][]) : null
  const sample = g === null && Boolean(f.profile?.cache_key)
  return {
    id: f.id,
    name: f.name,
    ring,
    centroid: { lat: f.lat, lng: f.lon },
    area_ha: f.area_ha,
    area_source: sample ? 'sample' : (props.area_source ?? (f.area_ha !== null ? 'reported' : null)),
    place_name: props.place_name ?? prev?.place_name ?? '',
    status: prev?.status ?? 'draft',
    sample,
    pending: false,
    profile: f.profile,
    created_at: f.created_at,
    updated_at: f.updated_at,
  }
}

// ---------- hooks ----------
export function useFields(): LocalField[] {
  return useSyncExternalStore(subscribe, () => fields)
}

export function useSync(): SyncState {
  return useSyncExternalStore(subscribe, () => sync)
}

export function useActiveFieldId(): string | null {
  const list = useFields()
  const id = useSyncExternalStore(subscribe, () => activeId)
  return list.some((f) => f.id === id) ? id : (list[0]?.id ?? null)
}

export function getField(id: string | null): LocalField | undefined {
  return id ? fields.find((f) => f.id === id) : undefined
}

export function setActiveField(id: string) {
  activeId = id
  save(ACTIVE_KEY, id)
  emit()
}

// ---------- sync ----------
let inflight: Promise<void> | null = null

/** Pull the server list, then push parcels that were created offline. Safe to call repeatedly. */
export function syncFields(): Promise<void> {
  inflight ??= (async () => {
    try {
      const server = await api.listFields()
      const prev = new Map(fields.map((f) => [f.id, f]))
      const pending = fields.filter((f) => f.pending)
      let next = [...server.map((f) => fromApi(f, prev.get(f.id))), ...pending]
      for (const p of pending) {
        const created = fromApi(await api.createField(toWrite(p)), p)
        next = next.map((f) => (f.id === p.id ? created : f))
        if (activeId === p.id) setActiveField(created.id)
      }
      sync = 'online'
      commit(next)
    } catch (e) {
      sync = e instanceof ApiError && e.unreachable ? 'offline' : 'online'
      emit()
      if (!(e instanceof ApiError && e.unreachable)) console.error('Field sync failed', e)
    } finally {
      inflight = null
    }
  })()
  return inflight
}

/** Create or update a parcel. Resolves with the saved parcel; `offline` is true if it was only kept on this device. */
export async function saveField(input: FieldInput): Promise<{ field: LocalField; offline: boolean }> {
  const existing = getField(input.id ?? null)
  const now = new Date().toISOString()
  try {
    if (existing && !existing.pending) {
      const moved = existing.centroid.lat !== input.centroid.lat || existing.centroid.lng !== input.centroid.lng
      const w = toWrite(input)
      const field = fromApi(
        await api.patchField(existing.id, { name: w.name, area_ha: w.area_ha ?? undefined, geometry: w.geometry, ...(moved ? { lat: w.lat, lon: w.lon } : {}) }),
        existing,
      )
      commit(fields.map((f) => (f.id === field.id ? field : f)))
      setActiveField(field.id)
      return { field, offline: false }
    }
    const field = fromApi(await api.createField(toWrite(input)), existing)
    commit(existing ? fields.map((f) => (f.id === existing.id ? field : f)) : [...fields, field])
    sync = 'online'
    setActiveField(field.id)
    return { field, offline: false }
  } catch (e) {
    if (!(e instanceof ApiError && e.unreachable)) throw e
    if (existing && !existing.pending) throw new ApiError(0, 'UNREACHABLE', 'Cần kết nối máy chủ để sửa thửa đã đồng bộ. Thử lại khi có mạng.')
    sync = 'offline'
    const field: LocalField = {
      ...input,
      id: existing?.id ?? `local_${crypto.randomUUID()}`,
      status: 'draft',
      sample: false,
      pending: true,
      profile: null,
      created_at: existing?.created_at ?? now,
      updated_at: now,
    }
    commit(existing ? fields.map((f) => (f.id === field.id ? field : f)) : [...fields, field])
    setActiveField(field.id)
    return { field, offline: true }
  }
}

/** Only the place label changes (filled in by the geocoder after saving). */
export async function renamePlace(id: string, place_name: string) {
  const f = getField(id)
  if (!f || f.place_name === place_name) return
  await saveField({ ...f, place_name }).catch(() => undefined)
}

export async function removeField(id: string): Promise<void> {
  const f = getField(id)
  if (!f) return
  if (!f.pending) await api.deleteField(id)
  commit(fields.filter((x) => x.id !== id))
  if (activeId === id) {
    activeId = fields[0]?.id ?? null
    save(ACTIVE_KEY, activeId)
    emit()
  }
}

export const FIELD_STATUS_LABEL: Record<FieldStatus, string> = {
  draft: 'Chưa khai báo điều kiện',
  planned: 'Đã có kế hoạch',
  replan_required: 'Cần tính lại',
}

// First load, and again whenever the browser comes back online.
syncFields()
window.addEventListener('online', () => void syncFields())
