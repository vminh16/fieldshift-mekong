import { useId } from 'react'
import type { TwinWeek } from '../../../../contracts/types'
import { CROP_PHOTO } from '../../shared/decision/photos'
import { CROP_SHORT, cropTone } from '../../shared/decision/source'

/** Canopy height as a share of full growth per FAO-56 stage (drawing only; no engine number). */
const GROWTH: Record<string, number> = { initial: 0.22, development: 0.55, mid: 1, late: 0.88 }
const STAGE_VI: Record<string, string> = { initial: 'Mới gieo', development: 'Đang phát triển', mid: 'Sinh trưởng mạnh', late: 'Chín, sắp thu' }

const W = 420
const AXIS = 40
const CANAL = 54
const GROUND = 150
const BOTTOM = 290
const DEPTH_M = 1.2
const PX_M = (BOTTOM - GROUND) / DEPTH_M
const nf = (n: number, d = 0) => n.toLocaleString('vi-VN', { maximumFractionDigits: d })

/**
 * Technical cross-section of the parcel for one week: real crop photo above ground growing with the
 * stage, soil column with depth axis, root zone, root-zone wetness, standing water and the canal.
 */
export function SoilColumn({ week }: { week: TwinWeek | undefined }) {
  const id = useId().replace(/:/g, '')
  const crop = week?.crop ?? null
  const stage = (week?.stage as string | null) ?? null
  const photo = crop ? CROP_PHOTO[crop] : undefined
  const growth = stage ? (GROWTH[stage] ?? 0.5) : 0
  const canopyH = growth * 118
  const pond = week?.ponding_mm.value ?? null
  const pondH = pond ? Math.max(3, (Math.min(pond, 120) / 120) * 26) : 0
  const root = week?.root_depth_m.value ?? null
  const rootH = root ? Math.min(root, DEPTH_M) * PX_M : 0
  const wet = week?.root_zone_water.value ?? null
  const salt = week?.salinity
  const inSaltSeason = Boolean(salt?.in_salinity_season)
  const x0 = AXIS
  const x1 = W - CANAL - 8
  const fieldW = x1 - x0

  const caption = crop ? `${CROP_SHORT[crop] ?? crop} · ${STAGE_VI[stage ?? ''] ?? 'Đang trồng'}` : 'Đất trống · làm đất, chuẩn bị vụ sau'

  return (
    <svg className="soil-col" viewBox={`0 0 ${W} 300`} role="img" aria-label={`${caption}. ${root ? `Rễ sâu ${nf(root, 1)} m.` : ''} ${wet !== null ? `Ẩm vùng rễ ${Math.round(wet * 100)}%.` : ''}`}>
      <defs>
        <clipPath id={`${id}-canopy`}>
          <rect x={x0} y={GROUND - canopyH} width={fieldW} height={canopyH} rx="3" />
        </clipPath>
        <linearGradient id={`${id}-fade`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#121513" stopOpacity="0.65" />
          <stop offset="0.45" stopColor="#121513" stopOpacity="0" />
        </linearGradient>
        <pattern id={`${id}-salt`} width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="6" stroke="#e3b866" strokeWidth="2" strokeOpacity="0.55" />
        </pattern>
        <pattern id={`${id}-roots`} width="14" height="10" patternUnits="userSpaceOnUse">
          <path d="M7 0v10M7 4l-4 6M7 6l3 4" stroke="#c2e3a8" strokeOpacity="0.16" strokeWidth="1" fill="none" />
        </pattern>
      </defs>

      {/* canopy: the crop's own photo, as tall as the stage */}
      {crop && photo && canopyH > 0 && (
        <g clipPath={`url(#${id}-canopy)`}>
          <image href={photo.src} x={x0} y={GROUND - 118} width={fieldW} height={118} preserveAspectRatio="xMidYMax slice" />
          <rect x={x0} y={GROUND - 118} width={fieldW} height={118} fill={`url(#${id}-fade)`} />
        </g>
      )}
      {crop && !photo && canopyH > 0 && <rect className={`soil-col__canopy soil-col__canopy--${cropTone(crop)}`} x={x0} y={GROUND - canopyH} width={fieldW} height={canopyH} rx="3" />}
      <text className="soil-col__caption" x={x0} y={18}>
        {caption}
      </text>

      {/* standing water (paddy only) */}
      {pondH > 0 && (
        <>
          <rect className="soil-col__pond" x={x0} y={GROUND - pondH} width={fieldW} height={pondH} />
          <text className="soil-col__note" x={x1 - 4} y={GROUND - pondH - 5} textAnchor="end">
            Nước mặt ruộng {nf(pond!)} mm
          </text>
        </>
      )}

      {/* soil column */}
      <rect className="soil-col__soil" x={x0} y={GROUND} width={fieldW} height={BOTTOM - GROUND} />
      {rootH > 0 && (
        <>
          <rect x={x0} y={GROUND} width={fieldW} height={rootH} fill={`url(#${id}-roots)`} />
          {wet !== null && <rect className="soil-col__wet" x={x0} y={GROUND + rootH * (1 - wet)} width={fieldW} height={rootH * wet} />}
          <line className="soil-col__rootline" x1={x0} x2={x1} y1={GROUND + rootH} y2={GROUND + rootH} />
          <text className="soil-col__note" x={x0 + 8} y={GROUND + rootH - 6}>
            Vùng rễ {nf(root!, 1)} m
          </text>
          {wet !== null && (
            <text className="soil-col__value" x={x1 - 8} y={GROUND + rootH - 6} textAnchor="end">
              Ẩm {Math.round(wet * 100)}%
            </text>
          )}
        </>
      )}
      <line className="soil-col__ground" x1={x0} x2={x1} y1={GROUND} y2={GROUND} />

      {/* depth axis */}
      {[0, 0.4, 0.8, 1.2].map((d) => (
        <g key={d}>
          <line className="soil-col__tick" x1={x0 - 5} x2={x0} y1={GROUND + d * PX_M} y2={GROUND + d * PX_M} />
          <text className="soil-col__axis" x={x0 - 8} y={GROUND + d * PX_M + 4} textAnchor="end">
            {nf(d, 1)} m
          </text>
        </g>
      ))}

      {/* canal + salinity */}
      <g transform={`translate(${W - CANAL}, 0)`}>
        <text className="soil-col__axis" x={CANAL / 2} y={GROUND - 30} textAnchor="middle">
          Kênh
        </text>
        <rect className="soil-col__canal" x="0" y={GROUND - 18} width={CANAL} height={86} rx="3" />
        {inSaltSeason && <rect x="0" y={GROUND - 18} width={CANAL} height={86} rx="3" fill={`url(#${id}-salt)`} />}
        <text className="soil-col__salt" x={CANAL / 2} y={GROUND + 30} textAnchor="middle">
          {salt?.value != null ? `${nf(salt.value, 1)}` : '?'}
        </text>
        <text className="soil-col__axis" x={CANAL / 2} y={GROUND + 46} textAnchor="middle">
          {salt?.value != null ? 'dS/m' : 'chưa đo'}
        </text>
        {inSaltSeason && (
          <text className="soil-col__warn" x={CANAL / 2} y={GROUND + 84} textAnchor="middle">
            Mùa mặn
          </text>
        )}
      </g>
    </svg>
  )
}
