import type { Season } from '../../../../contracts/types'
import { CROP_SHORT, cropTone } from '../../shared/decision/source'
import { CROP_PHOTO } from '../../shared/decision/photos'
import { CropArt } from './CropArt'

const t = (iso: string) => new Date(iso).getTime()
const day = (iso: string) => {
  const d = new Date(iso)
  return `${d.getDate()}/${d.getMonth() + 1}`
}

/**
 * The proposed rotation on a real month axis, with the current chain underneath for comparison.
 * Proposed crops are photo tiles placed at their sow → harvest dates; gaps are land preparation.
 */
export function SeasonTimeline({ pick, base, today }: { pick: Season[]; base: Season[]; today: string }) {
  const all = [...pick, ...base]
  const start = new Date(Math.min(t(today), ...all.map((s) => t(s.sow))))
  start.setDate(1)
  const end = new Date(Math.max(...all.map((s) => t(s.harvest))))
  end.setMonth(end.getMonth() + 1, 1)
  const span = end.getTime() - start.getTime()
  const x = (ms: number) => ((ms - start.getTime()) / span) * 100

  const months: Date[] = []
  for (const m = new Date(start); m < end; m.setMonth(m.getMonth() + 1)) months.push(new Date(m))

  return (
    <div className="tl" role="img" aria-label={`Đề xuất: ${pick.map((s) => `${CROP_SHORT[s.crop] ?? s.crop} ${day(s.sow)}–${day(s.harvest)}`).join(', ')}`}>
      <div className="tl__scroll">
        <div className="tl__inner">
          <div className="tl__months" aria-hidden="true">
            {months.map((m, i) => (
              <span key={m.toISOString()} style={{ left: `${x(m.getTime())}%` }} data-year={m.getMonth() === 0 || i === 0 || undefined}>
                <b>T{m.getMonth() + 1}</b>
                {(m.getMonth() === 0 || i === 0) && <small>{m.getFullYear()}</small>}
              </span>
            ))}
            <span className="tl__today" style={{ left: `${x(t(today))}%` }}>
              Hôm nay
            </span>
          </div>

          <div className="tl__row tl__row--pick">
            {pick.map((s, i) => {
              const changed = base[i] && base[i].crop !== s.crop
              const photo = CROP_PHOTO[s.crop]
              return (
                <figure
                  key={s.index}
                  className="tl__tile"
                  data-changed={changed || undefined}
                  data-tone={cropTone(s.crop)}
                  style={{ left: `${x(t(s.sow))}%`, width: `calc(${x(t(s.harvest)) - x(t(s.sow))}% - 3px)` }}
                >
                  {photo ? <img src={photo.src} alt="" loading="lazy" /> : <CropArt crop={s.crop} size={44} />}
                  <figcaption>
                    <strong>{CROP_SHORT[s.crop] ?? s.crop_name_vi}</strong>
                    <span>
                      {day(s.sow)} – {day(s.harvest)}
                    </span>
                  </figcaption>
                  {changed && <span className="tl__flag">Đổi</span>}
                </figure>
              )
            })}
          </div>

          <div className="tl__row tl__row--base">
            <span className="tl__label">Hiện tại</span>
            {base.map((s) => (
              <span
                key={s.index}
                className="tl__bar"
                data-tone={cropTone(s.crop)}
                style={{ left: `${x(t(s.sow))}%`, width: `calc(${x(t(s.harvest)) - x(t(s.sow))}% - 3px)` }}
              >
                {CROP_SHORT[s.crop] ?? s.crop_name_vi}
              </span>
            ))}
          </div>

          {months.map((m) => (
            <span key={m.toISOString()} className="tl__grid" style={{ left: `${x(m.getTime())}%` }} aria-hidden="true" />
          ))}
        </div>
      </div>
    </div>
  )
}
