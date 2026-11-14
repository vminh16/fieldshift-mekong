# Báo cáo độ nhạy (sensitivity)

Sinh tự động bởi `scripts/sensitivity.py`. as_of `2026-11-14`, offline trên cache có sẵn, yêu cầu mặc định (horizon 3 vụ, ràng buộc mặc định, outlook CLIMATOLOGY+STRESS_TEST). Mỗi lần đổi MỘT tham số trong bộ nhớ.

- **Top-1**: phương án đầu tiên trong `options` (thứ tự theo ưu tiên mặc định) so với tham chiếu.
- **Jaccard**: |giao|/|hợp| của tập `sequence_id` trong shortlist so với tham chiếu.
- **Đổi status**: số chuỗi có mặt ở cả hai lần chạy nhưng `decision_status` đổi.
- **ΔIrr**: thay đổi % nhu cầu tưới của baseline (kịch bản khí hậu).
- **Cờ `cần nguồn`**: tham số mà tỷ lệ (ruộng × giá trị) đổi top-1 **hoặc** shortlist (Jaccard<1) > 20%, hoặc làm đổi nhu cầu tưới baseline > 20%.

Kiểm tra xác định: chạy tham chiếu 2 lần cho kết quả GIỐNG HỆT.

## Kết quả chi tiết

| Tham số | Giá trị | Ruộng | Top-1 giữ nguyên | Jaccard | Đổi status | ΔIrr baseline |
|---|---|---|---|---|---|---|
| Thấm paddy (mm/ngày) | 1 | Cần Thơ | có | 1.00 | 0 | -11.2% |
| Thấm paddy (mm/ngày) | 1 | Châu Đốc | có | 1.00 | 0 | -12.6% |
| Thấm paddy (mm/ngày) | 1 | Bến Tre | có | 1.00 | 0 | -13.2% |
| Thấm paddy (mm/ngày) | 1 | Sóc Trăng | có | 1.00 | 0 | -11.5% |
| Thấm paddy (mm/ngày) | 2 | Cần Thơ | có | 1.00 | 0 | +0.0% |
| Thấm paddy (mm/ngày) | 2 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| Thấm paddy (mm/ngày) | 2 | Bến Tre | có | 1.00 | 0 | +0.0% |
| Thấm paddy (mm/ngày) | 2 | Sóc Trăng | có | 1.00 | 0 | +0.0% |
| Thấm paddy (mm/ngày) | 5 | Cần Thơ | có | 1.00 | 0 | +41.2% |
| Thấm paddy (mm/ngày) | 5 | Châu Đốc | có | 1.00 | 0 | +46.2% |
| Thấm paddy (mm/ngày) | 5 | Bến Tre | có | 1.00 | 0 | +42.4% |
| Thấm paddy (mm/ngày) | 5 | Sóc Trăng | có | 1.00 | 0 | +46.3% |
| TAW đất (mm/m) | 120 | Cần Thơ | có | 0.75 | 0 | +0.0% |
| TAW đất (mm/m) | 120 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| TAW đất (mm/m) | 120 | Bến Tre | có | 1.00 | 0 | +0.0% |
| TAW đất (mm/m) | 120 | Sóc Trăng | có | 1.00 | 0 | +0.0% |
| TAW đất (mm/m) | 150 | Cần Thơ | có | 1.00 | 0 | +0.0% |
| TAW đất (mm/m) | 150 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| TAW đất (mm/m) | 150 | Bến Tre | có | 1.00 | 0 | +0.0% |
| TAW đất (mm/m) | 150 | Sóc Trăng | có | 1.00 | 0 | +0.0% |
| TAW đất (mm/m) | 200 | Cần Thơ | có | 1.00 | 0 | +0.0% |
| TAW đất (mm/m) | 200 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| TAW đất (mm/m) | 200 | Bến Tre | có | 1.00 | 0 | +0.0% |
| TAW đất (mm/m) | 200 | Sóc Trăng | có | 0.75 | 0 | +0.0% |
| Kc mọi cây | ×0.9 | Cần Thơ | có | 1.00 | 0 | -6.9% |
| Kc mọi cây | ×0.9 | Châu Đốc | có | 1.00 | 0 | -7.7% |
| Kc mọi cây | ×0.9 | Bến Tre | có | 1.00 | 0 | -7.2% |
| Kc mọi cây | ×0.9 | Sóc Trăng | có | 1.00 | 0 | -6.1% |
| Kc mọi cây | ×1.0 | Cần Thơ | có | 1.00 | 0 | +0.0% |
| Kc mọi cây | ×1.0 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| Kc mọi cây | ×1.0 | Bến Tre | có | 1.00 | 0 | +0.0% |
| Kc mọi cây | ×1.0 | Sóc Trăng | có | 1.00 | 0 | +0.0% |
| Kc mọi cây | ×1.1 | Cần Thơ | có | 1.00 | 0 | +7.6% |
| Kc mọi cây | ×1.1 | Châu Đốc | có | 1.00 | 0 | +5.7% |
| Kc mọi cây | ×1.1 | Bến Tre | có | 1.00 | 0 | +6.2% |
| Kc mọi cây | ×1.1 | Sóc Trăng | có | 1.00 | 0 | +8.2% |
| Ngưỡng ngày nóng (R_HEAT) | 3 | Cần Thơ | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày nóng (R_HEAT) | 3 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày nóng (R_HEAT) | 3 | Bến Tre | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày nóng (R_HEAT) | 3 | Sóc Trăng | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày nóng (R_HEAT) | 5 | Cần Thơ | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày nóng (R_HEAT) | 5 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày nóng (R_HEAT) | 5 | Bến Tre | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày nóng (R_HEAT) | 5 | Sóc Trăng | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày nóng (R_HEAT) | 10 | Cần Thơ | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày nóng (R_HEAT) | 10 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày nóng (R_HEAT) | 10 | Bến Tre | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày nóng (R_HEAT) | 10 | Sóc Trăng | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày thiếu nước (R_WATER_STRESS) | 5 | Cần Thơ | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày thiếu nước (R_WATER_STRESS) | 5 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày thiếu nước (R_WATER_STRESS) | 5 | Bến Tre | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày thiếu nước (R_WATER_STRESS) | 5 | Sóc Trăng | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày thiếu nước (R_WATER_STRESS) | 7 | Cần Thơ | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày thiếu nước (R_WATER_STRESS) | 7 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày thiếu nước (R_WATER_STRESS) | 7 | Bến Tre | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày thiếu nước (R_WATER_STRESS) | 7 | Sóc Trăng | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày thiếu nước (R_WATER_STRESS) | 14 | Cần Thơ | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày thiếu nước (R_WATER_STRESS) | 14 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày thiếu nước (R_WATER_STRESS) | 14 | Bến Tre | có | 1.00 | 0 | +0.0% |
| Ngưỡng ngày thiếu nước (R_WATER_STRESS) | 14 | Sóc Trăng | có | 1.00 | 0 | +0.0% |
| Ngưỡng mưa úng (mm/vụ) | 400 | Cần Thơ | có | 1.00 | 0 | +0.0% |
| Ngưỡng mưa úng (mm/vụ) | 400 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| Ngưỡng mưa úng (mm/vụ) | 400 | Bến Tre | có | 1.00 | 0 | +0.0% |
| Ngưỡng mưa úng (mm/vụ) | 400 | Sóc Trăng | có | 1.00 | 0 | +0.0% |
| Ngưỡng mưa úng (mm/vụ) | 600 | Cần Thơ | có | 1.00 | 0 | +0.0% |
| Ngưỡng mưa úng (mm/vụ) | 600 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| Ngưỡng mưa úng (mm/vụ) | 600 | Bến Tre | có | 1.00 | 0 | +0.0% |
| Ngưỡng mưa úng (mm/vụ) | 600 | Sóc Trăng | có | 1.00 | 0 | +0.0% |
| Ngưỡng mưa úng (mm/vụ) | 800 | Cần Thơ | có | 1.00 | 0 | +0.0% |
| Ngưỡng mưa úng (mm/vụ) | 800 | Châu Đốc | có | 1.00 | 0 | +0.0% |
| Ngưỡng mưa úng (mm/vụ) | 800 | Bến Tre | có | 1.00 | 0 | +0.0% |
| Ngưỡng mưa úng (mm/vụ) | 800 | Sóc Trăng | có | 1.00 | 0 | +0.0% |

