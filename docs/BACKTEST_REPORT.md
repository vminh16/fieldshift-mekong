# Backtest 2016 / 2020 (hindcast có kiểm soát)

Sinh tự động bởi `scripts/backtest_2016.py`. Kế hoạch lập tại `as_of` chỉ dùng dữ liệu < as_of (engine ép AC-04; forecast mùa và CMIP6 tắt ở hindcast), horizon 3 vụ, ràng buộc mặc định. Sau đó baseline và từng phương án được mô phỏng lại bằng CÙNG mô hình nước FAO-56 trên thời tiết NASA POWER **thực** của các vụ đó. Hai cấu hình nước: `full` (tưới đủ) và `canal_limited` (trần 500 mm/vụ, để ngày thiếu nước có ý nghĩa).


## Cần Thơ (nội đồng) — as_of 2015-11-15 — nước `full`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **59 mm** (trung bình các năm trước 148 mm; khô hơn 93% số năm trước).
- Engine tại as_of: baseline `RECOMMEND_FOR_CONSIDERATION`; luật kích hoạt: R_HEAT, R_PEST_CYCLE; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1835 mm, năm hạn 2134 mm; thiếu nước 0 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1969 mm, thiếu nước 0 ngày, nóng 28 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | RECOMMEND_FOR_CONSIDERATION | 0 | 0 | 1969 | 0 | 139 | - |
| low_risk | soybean/rice/rice | CONDITIONAL_PENDING_CHECK | -694 | -722 | 1247 | +0.0 | 101 | có |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -823 | -864 | 1105 | +0.0 | 86 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -656 | -679 | 1290 | +0.0 | 116 | có |
| balanced | fallow_cover/rice/rice | RECOMMEND_FOR_CONSIDERATION | -946 | -1034 | 935 | +14.0 | 77 | KHÔNG |

## Cần Thơ (nội đồng) — as_of 2015-11-15 — nước `canal_limited`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **59 mm** (trung bình các năm trước 148 mm; khô hơn 93% số năm trước).
- Engine tại as_of: baseline `RECOMMEND_FOR_CONSIDERATION`; luật kích hoạt: R_HEAT, R_PEST_CYCLE, R_WATER_STRESS; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1294 mm, năm hạn 1367 mm; thiếu nước 93 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1254 mm, thiếu nước 63 ngày, nóng 28 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | RECOMMEND_FOR_CONSIDERATION | 0 | 0 | 1254 | 0 | 139 | - |
| low_risk | soybean/rice/rice | CONDITIONAL_PENDING_CHECK | -308 | -188 | 1067 | -50.0 | 101 | có |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -378 | -330 | 924 | -50.0 | 86 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -337 | -310 | 944 | -20.0 | 116 | có |
| balanced | fallow_cover/rice/rice | RECOMMEND_FOR_CONSIDERATION | -500 | -500 | 754 | -36.0 | 77 | có |

## Cần Thơ (nội đồng) — as_of 2019-11-15 — nước `full`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **134 mm** (trung bình các năm trước 181 mm; khô hơn 44% số năm trước).
- Engine tại as_of: baseline `RECOMMEND_FOR_CONSIDERATION`; luật kích hoạt: R_HEAT, R_PEST_CYCLE; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1835 mm, năm hạn 2134 mm; thiếu nước 0 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1810 mm, thiếu nước 0 ngày, nóng 22 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | RECOMMEND_FOR_CONSIDERATION | 0 | 0 | 1810 | 0 | 139 | - |
| low_risk | soybean/rice/rice | CONDITIONAL_PENDING_CHECK | -694 | -696 | 1114 | +0.0 | 101 | có |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -832 | -833 | 977 | +0.0 | 86 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -656 | -581 | 1230 | +0.0 | 116 | có |
| balanced | fallow_cover/rice/rice | RECOMMEND_FOR_CONSIDERATION | -946 | -1005 | 805 | +32.0 | 77 | KHÔNG |

## Cần Thơ (nội đồng) — as_of 2019-11-15 — nước `canal_limited`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **134 mm** (trung bình các năm trước 181 mm; khô hơn 44% số năm trước).
- Engine tại as_of: baseline `RECOMMEND_FOR_CONSIDERATION`; luật kích hoạt: R_HEAT, R_PEST_CYCLE, R_WATER_STRESS; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1280 mm, năm hạn 1367 mm; thiếu nước 93 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1256 mm, thiếu nước 49 ngày, nóng 22 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | RECOMMEND_FOR_CONSIDERATION | 0 | 0 | 1256 | 0 | 139 | - |
| low_risk | soybean/rice/rice | CONDITIONAL_PENDING_CHECK | -294 | -191 | 1065 | -49.0 | 101 | có |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -371 | -328 | 928 | -49.0 | 86 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -336 | -352 | 904 | -4.0 | 116 | có |
| balanced | fallow_cover/rice/rice | RECOMMEND_FOR_CONSIDERATION | -500 | -500 | 756 | -17.0 | 77 | có |

