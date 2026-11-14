# Luật, ngưỡng và nguồn của FieldShift-Mekong

> Tệp này được SINH TỰ ĐỘNG bởi `scripts/export_rules.py` (không sửa tay). Phân loại: **[A] tài liệu khoa học** = có trích dẫn; **[B] heuristic nhóm tự đặt** = ngưỡng/giá trị nhóm tự đặt, chưa có nguồn; **[C] trống/không hoạt động** = tham số trống hoặc luật không bao giờ kích hoạt.

## 1. Luật của engine (parse từ `rotation_planner.py`)

| Rule | Mức | Điều kiện | Phân loại | Nguồn / ghi chú |
|---|---|---|---|---|
| R_WINDOW | HARD | Cây không thuộc lịch vụ của vùng (crops.allowed_windows) | [A] tài liệu khoa học | lịch MARD/Cục Trồng trọt (regions.json) |
| R_SEASON_OVERLAP | HARD | Thu hoạch + thời gian làm đất > ngày gieo vụ sau | [A] tài liệu khoa học | lịch vụ MARD; turnaround 10 ngày là giá trị vùng |
| R_UPSTREAM_DISCHARGE_LOW | SOFT | Vùng ven biển + lưu lượng thượng nguồn thấp hơn nền cùng lịch | [B] heuristic nhóm tự đặt | GloFAS là tín hiệu vùng, không phải mặn |
| R_DRAINAGE | HARD | Cây cạn cần thoát nước tốt nhưng nông dân báo thoát nước kém | [B] heuristic nhóm tự đặt | crops.requires_good_drainage do nhóm gán |
| R_DRAINAGE_UNKNOWN | UNKNOWN_REQUIRES_CHECK | Cây cạn cần thoát nước tốt, chưa xác nhận | [B] heuristic nhóm tự đặt | - |
| R_SALINITY_UNKNOWN | UNKNOWN_REQUIRES_CHECK | Vụ trùng mùa mặn >= SALINITY_OVERLAP_DAYS ngày (tính cả mặn đến sớm SALINITY_EARLY_WEEKS tuần), chưa đo ECw | [B] heuristic nhóm tự đặt | ngưỡng ngày và 4 tuần do nhóm đặt; mùa mặn từ MARD/SIWRP |
| R_SALINITY | SOFT | ECw đo được > ngưỡng ECw của cây (ECe≈1,5·ECw) | [A] tài liệu khoa học | FAO-29 / Maas-Hoffman 1977 |
| R_HEAT | SOFT | Số ngày Tmax >= ngưỡng ở giai đoạn nhạy cảm (trung vị) >= HEAT_STRESS_DAYS_SOFT | [B] heuristic nhóm tự đặt | ngưỡng Tmax theo cây: xem bảng cây; ngưỡng ngày do nhóm đặt |
| R_WATER_STRESS | SOFT | Số ngày thiếu nước (trung vị) >= WATER_STRESS_DAYS_SOFT | [B] heuristic nhóm tự đặt | ngưỡng ngày do nhóm đặt |
| R_WATERLOG | SOFT | Cây cạn chịu úng kém và mưa trung vị trong vụ >= WATERLOG_RAIN_MM | [B] heuristic nhóm tự đặt | ngưỡng mm do nhóm đặt |
| R_MACHINERY | HARD | Cây cần máy (crops.machinery_required) khi no_new_machinery=True | [C] trống/không hoạt động | KHÔNG HOẠT ĐỘNG: machinery_required rỗng ở mọi cây -> luật HARD không bao giờ bắn (AC-07 chỉ test trên catalog giả lập) |
| R_BUDGET | SOFT | Cây chi phí 'high' khi budget_level='low' | [B] heuristic nhóm tự đặt | relative_cost_level do nhóm gán |
| R_PEST_CYCLE | SOFT | Lúa liên tục các vụ (lợi ích luân canh định tính) | [B] heuristic nhóm tự đặt | định tính, không có số |

## 2. Hằng số module

