import { AppShell } from './AppShell'
import { Icon, type IconName } from '../../shared/ui/Icon'
import { href } from '../../shared/router'

/** Placeholder for a section whose design is agreed but not built yet. Lists what it will contain. */
export function PlannedScreen({ title, icon, lead, items }: { title: string; icon: IconName; lead: string; items: string[] }) {
  return (
    <AppShell>
      <section className="planned">
        <div className="planned__icon" aria-hidden="true">
          <Icon name={icon} className="icon" />
        </div>
        <p className="planned__kicker">Đang thiết kế</p>
        <h1>{title}</h1>
        <p className="planned__lead">{lead}</p>
        <ul>
          {items.map((i) => (
            <li key={i}>{i}</li>
          ))}
        </ul>
        <a className="btn btn--ghost" href={href('/ruong')}>
          <Icon name="fields" /> Về Ruộng của tôi
        </a>
      </section>
    </AppShell>
  )
}
