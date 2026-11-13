# UI Design Brief — FieldShift-Mekong (chống "AI slop", dựa trên nghiên cứu)

Đọc cùng `docs/architecture/SOLUTION_DESIGN.md` §11. Mục tiêu: một công cụ **cán bộ khuyến nông ngồi cùng nông dân** dùng trên điện thoại để quyết định chuỗi vụ — không phải dashboard trình diễn.

## 1. Căn cứ nghiên cứu → quyết định thiết kế

| Bằng chứng | Hệ quả cho UI |
|---|---|
| Nông dân ĐBSCL chủ yếu dùng **Zalo**; chỉ ~3% dùng app nông nghiệp chuyên dụng; nguồn tin tin cậy nhất là **cán bộ khuyến nông/HTX** (IRRI, Barnard et al. 2023). Bản tin nông vụ phát qua >1.000 nhóm Zalo. | Người dùng chính = cán bộ khuyến nông. Kết quả phải **chia sẻ được dưới dạng 1 ảnh/1 trang** (nút "Chia sẻ qua Zalo" = mở trang export / tải ảnh). Ngôn ngữ nông dân, không thuật ngữ. |
| Áp dụng DSS thấp; khả năng dùng và **khớp với cách nông dân ra quyết định** quyết định adoption (Rose et al. 2016, Agricultural Systems). Twin chỉ hữu ích khi khớp thực hành quản lý (nghiên cứu digital twin đồng cỏ Úc, Agric. Human Values 2025). | Màn chính trả lời đúng 3 câu: *Đổi vụ nào? Được/mất gì so với hiện tại? Phải kiểm tra gì trước?* Twin dùng ẩn dụ nông dân quen: **mực nước ruộng** (như ống AWD), lịch vụ, mặn theo tháng. |
| **Quantile dotplot** giúp người không chuyên ước lượng xác suất chính xác hơn và quyết định tốt hơn so với khoảng/mật độ (Kay et al. CHI 2016; Fernandes et al. CHI 2018). | Hiển thị bất định bằng **mỗi chấm = một năm thời tiết thật (2001–2024)**: "Trong 24 năm, có 5 năm phải tưới > 1.500 mm". Không dùng ±, không dùng "xác suất" (kịch bản không phải xác suất đã hiệu chỉnh). |
| Hiệu quả trực quan cho quyết định khác cho ước lượng (Kale et al. TVCG 2021). | Luôn kèm **câu kết luận bằng chữ** cạnh biểu đồ; biểu đồ là bằng chứng phụ. |

## 2. Chống AI slop — cấm

- Gradient tím/xanh, glassmorphism, blob, hero to với slogan, "✨", emoji làm icon, card bóng đổ đồng loạt, số liệu "dashboard" khổng lồ không ngữ cảnh.
- Copy rỗng: "Unlock", "Empower", "AI-powered insights", "Smart farming". Không chữ "AI" trên UI.
- Thanh tiến độ/điểm "Soil health 87%", gauge, radar chart, % độ tin cậy tự chế.
- Tất cả các card cùng kích thước, cùng icon tròn màu pastel; lưới 3 cột feature.
- Màu là tín hiệu duy nhất. Animation trang trí.

## 3. Ngôn ngữ thị giác

- **Chất liệu:** giống tờ lịch thời vụ in của khuyến nông + bản đồ thủy văn: nền giấy ngà, mực sẫm, đường kẻ mảnh, bảng rõ.
- **Màu (token, không dùng ngoài bảng):** `--ink #1d2a24`, `--paper #f7f4ec`, `--rule #d9d2c3`, `--water #2f6f9f` (nước/tưới), `--rice #6f8f3a` (lúa), `--upland #b07a2a` (cây cạn/đậu), `--salt #b4483c` (mặn/rủi ro), `--muted #6b7068`. Trạng thái: chữ + biểu tượng hình học (●▲■?) + màu.
- **Chữ:** 1 font sans hỗ trợ tiếng Việt tốt (Be Vietnam Pro hoặc system-ui), số dùng `font-variant-numeric: tabular-nums`. Cỡ ≥16px trên điện thoại.
- **Đơn vị luôn đi kèm**; số làm tròn có nghĩa (tưới: 10 mm; nước: m³/ha ×10 = mm).
- **Nhãn nguồn** cạnh mỗi số: chip nhỏ chữ `Đo tại ruộng / Ước lượng vùng / Dự kiến / Kịch bản / Chưa biết` (lấy từ API `label`).

## 4. Màn hình