| Tên | Giá trị | Vị trí | Phân loại | Ý nghĩa |
|---|---|---|---|---|
| DEFAULT_CANAL_CAP_MM | 500.0 | hằng số module | [B] heuristic nhóm tự đặt | Trần tưới mỗi vụ cho 'canal_limited' (mm), giả định |
| PPT_PER_DS_M | 0.64 | hằng số module | [A] tài liệu khoa học | TDS ≈ 640·ECw (FAO-29) -> ‰ |
| SCREENING_SCENARIOS | ['sc_clim', 'sc_dry'] | hằng số module | [B] heuristic nhóm tự đặt | Kịch bản dùng để sàng lọc |
| HEAT_STRESS_DAYS_SOFT | 5 | hằng số module | [B] heuristic nhóm tự đặt | R_HEAT: ngày |
| WATER_STRESS_DAYS_SOFT | 7 | hằng số module | [B] heuristic nhóm tự đặt | R_WATER_STRESS: ngày |
| WATERLOG_RAIN_MM | 600 | hằng số module | [B] heuristic nhóm tự đặt | R_WATERLOG: mm mưa/vụ |
| SALINITY_OVERLAP_DAYS | 7 | hằng số module | [B] heuristic nhóm tự đặt | R_SALINITY*: ngày trùng mùa mặn |
| SALINITY_EARLY_WEEKS | -4 | hằng số module | [B] heuristic nhóm tự đặt | R_SALINITY*: mặn đến sớm (tuần, âm = sớm) |

## 3. Tham số cây trồng (`crops.json` crops-2026.11.0)

| Cây | Kc ini/mid/end | Mặn ECe ngưỡng, độ dốc; ECw | Ngưỡng Tmax | Thời gian ngày min/typ/max | Cửa sổ | Máy móc |
|---|---|---|---|---|---|---|
| rice | 1.05/1.2/0.75 [A] | 3.0 dS/m, 12%/dS/m; ECw 2.0 [A] | 35 °C [A] | 90/100/110 [A] | dong_xuan, xuan_he, thu_dong [A] | rỗng [C] |
| maize | 0.3/1.2/0.6 [A] | 1.7 dS/m, 12%/dS/m; ECw 1.13 [A] | 35 °C [B] | 85/95/110 [B] | dong_xuan, xuan_he [B] | rỗng [C] |
| soybean | 0.4/1.15/0.5 [A] | 5.0 dS/m, 20%/dS/m; ECw 3.33 [A] | 35 °C [B] | 75/85/100 [B] | dong_xuan, xuan_he [B] | rỗng [C] |
| mungbean | 0.4/1.05/0.35 [A] | 1.8 dS/m, 20%/dS/m; ECw 1.2 [B] | 35 °C [B] | 60/70/80 [B] | dong_xuan, xuan_he [B] | rỗng [C] |
| sesame | 0.35/1.1/0.25 [A] | 2.5 dS/m, 15%/dS/m; ECw 1.67 [B] | 36 °C [B] | 75/90/100 [B] | dong_xuan, xuan_he [B] | rỗng [C] |
| peanut | 0.4/1.15/0.6 [A] | 3.2 dS/m, 29%/dS/m; ECw 2.13 [A] | 35 °C [B] | 90/100/115 [B] | dong_xuan, xuan_he [B] | rỗng [C] |
| watermelon | 0.4/1.0/0.75 [A] | 2.2 dS/m, 16%/dS/m; ECw 1.47 [B] | 35 °C [B] | 75/85/95 [B] | dong_xuan, xuan_he [B] | rỗng [C] |
| fallow_cover | 0.3/0.4/0.3 [B] | 99.0 dS/m, 0.0%/dS/m; ECw 66.0 [C] | 45 °C [C] | 30/60/90 [B] | dong_xuan, xuan_he, thu_dong [B] | rỗng [C] |

Mã trong ô: [A]/[B]/[C] như trên.

### Nguồn và hạn chế theo cây

