import type { ReactNode } from 'react'
import { Icon, type IconName } from '../../shared/ui/Icon'
import { href, navigate, useRoute } from '../../shared/router'
import { setActiveField, useActiveFieldId, useFields } from '../../shared/fields/store'
import './shell.css'

interface NavItem {
  path: string
  label: string
  short: string
  icon: IconName
}

export const NAV: NavItem[] = [
  { path: '/', label: 'Trang chủ', short: 'Trang chủ', icon: 'globe' },
  { path: '/ruong', label: 'Ruộng của tôi', short: 'Ruộng', icon: 'fields' },
  { path: '/mo-phong', label: 'Mô phỏng luân canh', short: 'Mô phỏng', icon: 'rotate' },
  { path: '/theo-doi', label: 'Theo dõi vụ', short: 'Theo dõi', icon: 'calendar' },
  { path: '/nguon', label: 'Nguồn dữ liệu', short: 'Dữ liệu', icon: 'satellite' },
]

const isActive = (current: string, item: string) => (item === '/' ? current === '/' : current === item || current.startsWith(`${item}/`))

/**
 * Frame for every screen after the landing page.
 * `crumbs` is the page path shown in the top bar; `bleed` lets map screens fill the content area edge to edge.
 */
export function AppShell({
  crumbs,
  actions,
  bleed = false,
  children,
}: {
  crumbs: { label: string; to?: string }[]
  actions?: ReactNode
  bleed?: boolean
  children: ReactNode
}) {
  const { path } = useRoute()
  const fields = useFields()
  const activeId = useActiveFieldId()

  return (
    <div className="shell">
      <a className="skip-link" href="#main">
        Bỏ qua điều hướng
      </a>
      <aside className="sidenav" aria-label="Điều hướng ứng dụng">
        <a className="sidenav__brand" href={href('/')} aria-label="FieldShift Mekong — trang chủ">
          <svg className="sidenav__mark" viewBox="0 0 32 32" aria-hidden="true">
            <path d="M16 28V15M16 15c0-5.5-4.2-8.5-9.5-8.5 0 5.5 4.2 8.5 9.5 8.5Zm0 0c0-5.5 4.2-8.5 9.5-8.5 0 5.5-4.2 8.5-9.5 8.5Z" />
          </svg>
          <span>FieldShift</span>
        </a>
        <nav>
          <ul>
            {NAV.map((item) => (
              <li key={item.path}>
                <a href={href(item.path)} aria-current={isActive(path, item.path) ? 'page' : undefined}>
                  <Icon name={item.icon} />
                  <span className="sidenav__label">{item.label}</span>
                  <span className="sidenav__short">{item.short}</span>
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <p className="sidenav__foot">Dữ liệu NASA · Hỗ trợ quyết định, không thay chuyên gia</p>
      </aside>

      <div className="shell__main">
        <header className="appbar">
          <nav className="crumbs" aria-label="Vị trí trang">
            <ol>
              {crumbs.map((c, i) => (
                <li key={c.label}>
                  {c.to && i < crumbs.length - 1 ? <a href={c.to}>{c.label}</a> : <span aria-current={i === crumbs.length - 1 ? 'page' : undefined}>{c.label}</span>}
                </li>
              ))}
            </ol>
          </nav>
          <div className="appbar__right">
            {fields.length > 0 && (
              <label className="field-switch">
                <span className="visually-hidden">Thửa đang làm việc</span>
                <Icon name="fields" />
                <select value={activeId ?? ''} onChange={(e) => setActiveField(e.target.value)}>
                  {fields.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name}
                    </option>
                  ))}
                </select>
                <Icon name="chevron" className="icon field-switch__chev" />
              </label>
            )}
            {actions ?? (
              <button type="button" className="btn btn--ghost btn--sm" onClick={() => navigate('/ruong/moi')}>
                <Icon name="plus" />
                <span>Thêm thửa</span>
              </button>
            )}
          </div>
        </header>
        <main id="main" className={bleed ? 'shell__content shell__content--bleed' : 'shell__content'}>
          {children}
        </main>
      </div>
    </div>
  )
}
