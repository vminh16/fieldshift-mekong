import { useEffect, useState } from 'react'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

type ApiState = 'checking' | 'online' | 'offline'

export function App() {
  const [status, setStatus] = useState<ApiState>('checking')
  useEffect(() => {
    const controller = new AbortController()
    fetch(`${apiBaseUrl}/v1/health`, { signal: controller.signal })
      .then((response) => setStatus(response.ok ? 'online' : 'offline'))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          console.error('API health request failed', error)
          setStatus('offline')
        }
      })
    return () => controller.abort()
  }, [])
  return (
    <main className="layout">
      <span className="eyebrow">NASA Space Apps 2026 · Field Shift</span>
      <h1>FieldShift–Mekong</h1>
      <p className="lead">Climate-Adaptive Crop Rotation Decision Support System</p>
      <section className="panel">
        <h2>Engineering starter</h2>
        <p>Khung dự án đã sẵn sàng. Planning Engine, dự báo, nguồn NASA và Digital Twin chưa được hiện thực.</p>
        <p>API status: <strong data-state={status}>{status}</strong></p>
        <p>Không dùng bản scaffold này để đưa ra quyết định canh tác thực tế.</p>
      </section>
      <section className="grid" aria-label="Planned product modules">
        <article><h3>Field Profile</h3><p>Đất · Nước · Lịch sử · Ràng buộc</p></article>
        <article><h3>Future Outlook</h3><p>Forecast ≠ Projection ≠ Stress Test</p></article>
        <article><h3>Rotation Planning</h3><p>Candidate · Feasibility · Risk</p></article>
        <article><h3>Digital Twin</h3><p>Viewer of backend trajectories</p></article>
      </section>
    </main>
  )
}