- **rice** — nguồn: FAO-56 Table 12 (Kc), Table 22 (root depth, p); FAO-29 Table (rice ECe 3.0, 12%/dS/m); Maas & Hoffman 1977; Mekong short-duration varieties OM5451/OM18 (SIAP/MARD, ~90-105 d). Hạn chế: Stage lengths are a short-duration Mekong variety split, not FAO-56 long-season values. | Kc end 0.75 is a mid-value of FAO-56 range 0.90-0.60 (depends on drain-down timing). | Rice is most salt-sensitive at seedling and flowering; a single seasonal threshold overstates tolerance there. | Root depth is FAO-56 shallow-puddled soil value; p=0.20 is only relevant if not ponded. | ecw_threshold_ds_m approximated as ECe/1.5 (FAO-29 convention ECe ~ 1.5 ECw); salinity values are Maas-Hoffman steady-state, not Mekong-calibrated.
- **maize** — nguồn: FAO-56 Table 12 (Kc), Table 22 (root depth, p); FAO-29 / Maas-Hoffman (maize ECe 1.7, 12%); FAO-33 maize yield response Ky ~1.25. Hạn chế: Kc end 0.60 is for grain harvested at high moisture; 0.35 if field-dried. | Duration is typical hybrid in the Mekong, regional estimate. | Very sensitive to waterlogging; needs raised beds in clay soil. | ecw_threshold_ds_m approximated as ECe/1.5 (FAO-29 convention ECe ~ 1.5 ECw); salinity values are Maas-Hoffman steady-state, not Mekong-calibrated.
- **soybean** — nguồn: FAO-56 Table 12 (Kc), Table 22 (root depth, p); FAO-29 / Maas-Hoffman (soybean ECe 5.0, 20%); FAO-33. Hạn chế: Stage lengths scaled from FAO-56 130-day values to a short Mekong cultivar (estimate). | Root max 0.8 m limited by shallow Mekong water table, below FAO-56 1.3 m. | Maas-Hoffman threshold 5.0 is for mature plants; germination is more sensitive. | ecw_threshold_ds_m approximated as ECe/1.5 (FAO-29 convention ECe ~ 1.5 ECw); salinity values are Maas-Hoffman steady-state, not Mekong-calibrated.
- **mungbean** — nguồn: FAO-56 Table 12 (pulses/green gram), Table 22; Maas-Hoffman 1977 (mungbean sensitive, estimate); FAO-33. Hạn chế: Salinity threshold 1.8 dS/m is a best-estimate from mungbean/cowpea literature, not a measured Mekong value. | Kc mid 1.05 is within FAO-56 pulses range; no mungbean-specific entry. | Stage lengths are regional estimates. | ecw_threshold_ds_m approximated as ECe/1.5 (FAO-29 convention ECe ~ 1.5 ECw); salinity values are Maas-Hoffman steady-state, not Mekong-calibrated.
- **sesame** — nguồn: FAO-56 Table 12 (sesame Kc 0.35/1.10/0.25), Table 22; AquaCrop/FAO-33 oilcrop data; FAO-29 (sesame sensitive at germination). Hạn chế: Salinity threshold 2.5 dS/m and slope 15 are uncertain best estimates, not Maas-Hoffman listed values. | Very intolerant of waterlogging; unsuitable on poorly drained clay. | Stage lengths are regional estimates. | ecw_threshold_ds_m approximated as ECe/1.5 (FAO-29 convention ECe ~ 1.5 ECw); salinity values are Maas-Hoffman steady-state, not Mekong-calibrated.
- **peanut** — nguồn: FAO-56 Table 12 (Kc), Table 22 (root depth, p) (groundnut); Maas & Hoffman 1977 (peanut ECe 3.2, 29%); FAO-33. Hạn chế: Stage lengths scaled from FAO-56 130-day groundnut to ~100 days (estimate). | Sensitive to waterlogging at pod filling; needs sandy-loam or raised bed. | Kc end 0.60 assumes harvest at moderate moisture. | ecw_threshold_ds_m approximated as ECe/1.5 (FAO-29 convention ECe ~ 1.5 ECw); salinity values are Maas-Hoffman steady-state, not Mekong-calibrated.
- **watermelon** — nguồn: FAO-56 Table 12 (Kc), Table 22 (root depth, p) (watermelon); Maas & Hoffman 1977 (watermelon ECe 2.2, 16%); FAO-33. Hạn chế: Rooting depth 0.8-1.5 m exceeds usable Mekong depth with high water table; real effective depth likely lower. | Highly susceptible to waterlogging and soil-borne disease, needs raised beds. | Salinity values are lower-confidence (limited trials). | ecw_threshold_ds_m approximated as ECe/1.5 (FAO-29 convention ECe ~ 1.5 ECw); salinity values are Maas-Hoffman steady-state, not Mekong-calibrated.
- **fallow_cover** — nguồn: FAO-56 Table 12 (bare soil/ground cover Kc 0.15-0.5); FAO-56 Table 22 (generic p 0.5). Hạn chế: Salinity: not applicable, values are placeholders (tolerance T, threshold 99) so salinity penalty is zero. | Kc ~0.3-0.4 is a mid-value for sparse cover/weeds, not a specific species. | Duration and stages are nominal; farmer-set. | ecw_threshold_ds_m approximated as ECe/1.5 (FAO-29 convention ECe ~ 1.5 ECw); salinity values are Maas-Hoffman steady-state, not Mekong-calibrated.

