import { useEffect, useId, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { searchPlaces } from '../../shared/geo/geocode'
import { MEKONG_PROVINCES, SUGGESTED_IDS, searchGazetteer } from '../../shared/geo/mekongProvinces'
import type { Place } from '../../shared/geo/types'
import './location-search.css'

interface Props {
  onLocate: (place: Place) => void
}

type Status = 'idle' | 'loading' | 'not-found' | 'error'

export function LocationSearch({ onLocate }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Place[]>([])
  const [open, setOpen] = useState(false)
  const [activeIdx, setActiveIdx] = useState(-1)
  const [status, setStatus] = useState<Status>('idle')
  const abortRef = useRef<AbortController | null>(null)
  const pendingRef = useRef<Promise<Place[]> | null>(null)
  const listId = useId()
  const statusId = useId()

  const suggestions = SUGGESTED_IDS.map((id) => MEKONG_PROVINCES.find((p) => p.id === id)!)
  const showList = open && results.length > 0

  // Instant local matches, then worldwide results after a short pause in typing.
  useEffect(() => {
    const q = query.trim()
    abortRef.current?.abort()
    if (!q) {
      setResults([])
      setStatus('idle')
      return
    }
    setResults(searchGazetteer(q))
    const ctrl = new AbortController()
    abortRef.current = ctrl
    const timer = window.setTimeout(() => {
      setStatus('loading')
      const p = searchPlaces(q, ctrl.signal)
      pendingRef.current = p
      p.then((r) => {
        if (ctrl.signal.aborted) return
        setResults(r)
        setStatus(r.length ? 'idle' : 'not-found')
      }).catch((err) => {
        if (ctrl.signal.aborted) return
        console.error('Geocoder failed', err)
        setStatus('error')
      })
    }, 280)
    return () => {
      window.clearTimeout(timer)
      ctrl.abort()
    }
  }, [query])

  const choose = (place: Place) => {
    setQuery(place.name)
    setOpen(false)
    setActiveIdx(-1)
    setStatus('idle')
    onLocate(place)
  }

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    const q = query.trim()
    if (!q) return
    if (showList && activeIdx >= 0) return choose(results[activeIdx])
    if (results.length && status !== 'loading') return choose(results[0])
    setStatus('loading')
    try {
      const r = await searchPlaces(q)
      if (r.length) choose(r[0])
      else setStatus('not-found')
    } catch (err) {
      console.error('Geocoder failed', err)
      setStatus('error')
    }
  }

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!showList) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIdx((i) => (i + 1) % results.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIdx((i) => (i <= 0 ? results.length - 1 : i - 1))
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div className="search">
      <form className="search__bar" role="search" onSubmit={submit}>
        <label className="search__field">
          <span className="visually-hidden">Tìm tỉnh, thành phố hoặc địa chỉ</span>
          <svg className="search__icon" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" />
          </svg>
          <input
            type="text"
            value={query}
            placeholder="Nhập tỉnh, huyện, xã hoặc địa chỉ"
            autoComplete="off"
            spellCheck={false}
            role="combobox"
            aria-expanded={showList}
            aria-controls={listId}
            aria-autocomplete="list"
            aria-activedescendant={showList && activeIdx >= 0 ? `${listId}-${activeIdx}` : undefined}
            aria-describedby={statusId}
            onChange={(e) => {
              setQuery(e.target.value)
              setOpen(true)
              setActiveIdx(-1)
            }}
            onFocus={() => setOpen(true)}
            onBlur={() => window.setTimeout(() => setOpen(false), 120)}
            onKeyDown={onKeyDown}
          />
          {status === 'loading' && <span className="search__spinner" aria-hidden="true" />}
        </label>
        <button className="search__submit" type="submit">
          Định vị
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
        </button>

        {showList && (
          <ul className="search__list" id={listId} role="listbox">
            {results.map((p, i) => (
              <li
                key={p.id}
                id={`${listId}-${i}`}
                role="option"
                aria-selected={i === activeIdx}
                className={i === activeIdx ? 'is-active' : undefined}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => choose(p)}
              >
                <span className="search__opt-name">{p.name}</span>
                <span className="search__opt-meta">{p.context}</span>
              </li>
            ))}
          </ul>
        )}
      </form>

      <p className="search__status" id={statusId} role="status">
        {status === 'not-found' && `Chưa tìm thấy “${query.trim()}”. Thử tên khác hoặc thêm tỉnh/thành phố.`}
        {status === 'error' && 'Không kết nối được dịch vụ tìm địa điểm. Bạn vẫn có thể chọn tỉnh ĐBSCL bên dưới.'}
      </p>

      <div className="search__chips" aria-label="Gợi ý khu vực">
        <span className="search__chips-label">Gợi ý</span>
        {suggestions.map((p) => (
          <button key={p.id} type="button" className="chip" onClick={() => choose(p)}>
            {p.name}
          </button>
        ))}
      </div>
    </div>
  )
}
