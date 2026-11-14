# A7 — xung đột Tmax POWER / ERA5

Sinh bởi `scripts/audit_heat_bias.py`, offline, as_of 14/11/2026. Mỗi phép so chỉ tắt/bật hiệu chỉnh ngày nóng, giữ cùng khung mặn và mọi đầu vào khác.

Chính sách §7.3: dùng các cặp ngày trước as_of để tính chênh lệch trung bình theo tháng (ít nhất 60 ngày). Khi |POWER − ERA5| > 2 °C, trừ chênh lệch khỏi Tmax **chỉ để đếm ngày nóng**. Còn lại dùng POWER gốc. Giữ cả hai nguồn và `source_conflicts`; không phải đo tại thửa hay kiểm định cực trị ngày. Ngoài 4 bundle ERA5, giữ POWER và ghi UNAVAILABLE.

ET₀ giữ nguyên Tmax/Tmin/điểm sương/bức xạ/gió POWER để không ghép một vector khí tượng chưa hiệu chỉnh đồng bộ. Vì vậy không tuyên bố đã sửa sai lệch ET₀; tưới tuyệt đối vẫn là ước tính mô hình. Các số tưới dưới đây là baseline cố định, chưa lẫn tác động đổi lựa chọn.

## Tháng 3, 2001–2025

| Ruộng | Tmax POWER / ERA5 (°C) | Ngày ≥35 °C/năm POWER / sau chỉnh / ERA5 |
|---|---|---|
| Cần Thơ | 36.7 / 32.6 | 25.6 / 2.8 / 0.5 |
| Châu Đốc | 37.0 / 34.2 | 26.3 / 12.1 / 9.4 |
| Bến Tre | 34.1 / 30.6 | 7.5 / 0.0 / 0.0 |
| Sóc Trăng | 30.5 / 28.9 | 0.0 / 0.0 / 0.0 |

## 3 vụ tới: baseline lúa cố định, sc_clim (trung vị)

| Ruộng | Ngày nóng giai đoạn nhạy cảm trước → sau | Số cờ R_HEAT trước → sau | Tưới (mm) trước → sau | Δ ET₀ / tưới do chỉnh nhiệt (mm) | Tưới top-1 trước → sau (mm, có thể đổi chuỗi) |
|---|---|---|---|---|---|
| Cần Thơ | 14.5 → 0.0 | 1 → 0 | 1747 → 1747 | 0 | 1144 → 1144 |
| Châu Đốc | 21.0 → 2.5 | 1 → 0 | 1740 → 1740 | 0 | 1208 → 1323 |
| Bến Tre | 0.5 → 0.0 | 0 → 0 | 1673 → 1673 | 0 | 1003 → 1003 |
| Sóc Trăng | 0.0 → 0.0 | 0 → 0 | 1587 → 1587 | 0 | 1001 → 1001 |

## Lựa chọn sau A7

- Cần Thơ: top-1 trước `seq_rice_peanut_rice__early_standard_standard`, sau `seq_rice_peanut_rice__early_standard_standard`; shortlist sau: `low_risk: rice/peanut/rice`, `save_water: mungbean/rice/rice`, `soil_support: peanut/rice/rice`, `balanced: rice/maize/rice`, `third_season_rest: rice/rice/fallow_cover`
- Châu Đốc: top-1 trước `seq_rice_maize_rice__early_standard_standard`, sau `seq_rice_peanut_rice__standard_standard_standard`; shortlist sau: `low_risk: rice/peanut/rice`, `save_water: mungbean/rice/rice`, `soil_support: peanut/rice/rice`, `balanced: rice/maize/rice`, `third_season_rest: rice/rice/fallow_cover`
- Bến Tre: top-1 trước `seq_rice_fallow_cover_rice__early_standard_standard`, sau `seq_rice_fallow_cover_rice__early_standard_standard`; shortlist sau: `low_risk: rice/fallow_cover/rice`, `save_water: mungbean/rice/rice`, `soil_support: rice/peanut/rice`, `balanced: rice/maize/rice`, `salinity_avoidance: rice/rice/rice`
- Sóc Trăng: top-1 trước `seq_rice_fallow_cover_rice__early_standard_standard`, sau `seq_rice_fallow_cover_rice__early_standard_standard`; shortlist sau: `low_risk: rice/fallow_cover/rice`, `save_water: mungbean/rice/rice`, `soil_support: rice/peanut/rice`, `balanced: rice/maize/rice`, `salinity_avoidance: rice/rice/rice`

Cần Thơ/Châu Đốc giảm rõ ngày nóng khi đối chiếu ERA5; Sóc Trăng không tự tăng nóng để bù ô biển. Ngưỡng xung đột và hiệu chỉnh trung bình tháng là giả định nhóm, cần kiểm định độc lập. Việc chọn chuỗi có thể đổi vì R_HEAT/stress đổi; không gọi đó là giảm nước do hiệu chỉnh ET₀.