## 4. Giá trị vùng (`regions.json` regions-2026.11.0)

| Vùng | Tham số | Giá trị | Phân loại | Nguồn | Hạn chế |
|---|---|---|---|---|---|
| mekong | Cửa sổ vụ | dong_xuan 11-15→12-31; xuan_he 03-01→04-30; thu_dong 07-01→08-31 | [A] tài liệu khoa học | MARD/Cuc Trong trot cropping calendars for Mekong Delta (Đông Xuân Nov-Dec, Hè Thu Mar-May, Thu Đông Jul-Aug) | Windows are widened to guarantee a 3-crop rice sequence: latest sowing + 110 d + 10 d turnaround fits the next window's end; actual local calendars vary by province and flood/salinity status. / Upland crops in Hè Thu face rain onset in May; their duration must be checked per sowing date. |
| mekong | min_turnaround_days | 10 | [A] tài liệu khoa học | MARD/Cuc Trong trot cropping calendars for Mekong Delta (Đông Xuân Nov-Dec, Hè Thu Mar-May, Thu Đông Jul-Aug) | Windows are widened to guarantee a 3-crop rice sequence: latest sowing + 110 d + 10 d turnaround fits the next window's end; actual local calendars vary by province and flood/salinity status. / Upland crops in Hè Thu face rain onset in May; their duration must be checked per sowing date. |
| mekong | Paddy: thấm / làm đất / ponding | 2.0 mm/ngày / 200 mm / 50-100 mm | [A] tài liệu khoa học | FAO-56 section on rice (land prep ~200 mm, ponding 50-100 mm); FAO Irrigation Paper 33/IRRI: percolation 1-5 mm/d on heavy clay; Mekong alluvial paddy studies (Can Tho Univ.) | Percolation 2 mm/day is a mid value for heavy clay; varies 1-5 mm/day by soil and water table. / Land prep 200 mm is the FAO-56 standard, not locally measured. / Ponding depths are agronomic guidance, not field-specific. |
| mekong | Đất: TAW / pH / kết cấu | 150.0 mm/m / [4.5, 6.5] / clay | [A] tài liệu khoa học | FAO-56 Table 19 (clay TAW 120-200 mm/m); Vietnamese Mekong soil surveys (SIWRP / Can Tho Univ.) | Regional prior only; replace with field soil data when available. / TAW 150 mm/m is a mid value; acid sulfate soils have pH down to ~3.5-4.5. |
| mekong | Mùa mặn: đầu / đỉnh / cuối | 01-15 / 04-15 / 06-15 | [A] tài liệu khoa học | MARD/SIWRP salinity intrusion reports 2016, 2020, 2024; MRC Mekong salinity intrusion studies | Dates are multi-year typical; actual onset and peak shift with El Nino years and upstream discharge. / Applies to coastal zones only; inland sites have negligible risk. |

---
Hash nội dung (sha256, 16 ký tự đầu, không gồm dòng này): `bff12d112befb85f`