## Tóm tắt theo tham số

| Tham số | Số ca | Đổi top-1 | Đổi shortlist | Đổi status | Max abs ΔIrr baseline | Kết luận |
|---|---|---|---|---|---|---|
| Thấm paddy (mm/ngày) | 12 | 0% | 0% | 0% | 46.3% | thứ hạng ổn định; **cần nguồn** (độ lớn nhu cầu tưới đổi > 20%) |
| TAW đất (mm/m) | 12 | 0% | 17% | 0% | 0.0% | thứ hạng ổn định |
| Kc mọi cây | 12 | 0% | 0% | 0% | 8.2% | thứ hạng ổn định |
| Ngưỡng ngày nóng (R_HEAT) | 12 | 0% | 0% | 0% | 0.0% | thứ hạng ổn định |
| Ngưỡng ngày thiếu nước (R_WATER_STRESS) | 12 | 0% | 0% | 0% | 0.0% | thứ hạng ổn định |
| Ngưỡng mưa úng (mm/vụ) | 12 | 0% | 0% | 0% | 0.0% | thứ hạng ổn định |

## Kết luận

- Tham số làm đổi kết quả > 20%: không có.
- Tham số làm đổi độ lớn nhu cầu tưới baseline > 20% (số tuyệt đối không nên trích như đo đạc): Thấm paddy (mm/ngày).
- Mẫu nhỏ: 4 ruộng demo, 1 ngày as_of, 1 yêu cầu mặc định; đây là kiểm tra độ nhạy, không phải xác nhận mô hình.