## Sóc Trăng (ven biển) — as_of 2015-11-15 — nước `full`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **64 mm** (trung bình các năm trước 181 mm; khô hơn 100% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1625 mm, năm hạn 1875 mm; thiếu nước 0 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1825 mm, thiếu nước 0 ngày, nóng 0 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1825 | 0 | 139 | - |
| low_risk | fallow_cover/rice/rice | CONDITIONAL_PENDING_CHECK | -877 | -934 | 892 | +11.0 | 77 | KHÔNG |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -767 | -766 | 1059 | +0.0 | 86 | có |
| soil_support | soybean/rice/rice | CONDITIONAL_PENDING_CHECK | -680 | -682 | 1143 | +0.0 | 101 | có |
| balanced | rice/soybean/rice | CONDITIONAL_PENDING_CHECK | -528 | -560 | 1265 | +0.0 | 116 | có |

## Sóc Trăng (ven biển) — as_of 2015-11-15 — nước `canal_limited`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **64 mm** (trung bình các năm trước 181 mm; khô hơn 100% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN, R_WATER_STRESS; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1226 mm, năm hạn 1284 mm; thiếu nước 72 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1254 mm, thiếu nước 57 ngày, nóng 0 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1254 | 0 | 139 | - |
| low_risk | fallow_cover/rice/rice | CONDITIONAL_PENDING_CHECK | -500 | -500 | 754 | -37.0 | 77 | có |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -368 | -332 | 922 | -48.0 | 86 | có |
| soil_support | rice/soybean/rice | CONDITIONAL_PENDING_CHECK | -364 | -278 | 976 | -16.0 | 116 | có |
| balanced | soybean/rice/rice | CONDITIONAL_PENDING_CHECK | -281 | -248 | 1006 | -48.0 | 101 | có |

## Sóc Trăng (ven biển) — as_of 2019-11-15 — nước `full`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **97 mm** (trung bình các năm trước 197 mm; khô hơn 89% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1625 mm, năm hạn 1875 mm; thiếu nước 0 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1782 mm, thiếu nước 0 ngày, nóng 0 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1782 | 0 | 139 | - |
| low_risk | fallow_cover/rice/rice | CONDITIONAL_PENDING_CHECK | -877 | -943 | 840 | +35.0 | 77 | KHÔNG |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -767 | -720 | 1063 | +0.0 | 86 | có |
| soil_support | soybean/rice/rice | CONDITIONAL_PENDING_CHECK | -680 | -641 | 1142 | +0.0 | 101 | có |

## Sóc Trăng (ven biển) — as_of 2019-11-15 — nước `canal_limited`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **97 mm** (trung bình các năm trước 197 mm; khô hơn 89% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN, R_WATER_STRESS; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1226 mm, năm hạn 1284 mm; thiếu nước 72 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1257 mm, thiếu nước 57 ngày, nóng 0 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1257 | 0 | 139 | - |
| low_risk | fallow_cover/rice/rice | CONDITIONAL_PENDING_CHECK | -500 | -500 | 757 | -14.0 | 77 | có |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -368 | -277 | 981 | -49.0 | 86 | có |
| soil_support | rice/soybean/rice | CONDITIONAL_PENDING_CHECK | -364 | -322 | 936 | -9.0 | 116 | có |
| balanced | soybean/rice/rice | CONDITIONAL_PENDING_CHECK | -281 | -198 | 1059 | -49.0 | 101 | có |

## Bến Tre (ven biển) — as_of 2015-11-15 — nước `full`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **73 mm** (trung bình các năm trước 159 mm; khô hơn 93% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1696 mm, năm hạn 1962 mm; thiếu nước 0 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1943 mm, thiếu nước 0 ngày, nóng 2 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1943 | 0 | 139 | - |
| low_risk | fallow_cover/rice/rice | CONDITIONAL_PENDING_CHECK | -895 | -994 | 950 | +9.0 | 77 | KHÔNG |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -783 | -821 | 1123 | +0.0 | 86 | có |
| soil_support | soybean/rice/rice | CONDITIONAL_PENDING_CHECK | -677 | -687 | 1256 | +0.0 | 101 | có |

## Bến Tre (ven biển) — as_of 2015-11-15 — nước `canal_limited`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **73 mm** (trung bình các năm trước 159 mm; khô hơn 93% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN, R_WATER_STRESS; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1225 mm, năm hạn 1336 mm; thiếu nước 76 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1283 mm, thiếu nước 59 ngày, nóng 2 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1283 | 0 | 139 | - |
| low_risk | fallow_cover/rice/rice | CONDITIONAL_PENDING_CHECK | -500 | -500 | 783 | -39.0 | 77 | có |
| save_water | rice/maize/rice | CONDITIONAL_PENDING_CHECK | -374 | -283 | 1000 | -18.0 | 116 | có |
| soil_support | rice/soybean/rice | CONDITIONAL_PENDING_CHECK | -327 | -283 | 1000 | -18.0 | 116 | có |
| balanced | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -353 | -327 | 956 | -48.0 | 86 | có |

