import type { ReactNode } from 'react'
import { Icon, type IconName } from '../../shared/ui/Icon'
import { href, useRoute } from '../../shared/router'
import './shell.css'

interface NavItem {
  path: string
  label: string
  short: string
  icon: IconName
}

export const NAV: NavItem[] = [
  { path: '/', label: 'Trang chủ', short: 'Trang chủ', icon: 'home' },
  { path: '/ruong', label: 'Ruộng của tôi', short: 'Ruộng', icon: 'fields' },
  { path: '/de-xuat', label: 'Đề xuất luân canh', short: 'Đề xuất', icon: 'sprout' },
  { path: '/theo-doi', label: 'Theo dõi vụ', short: 'Theo dõi', icon: 'calendar' },
  { path: '/nguon', label: 'Dữ liệu NASA', short: 'Dữ liệu', icon: 'database' },
]

const isActive = (current: string, item: string) => (item === '/' ? current === '/' : current === item || current.startsWith(`${item}/`))

/** Frame for every screen after the landing page: one top bar, content fills the rest. */
export function AppShell({ children, bleed = false }: { children: ReactNode; bleed?: boolean }) {
  const { path } = useRoute()
  return (
    <div className="shell">
      <a className="skip-link" href="#main">
        Bỏ qua điều hướng
      </a>
      <header className="topbar-app">
        <a className="topbar-app__brand" href={href('/')} aria-label="FieldShift Mekong — trang chủ">
          <svg className="topbar-app__mark" viewBox="0 0 32 32" aria-hidden="true">
            <path d="M16 28V15M16 15c0-5.5-4.2-8.5-9.5-8.5 0 5.5 4.2 8.5 9.5 8.5Zm0 0c0-5.5 4.2-8.5 9.5-8.5 0 5.5-4.2 8.5-9.5 8.5Z" />
          </svg>
          <span>FieldShift</span>
        </a>
        <nav className="appnav" aria-label="Điều hướng ứng dụng">
          <ul>
            {NAV.map((item) => (
              <li key={item.path}>
                <a href={href(item.path)} aria-current={isActive(path, item.path) ? 'page' : undefined}>
                  <Icon name={item.icon} />
                  <span className="appnav__label">{item.label}</span>
                  <span className="appnav__short">{item.short}</span>
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </header>
      <main id="main" className={bleed ? 'shell__content shell__content--bleed' : 'shell__content'}>
        {children}
      </main>
    </div>
  )
}
