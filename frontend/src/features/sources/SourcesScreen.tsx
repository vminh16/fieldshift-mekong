import { useEffect, useState } from 'react'
import { api } from '../../shared/api/client'
import { isDataSource, type DataSource, type SourceInventory, type SourceUse } from '../../shared/api/auditTypes'
import { AppShell } from '../shell/AppShell'
import './sources.css'

const GROUPS: [SourceUse, string, string][] = [
  ['DECISION', 'Quyết định', 'Tham gia tính toán hoặc xếp hạng phương án.'],
  ['EVIDENCE', 'Bằng chứng', 'Hỗ trợ giải thích và bản tin.'],
  ['CONTEXT', 'Bối cảnh', 'Cho biết bối cảnh, không trực tiếp đổi phương án.'],
  ['NOT_USED', 'Chưa dùng', 'Chưa tham gia vào đề xuất hiện tại.'],
]
const LEGACY_STATUS: Record<string, string> = {
  LIVE_OR_CACHED: 'Trực tuyến hoặc có bản lưu', OFTEN_UNAVAILABLE: 'Thường không có dữ liệu',
  UNAVAILABLE: 'Không có dữ liệu', USER_INPUT_ONLY: 'Chỉ do người dùng nhập',
}

export function SourcesScreen() {
  const [inventory, setInventory] = useState<SourceInventory | null>(null)
  const [error, setError] = useState(false)
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    let live = true
    setError(false)
    setInventory(null)
    api.sources().then((data) => {
      if (!Array.isArray(data.sources)) throw new Error('Invalid inventory')
      if (live) setInventory(data)
    }).catch(() => live && setError(true))
    return () => { live = false }
  }, [attempt])
  const sources = inventory?.sources.filter(isDataSource) ?? []
  const legacy = inventory?.sources.filter((s) => !isDataSource(s)) ?? []
  return (
    <AppShell>
      <div className="source-page">
        <header>
          <p className="source-page__kicker">Nguồn & giới hạn</p>
          <h1>Dữ liệu NASA</h1>
          <p>Nguồn nào đổi đề xuất, nguồn nào chỉ để đối chiếu? Danh mục dưới đây do API cung cấp, gồm cả nguồn ngoài NASA.</p>
          {inventory?.generated_at && <p className="source-page__muted">Danh mục cập nhật: {new Date(inventory.generated_at).toLocaleString('vi-VN')}</p>}
        </header>
        <aside className="source-explainer" aria-label="Hiểu đúng dữ liệu">
          <h2>Ô lưới khác số đo tại ruộng</h2>
          <p>NASA POWER dùng ô lưới khoảng 55 km: một ô có thể phủ nhiều xã, không phải số đo của thửa. Cần đo mặn nước kênh và kiểm tra điều kiện ruộng trước khi gieo.</p>
          <p><strong>ET₀</strong> là lượng nước bốc thoát tham chiếu, dùng để ước tính nhu cầu nước cây. <strong>IMERG</strong> ước lượng mưa từ vệ tinh theo ô lưới. <strong>ENSO / ONI (NOAA, ngoài NASA)</strong> là tín hiệu thống kê để đối chiếu các năm tương tự, không phải dự báo mưa hay mặn tại ruộng.</p>
        </aside>
        {!inventory && !error && <p role="status">Đang tải danh mục từ máy chủ…</p>}
        {error && <div role="alert"><p>Chưa tải được danh mục nguồn. Chưa thể xác nhận nguồn nào đang được dùng.</p><button className="btn btn--ghost" onClick={() => setAttempt((n) => n + 1)}>Thử lại</button></div>}
        {legacy.length > 0 && <section className="source-legacy" aria-labelledby="legacy-title">
          <h2 id="legacy-title">Máy chủ đang trả danh mục cũ</h2>
          <p>Danh mục này chỉ có trạng thái khả dụng, chưa xác nhận nguồn tham gia quyết định, bằng chứng hay bối cảnh. Không suy ra “đang dùng” từ việc đã tải dữ liệu; trạng thái có thể chưa khớp với bằng chứng trong từng kế hoạch.</p>
          <ul>{legacy.map((item, i) => {
            const s = item && typeof item === 'object' ? item as Record<string, unknown> : {}
            return <li key={i}><strong>{typeof s.id === 'string' ? s.id : 'Nguồn chưa rõ'}</strong>
              <span>{typeof s.status === 'string' ? LEGACY_STATUS[s.status] ?? s.status : 'Chưa có trạng thái'}</span>
              <span>Độ phân giải: {typeof s.resolution === 'string' ? s.resolution : 'chưa công bố'}</span>
              <span>Thời gian, phân loại NASA và cách dùng: chưa công bố trong danh mục này.</span>
              {typeof s.note === 'string' && <small>Ghi chú gốc từ API: {s.note}</small>}
            </li>
          })}</ul>
        </section>}
        {inventory && GROUPS.map(([use, title, note]) => <section key={use} aria-labelledby={`source-${use}`}>
          <h2 id={`source-${use}`}>{title}</h2><p className="source-page__muted">{note}</p>
          {sources.some((s) => s.use === use)
            ? <div className="source-cards">{sources.filter((s) => s.use === use).map((s) => <SourceCard key={s.id} source={s} />)}</div>
            : <p className="source-page__muted">API chưa công bố nguồn thuộc nhóm này.</p>}
        </section>)}
        {inventory?.sources.length === 0 && <p>Máy chủ trả danh mục trống. Chưa thể xác nhận nguồn đang dùng.</p>}
      </div>
    </AppShell>
  )
}

function SourceCard({ source: s }: { source: DataSource }) {
  const url = s.url && /^https?:\/\//i.test(s.url) ? s.url : null
  return <article className="source-card">
    <div className="source-card__head"><h3>{s.name}</h3><span className="source-badge" data-nasa={s.is_nasa}>{s.is_nasa ? 'NASA' : 'Ngoài NASA'}</span></div>
    <p className="source-page__muted">{s.provider}</p>
    <p><strong>Dùng để làm gì:</strong> {s.used_for_vi}</p>
    <dl><div><dt>Độ phân giải</dt><dd>{s.spatial_resolution || 'Chưa công bố'}</dd></div>
      <div><dt>Khoảng thời gian</dt><dd>{s.time_range || 'Chưa công bố'}</dd></div>
      <div><dt>Độ trễ</dt><dd>{s.latency || 'Chưa công bố'}</dd></div></dl>
    <strong>Giới hạn</strong>
    {s.limitations_vi.length ? <ul>{s.limitations_vi.map((v) => <li key={v}>{v}</li>)}</ul> : <p>API chưa công bố giới hạn của nguồn này.</p>}
    {url && <a href={url} target="_blank" rel="noreferrer">Xem nguồn gốc ↗</a>}
  </article>
}
