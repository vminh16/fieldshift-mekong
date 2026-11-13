/** Small outline icon set (24×24, stroke = currentColor). No icon font, no extra dependency. */
const PATHS = {
  globe: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm-9 9h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3Z',
  fields: 'M3 6.5 9 4l6 2.5L21 4v13.5L15 20l-6-2.5L3 20V6.5ZM9 4v13.5M15 6.5V20',
  rotate: 'M4 9h11l-3-3M20 15H9l3 3M4 9a8 8 0 0 1 3-4.5M20 15a8 8 0 0 1-3 4.5',
  calendar: 'M4 6.5A1.5 1.5 0 0 1 5.5 5h13A1.5 1.5 0 0 1 20 6.5v12a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 18.5v-12ZM4 10h16M8 3v4M16 3v4M9 15l2 2 4-4',
  satellite: 'M7.5 7.5 4 4m3.5 3.5 3-3 6 6-3 3-6-6Zm9 9L20 20M3.5 14.5a6 6 0 0 0 6 6M3.5 18a2.5 2.5 0 0 0 2.5 2.5',
  plus: 'M12 5v14M5 12h14',
  locate: 'M12 4V2m0 20v-2m8-8h2M2 12h2m8 6a6 6 0 1 0 0-12 6 6 0 0 0 0 12Zm0-3.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z',
  undo: 'M9 14 4 9l5-5M4 9h10.5a5.5 5.5 0 0 1 0 11H11',
  trash: 'M4 7h16M10 11v6M14 11v6M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2l1-12M9 7V4h6v3',
  check: 'M5 12.5 10 17 19 7',
  polygon: 'M5 7.5 12 4l7 4.5-1.5 9L8 20l-3-12.5Z',
  pin: 'M12 21s-6.5-6.2-6.5-11a6.5 6.5 0 0 1 13 0c0 4.8-6.5 11-6.5 11Zm0-8.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z',
  zoomIn: 'M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13Zm4.6-1.9L20 20M10.5 8v5M8 10.5h5',
  arrowLeft: 'M19 12H5m6-6-6 6 6 6',
  arrowRight: 'M5 12h14m-6-6 6 6-6 6',
  edit: 'M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16v4Zm9.5-13.5 4 4',
  chevron: 'm6 9 6 6 6-6',
} as const

export type IconName = keyof typeof PATHS

export function Icon({ name, className = 'icon' }: { name: IconName; className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden="true">
      <path d={PATHS[name]} />
    </svg>
  )
}
