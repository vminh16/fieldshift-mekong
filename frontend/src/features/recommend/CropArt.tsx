import { cropTone } from '../../shared/decision/source'

/**
 * Line drawings of the crop families, one per colour slot. Illustration, not UI icons:
 * single 1.6px stroke, round joins, drawn in the crop's validated colour on a faint ground line.
 */
const ART = {
  // Rice: curved culm, three blades, drooping panicle of grains.
  rice: (
    <>
      <path d="M24 44c0-9 1-18 4.5-27" />
      <path d="M28.5 17c3.5-2.6 7.5-1.6 9.6 3.6" />
      <path d="M30.6 15.4l.8-2.8M33.4 15l1-2.6M35.8 16.2l1.8-2M37.4 18.6l2.4-1.2M38.2 21.2l2.4.2" />
      <path d="M24.2 36c-5-5.5-9.5-7.6-15-7.4 4.4 2.8 8.6 5.6 15 7.4Z" />
      <path d="M24.8 30.5c4.4-4 8.6-5.2 13.6-4.4-4 2-8 3.6-13.6 4.4Z" />
      <path d="M24 40.5c-3.4-2.4-5.6-6.2-6.4-11.4" />
    </>
  ),
  // Legume: upright stem, trifoliate leaf, two hanging pods with beans.
  legume: (
    <>
      <path d="M24 44V14" />
      <path d="M24 14c-1.6-4.2-.4-8 3-10 1.2 4-.2 7.6-3 10Z" />
      <path d="M24 16c-4-.6-6.6-3.4-7-7.4 3.8.6 6.4 3.2 7 7.4Z" />
      <path d="M24 16c4-.6 6.6-3.4 7-7.4-3.8.6-6.4 3.2-7 7.4Z" />
      <path d="M24 24c4.6 1.2 7 5 6.6 11-3.4-2-5.8-5.6-6.6-11Z" />
      <path d="M24 26c-4.2 1.4-6.2 5.2-5.6 10.6 3.2-2 5.2-5.4 5.6-10.6Z" />
      <circle cx="27.6" cy="28.6" r=".9" />
      <circle cx="28.8" cy="31.6" r=".9" />
      <circle cx="20.6" cy="30.6" r=".9" />
      <circle cx="19.8" cy="33.6" r=".9" />
    </>
  ),
  // Cover crop: low clover-like mat holding the soil.
  cover: (
    <>
      <path d="M14 44c0-4 1-7 3-9M24 44c0-6 0-10 0-13M34 44c0-4-1-7-3-9" />
      <circle cx="15" cy="33" r="3" />
      <circle cx="19.4" cy="32" r="3" />
      <circle cx="17" cy="28.6" r="3" />
      <circle cx="22" cy="27.6" r="3" />
      <circle cx="26.4" cy="27.8" r="3" />
      <circle cx="24.2" cy="23.6" r="3" />
      <circle cx="31" cy="33" r="3" />
      <circle cx="33.4" cy="29.2" r="3" />
    </>
  ),
  // Anything else: a single broad leaf.
  other: (
    <>
      <path d="M24 44V22" />
      <path d="M24 30c-9-2-12-10-10-20 8 2 12 9 10 20Z" />
      <path d="M24 26c6-1.4 9-6 8-13-5.6 1.4-8.6 6-8 13Z" />
    </>
  ),
} as const

export function CropArt({ crop, size = 56 }: { crop: string; size?: number }) {
  const tone = cropTone(crop)
  return (
    <svg className="crop-art" data-tone={tone} width={size} height={size} viewBox="0 0 48 48" aria-hidden="true">
      <path className="crop-art__ground" d="M8 44.5h32" />
      <g className="crop-art__plant">{ART[tone]}</g>
    </svg>
  )
}
