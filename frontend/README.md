# FieldShift Mekong — Frontend

Môi trường frontend độc lập, tách khỏi `apps/web` (scaffold cũ). Hiện có **landing page** với quả địa cầu 3D.

## Stack (chốt tạm)

| Lớp | Lựa chọn | Lý do |
|---|---|---|
| UI | React 19 + TypeScript | Trùng với `apps/web` và hệ sinh thái component |
| Build | Vite 6 | Dev server nhanh, cấu hình tối thiểu |
| 3D | three.js + shader tự viết | Toàn quyền màu biển, ánh sáng, khí quyển, mây — giống ảnh mẫu |
| Bản đồ | MapLibre GL + ảnh vệ tinh Esri | Zoom lẻ mượt 60fps, điều khiển từng khung hình cùng địa cầu |
| Tìm địa điểm | Danh sách tỉnh ĐBSCL + Photon (OpenStreetMap) | Toàn cầu, không cần key; `VITE_GEOCODER_URL=off` để tắt |
| Font | Be Vietnam Pro (self-hosted qua `@fontsource`) | Thiết kế cho tiếng Việt, dấu rõ, không gọi Google Fonts |

## Chạy

```bash
cd frontend
npm install
npm run dev        # http://localhost:5180
npm run typecheck
npm run build
```

Tuỳ chọn: copy `.env.example` → `.env.local` để bật geocoder online (tìm huyện/xã/đường) hoặc đổi nguồn ảnh vệ tinh chi tiết.

## Cấu trúc

```text
frontend/
├─ public/textures/            Bề mặt 8K/4K, mây 4K, địa hình + mặt nạ đất
├─ src/
│  ├─ app/App.tsx              Điểm vào; router sẽ thêm khi có màn tiếp theo
│  ├─ styles/                  tokens.css (màu, chữ, bo góc) + global.css
│  ├─ features/
│  │  ├─ landing/              Bố cục landing page
│  │  ├─ globe/                EarthRenderer (three.js), shaders, WorldMap (MapLibre)
│  │  └─ location-search/      Ô tìm kiếm + gợi ý + chip tỉnh
│  └─ shared/geo/              Gazetteer ĐBSCL (13 tỉnh cũ → 6 đơn vị sau sáp nhập 2025), geocode
└─ .env.example
```

## Hành vi địa cầu

- Tự xoay tây → đông, 100 giây/vòng. Kéo để xoay (có quán tính); **không zoom** bằng cuộn chuột.
- Ánh sáng cố định góc trên-phải so với người xem: viền khí quyển sáng bên phải, bóng tối nhẹ góc dưới-trái.
- Chọn địa điểm bất kỳ trên thế giới (chip, ô tìm kiếm, bấm lên địa cầu, hoặc chấm **ĐBSCL**): địa cầu xoay tới →
  lao xuống → hoà sang bản đồ. **Một timeline duy nhất** điều khiển cả hai theo cùng mức zoom từng khung hình
  (`EarthGlobe.tsx → runZoom`), nên không có điểm chuyển giao giật. "Về toàn cầu" chạy ngược timeline đó.
- Đây là hiệu ứng thị giác; toạ độ tỉnh là **tâm ước lượng**, không phải ranh giới thửa.

### Texture (`public/textures/`)

| File | Nguồn | Ghi chú |
|---|---|---|
| `earth-day-8k.jpg`, `earth-day-4k.jpg` | Solar System Scope (CC BY 4.0), dựa trên NASA Blue Marble | 8K chỉ nạp khi GPU hỗ trợ |
| `earth-clouds-4k.jpg` | Solar System Scope (CC BY 4.0) | Hạ từ 8K |
| `earth-bump-mask-4k.jpg` | three.js examples (R: địa hình, G: mặt đất) | |

Shader nằm ở `src/features/globe/shaders.ts` — chỉnh màu biển, độ bão hoà đất, độ dày khí quyển tại đây.

## Giới hạn hiện tại

- Mây là ảnh tĩnh (không phải thời tiết hiện tại).
- Chưa có ranh giới hành chính (GeoJSON); bấm lên địa cầu chọn tỉnh có tâm gần nhất (~65 km), hoặc cả vùng ĐBSCL nếu bấm gần.
- Tìm kiếm gửi chuỗi người dùng gõ tới Photon (komoot). Dùng cho demo; production nên tự host Photon/Nominatim.
- Nút "Khoanh thửa ruộng" đang khoá — màn tiếp theo chưa thiết kế.
