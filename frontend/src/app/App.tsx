import { LandingPage } from '../features/landing/LandingPage'
import { FieldsWorkspace } from '../features/fields/FieldsWorkspace'
import { PlannedScreen } from '../features/shell/PlannedScreen'
import { useRoute } from '../shared/router'

export function App() {
  const route = useRoute()
  const { path } = route

  if (path === '/') return <LandingPage />
  // One workspace for browsing, drawing and editing parcels, so the map survives mode changes.
  if (path === '/ruong' || path.startsWith('/ruong/')) return <FieldsWorkspace route={route} />

  if (path === '/mo-phong')
    return (
      <PlannedScreen
        title="Mô phỏng luân canh"
        icon="sprout"
        lead="So sánh chuỗi vụ đang trồng với 2–4 phương án thay thế, cùng một kịch bản thời tiết, rồi xem diễn biến từng tuần trên ruộng."
        items={[
          'Khai báo điều kiện: chuỗi vụ hiện tại, tưới, thoát nước, độ mặn nước kênh — “Chưa biết” là một câu trả lời hợp lệ',
          'Thẻ phương án cạnh baseline, chip chênh lệch nước tưới và ngày stress',
          'Biểu đồ “mỗi chấm = 1 năm” thay cho con số xác suất',
          'Mặt cắt ruộng theo tuần: nước mặt ruộng, ẩm vùng rễ, mùa mặn',
          'Thử “nếu… thì…”: mưa −30%, mặn sớm 4 tuần, gieo trễ 7 ngày',
        ]}
      />
    )
  if (path === '/theo-doi')
    return (
      <PlannedScreen
        title="Theo dõi vụ"
        icon="calendar"
        lead="Sau khi chọn phương án: việc cần làm, các ngưỡng cảnh báo, và tính lại kế hoạch sau mỗi vụ."
        items={['Checklist đo đạc trước khi xuống giống', 'Ngưỡng “Nếu EC vượt … thì …” theo từng vụ', 'Đóng vụ và tính lại các vụ còn lại', 'Chia sẻ bản tóm tắt một trang qua Zalo hoặc in']}
      />
    )
  if (path === '/nguon')
    return (
      <PlannedScreen
        title="Dữ liệu NASA"
        icon="database"
        lead="Mỗi con số trong ứng dụng ghi rõ nguồn, độ phân giải và giới hạn của nó."
        items={['NASA POWER, GPM IMERG, SMAP, NASADEM — trạng thái và thời điểm cập nhật', 'Khác nhau giữa đo tại ruộng, ước lượng vùng và kịch bản', 'Giới hạn: ô lưới vệ tinh không phải số đo tại thửa']}
      />
    )

  return <LandingPage />
}