### 4.1 Quyết định (mặc định)
- Đầu trang: tên ruộng, ngày lập, kịch bản đang xem (chip loại kịch bản). 1 câu tóm tắt do backend cung cấp (reasons[0]).
- **Lịch 3 vụ dạng dải ngang theo tháng** (T11 → T10): mỗi phương án là một hàng; khối màu theo cây (lúa/cây cạn/nghỉ), dải mặn (`in_salinity_season`) phủ nền đỏ nhạt có gạch chéo. Hàng "Hiện tại" luôn ở trên cùng.
- Mỗi hàng bên phải: **Δ nước tưới so với hiện tại** (mm và m³/ha), trạng thái (chữ), 1 rủi ro lớn nhất. Chạm → mở chi tiết.
- Dotplot 24 năm cho phương án đang chọn vs hiện tại (cần backend trả phân bố theo năm — xem §6).

### 4.2 Mô phỏng (Twin) — phần trình diễn chính, phải làm tốt nhất
- **Mặt cắt ruộng (SVG)** chứ không phải 3D: lớp đất, rễ cây theo giai đoạn, **mực nước** (ruộng lúa: nước mặt trên mặt ruộng; cây cạn: ẩm vùng rễ dạng % tô trong đất), mưa tuần (vạch rơi), tưới (mũi tên từ kênh), kênh bên cạnh với **độ mặn**: số đo nếu có, "?" + "Chưa đo" nếu không, nền gạch chéo khi vào mùa mặn.
- **Hai mặt cắt cạnh nhau**: Hiện tại | Phương án — cùng năm thời tiết, cùng tuần. Thanh tuần (scrubber) dùng chung, phím ←/→.
- Bộ chọn năm thời tiết bằng tên dễ hiểu: "Năm bình thường", "Năm hạn như 2016", "Năm ướt như 2020" (từ `analog_year`/scenarios).
- Tối đa 4 chỉ số cố định dưới mặt cắt: nước vùng rễ, mặn kênh, stress tuần này, tưới cộng dồn — mỗi chỉ số có nhãn nguồn.
- Biểu đồ tuần nhỏ (sparkline) tưới cộng dồn 2 đường (hiện tại vs phương án) — khoảng cách giữa 2 đường = nước tiết kiệm. Ghi chú sự kiện trên trục: gieo, thu hoạch, bắt đầu mùa mặn.
- Không animation tự chạy; người dùng kéo. `prefers-reduced-motion` tôn trọng.

### 4.3 What-if
- Ngôn ngữ câu hỏi: "Nếu mưa ít hơn …%", "Nếu mặn đến sớm … tuần", "Nếu gieo muộn … ngày". Kết quả là **bản kế hoạch mới** (ghi "Bản thử #2, gốc #1"); hiển thị thay đổi so với bản gốc bằng câu: "Phương án đậu xanh vẫn tiết kiệm nước nhất; lúa vụ 3 chuyển sang 'cần kiểm tra'".

### 4.4 Kiểm tra trước khi xuống giống
- Checklist kiểu phiếu: ô vuông, việc cụ thể, ai làm. Ngưỡng dừng: "Nếu nước kênh > 1,2 dS/m (≈0,8 ‰) trước 15/1 → không gieo đậu xanh". Nút "Chia sẻ qua Zalo" (mở `/v1/plans/{id}/export`).
- Phần "Nguồn dữ liệu" gọn: NASA POWER (ô ~50 km), SRTM, … với giới hạn.

## 5. Chấp nhận (reviewer sẽ kiểm)
- 360px không cuộn ngang; mọi điều khiển bàn phím được; contrast ≥ 4.5:1.
- Không số nào không có đơn vị + nhãn nguồn; `null` → "Chưa biết" + lý do.
- Baseline và phương án luôn cùng kịch bản/năm khi so.
- Không component nào tự tính khuyến nghị/trạng thái.

## 6. Cần từ backend (sẽ bổ sung, additive)
- `options[].distribution[scenario_id] = [{year, irrigation_mm, water_stress_days}]` cho dotplot.
- Twin daily/weekly: `ponding_mm` (ruộng lúa) để vẽ mực nước thật.

Nguồn: Kay et al. 2016 (CHI) "When (ish) is my bus?"; Fernandes et al. 2018 (CHI); Kale, Kay, Hullman 2021 (IEEE TVCG); Rose et al. 2016 (Agricultural Systems 149:165–174); Barnard et al. 2023 (IRRI/CGIAR) "Use of digital tools in sustainable rice production in the Mekong Delta"; Agriculture and Human Values 2025 (rangeland digital twin interfaces).