## Bến Tre (ven biển) — as_of 2019-11-15 — nước `full`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **93 mm** (trung bình các năm trước 178 mm; khô hơn 78% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1696 mm, năm hạn 1962 mm; thiếu nước 0 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1811 mm, thiếu nước 0 ngày, nóng 2 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1811 | 0 | 139 | - |
| low_risk | fallow_cover/rice/rice | CONDITIONAL_PENDING_CHECK | -895 | -991 | 820 | +34.0 | 77 | KHÔNG |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -783 | -766 | 1045 | +0.0 | 86 | có |
| soil_support | soybean/rice/rice | CONDITIONAL_PENDING_CHECK | -679 | -693 | 1118 | +0.0 | 101 | có |

## Bến Tre (ven biển) — as_of 2019-11-15 — nước `canal_limited`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **93 mm** (trung bình các năm trước 178 mm; khô hơn 78% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN, R_WATER_STRESS; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1225 mm, năm hạn 1336 mm; thiếu nước 76 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1255 mm, thiếu nước 55 ngày, nóng 2 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1255 | 0 | 139 | - |
| low_risk | fallow_cover/rice/rice | CONDITIONAL_PENDING_CHECK | -500 | -500 | 755 | -16.0 | 77 | có |
| save_water | rice/maize/rice | CONDITIONAL_PENDING_CHECK | -374 | -346 | 908 | -8.0 | 116 | có |
| soil_support | rice/soybean/rice | CONDITIONAL_PENDING_CHECK | -327 | -320 | 935 | -8.0 | 116 | có |
| balanced | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -353 | -275 | 980 | -50.0 | 86 | có |

## Kết luận (số liệu, không tô vẽ)

- Phương án tốt hơn baseline TRONG năm thực (tưới ít hơn và thiếu nước không nhiều hơn, ít nhất một chiều nghiêm ngặt): **39/45**.
- Dấu của Δtưới dự kiến trùng với Δtưới thực: **45/45** phương án (trung vị nhiều năm so với một năm thực; chủ yếu do màu cạn dùng ít nước hơn lúa trong mô hình).
- Phương án KHÔNG tốt hơn baseline (6): Cần Thơ (nội đồng) 2015 full balanced; Cần Thơ (nội đồng) 2019 full balanced; Sóc Trăng (ven biển) 2015 full low_risk; Sóc Trăng (ven biển) 2019 full low_risk; Bến Tre (ven biển) 2015 full low_risk; Bến Tre (ven biển) 2019 full low_risk. Trong mô hình, `fallow_cover` không được tưới nên tăng số ngày thiếu nước khi tưới đủ.
- Cờ rủi ro của engine tại as_of GIỐNG HỆT nhau giữa năm 2015 (mùa khô thực rất khô) và 2019 ở **6/6** cặp (điểm × cấu hình nước). Hindcast không có forecast mùa nên engine chỉ có khí hậu nhiều năm: nó không phân biệt được năm cực khô với năm thường tại thời điểm lập kế hoạch.
- Cờ mặn R_SALINITY* trên baseline: 8/12 ca (đúng các ca ven biển; luôn bật vì lúa trùng mùa mặn điển hình, không dựa vào năm thực). Không có quan trắc để biết năm đó mặn thật hay không.
- Điều backtest KHÔNG chứng minh: lợi ích về năng suất/thu nhập (mô hình chưa hiệu chỉnh, gate G7) hay giảm thiệt hại do mặn. 'Tốt hơn' ở đây chỉ nghĩa là tiết kiệm nước tưới theo mô hình FAO-56 của chính engine.

## Hạn chế

- Không có quan trắc độ mặn/ECw: không thể chấm rủi ro mặn thật; chỉ so mức trùng cửa sổ mùa mặn điển hình (logic engine).
- NASA POWER là lưới ~50 km (có thể lẫn biển ở ô ven biển); mưa/ET0 không phải đo tại ruộng.
- Chấm điểm dùng chính mô hình nước FAO-56 của engine (chưa hiệu chỉnh, G7): đây là nhất quán nội bộ, KHÔNG phải kiểm chứng với năng suất/nước tưới đo thực.
- Một năm thực cho mỗi điểm: không có ý nghĩa thống kê; hai as_of × ba điểm × hai cấu hình là các ca không độc lập.
- Trần tưới `canal_limited` 500 mm/vụ là giả định mặc định của engine, không phải số đo.

