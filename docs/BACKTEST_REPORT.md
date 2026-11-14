# Backtest 2016 / 2020 (hindcast có kiểm soát)

Sinh tự động bởi `scripts/backtest_2016.py`. Kế hoạch lập tại `as_of` chỉ dùng dữ liệu < as_of (engine ép AC-04; forecast mùa và CMIP6 tắt ở hindcast), horizon 3 vụ, ràng buộc mặc định. Sau đó baseline và từng phương án được mô phỏng lại bằng CÙNG mô hình nước FAO-56 trên thời tiết NASA POWER **thực** của các vụ đó. Hai cấu hình nước: `full` (tưới đủ) và `canal_limited` (trần 500 mm/vụ, để ngày thiếu nước có ý nghĩa).


## Cần Thơ (nội đồng) — as_of 2015-11-15 — nước `full`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **59 mm** (trung bình các năm trước 148 mm; khô hơn 93% số năm trước).
- Engine tại as_of: baseline `RECOMMEND_FOR_CONSIDERATION`; luật kích hoạt: R_HEAT, R_PEST_CYCLE; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1835 mm, năm hạn 2134 mm; thiếu nước 0 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1969 mm, thiếu nước 0 ngày, nóng 28 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | RECOMMEND_FOR_CONSIDERATION | 0 | 0 | 1969 | 0 | 139 | - |
| low_risk | rice/maize/rice | CONDITIONAL_PENDING_CHECK | -592 | -659 | 1310 | +0.0 | 116 | có |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -832 | -864 | 1105 | +0.0 | 86 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -601 | -679 | 1290 | +0.0 | 116 | có |
| balanced | rice/sesame/rice | CONDITIONAL_PENDING_CHECK | -654 | -640 | 1329 | +0.0 | 116 | có |
| third_season_rest | rice/rice/fallow_cover | RECOMMEND_FOR_CONSIDERATION | -276 | -254 | 1715 | +0.0 | 139 | có |

## Cần Thơ (nội đồng) — as_of 2015-11-15 — nước `canal_limited`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **59 mm** (trung bình các năm trước 148 mm; khô hơn 93% số năm trước).
- Engine tại as_of: baseline `RECOMMEND_FOR_CONSIDERATION`; luật kích hoạt: R_HEAT, R_PEST_CYCLE, R_WATER_STRESS; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1294 mm, năm hạn 1367 mm; thiếu nước 93 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1254 mm, thiếu nước 63 ngày, nóng 28 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | RECOMMEND_FOR_CONSIDERATION | 0 | 0 | 1254 | 0 | 139 | - |
| low_risk | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -344 | -310 | 944 | -20.0 | 116 | có |
| save_water | rice/sesame/rice | CONDITIONAL_PENDING_CHECK | -422 | -262 | 992 | -12.0 | 139 | có |
| soil_support | rice/soybean/rice | CONDITIONAL_PENDING_CHECK | -363 | -224 | 1030 | -12.0 | 139 | có |
| balanced | rice/maize/rice | CONDITIONAL_PENDING_CHECK | -348 | -284 | 970 | -20.0 | 116 | có |
| third_season_rest | rice/rice/fallow_cover | RECOMMEND_FOR_CONSIDERATION | -294 | -254 | 1000 | +0.0 | 139 | có |

## Cần Thơ (nội đồng) — as_of 2019-11-15 — nước `full`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **134 mm** (trung bình các năm trước 181 mm; khô hơn 44% số năm trước).
- Engine tại as_of: baseline `RECOMMEND_FOR_CONSIDERATION`; luật kích hoạt: R_HEAT, R_PEST_CYCLE; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1835 mm, năm hạn 2134 mm; thiếu nước 0 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1810 mm, thiếu nước 0 ngày, nóng 22 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | RECOMMEND_FOR_CONSIDERATION | 0 | 0 | 1810 | 0 | 139 | - |
| low_risk | rice/maize/rice | CONDITIONAL_PENDING_CHECK | -592 | -572 | 1238 | +0.0 | 116 | có |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -832 | -833 | 977 | +0.0 | 86 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -601 | -581 | 1230 | +0.0 | 116 | có |
| balanced | rice/sesame/rice | CONDITIONAL_PENDING_CHECK | -654 | -557 | 1253 | +0.0 | 116 | có |
| third_season_rest | rice/rice/fallow_cover | RECOMMEND_FOR_CONSIDERATION | -276 | -256 | 1554 | +0.0 | 139 | có |

## Cần Thơ (nội đồng) — as_of 2019-11-15 — nước `canal_limited`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **134 mm** (trung bình các năm trước 181 mm; khô hơn 44% số năm trước).
- Engine tại as_of: baseline `RECOMMEND_FOR_CONSIDERATION`; luật kích hoạt: R_HEAT, R_PEST_CYCLE, R_WATER_STRESS; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1280 mm, năm hạn 1367 mm; thiếu nước 93 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1256 mm, thiếu nước 49 ngày, nóng 22 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | RECOMMEND_FOR_CONSIDERATION | 0 | 0 | 1256 | 0 | 139 | - |
| low_risk | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -338 | -352 | 904 | -4.0 | 116 | có |
| save_water | rice/sesame/rice | CONDITIONAL_PENDING_CHECK | -408 | -328 | 928 | +1.0 | 139 | KHÔNG |
| soil_support | rice/soybean/rice | CONDITIONAL_PENDING_CHECK | -349 | -316 | 940 | +1.0 | 139 | KHÔNG |
| balanced | rice/mungbean/rice | CONDITIONAL_PENDING_CHECK | -346 | -324 | 932 | -4.0 | 109 | có |
| third_season_rest | rice/rice/fallow_cover | RECOMMEND_FOR_CONSIDERATION | -280 | -256 | 1000 | +0.0 | 139 | có |

## Sóc Trăng (ven biển) — as_of 2015-11-15 — nước `full`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **64 mm** (trung bình các năm trước 181 mm; khô hơn 100% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1625 mm, năm hạn 1875 mm; thiếu nước 0 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1825 mm, thiếu nước 0 ngày, nóng 0 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1825 | 0 | 139 | - |
| low_risk | rice/fallow_cover/rice | CONDITIONAL_PENDING_CHECK | -596 | -718 | 1108 | +0.0 | 39 | có |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -767 | -766 | 1059 | +0.0 | 86 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -485 | -598 | 1227 | +0.0 | 116 | có |
| balanced | rice/maize/rice | CONDITIONAL_PENDING_CHECK | -509 | -572 | 1253 | +0.0 | 116 | có |
| salinity_avoidance | rice/rice/rice | CONDITIONAL_PENDING_CHECK | -97 | -80 | 1745 | +0.0 | 116 | có |

## Sóc Trăng (ven biển) — as_of 2015-11-15 — nước `canal_limited`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **64 mm** (trung bình các năm trước 181 mm; khô hơn 100% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN, R_WATER_STRESS; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1226 mm, năm hạn 1284 mm; thiếu nước 72 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1254 mm, thiếu nước 57 ngày, nóng 0 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1254 | 0 | 139 | - |
| low_risk | rice/fallow_cover/rice | CONDITIONAL_PENDING_CHECK | -448 | -497 | 757 | -17.0 | 39 | có |
| save_water | rice/soybean/rice | CONDITIONAL_PENDING_CHECK | -376 | -278 | 976 | -8.0 | 139 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -344 | -303 | 951 | -8.0 | 139 | có |
| balanced | rice/maize/rice | CONDITIONAL_PENDING_CHECK | -357 | -358 | 896 | -16.0 | 116 | có |
| salinity_avoidance | rice/rice/rice | CONDITIONAL_PENDING_CHECK | +0 | +0 | 1254 | -8.0 | 116 | có |

## Sóc Trăng (ven biển) — as_of 2019-11-15 — nước `full`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **97 mm** (trung bình các năm trước 197 mm; khô hơn 89% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1625 mm, năm hạn 1875 mm; thiếu nước 0 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1782 mm, thiếu nước 0 ngày, nóng 0 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1782 | 0 | 139 | - |
| low_risk | rice/fallow_cover/rice | CONDITIONAL_PENDING_CHECK | -596 | -602 | 1180 | +0.0 | 39 | có |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -767 | -720 | 1063 | +0.0 | 86 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -485 | -534 | 1249 | +0.0 | 116 | có |
| balanced | rice/maize/rice | CONDITIONAL_PENDING_CHECK | -509 | -524 | 1258 | +0.0 | 116 | có |
| salinity_avoidance | rice/rice/rice | CONDITIONAL_PENDING_CHECK | -97 | -20 | 1763 | +0.0 | 116 | có |

## Sóc Trăng (ven biển) — as_of 2019-11-15 — nước `canal_limited`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **97 mm** (trung bình các năm trước 197 mm; khô hơn 89% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN, R_WATER_STRESS; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1226 mm, năm hạn 1284 mm; thiếu nước 72 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1257 mm, thiếu nước 57 ngày, nóng 0 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1257 | 0 | 139 | - |
| low_risk | rice/fallow_cover/rice | CONDITIONAL_PENDING_CHECK | -451 | -446 | 811 | -10.0 | 39 | có |
| save_water | rice/soybean/rice | CONDITIONAL_PENDING_CHECK | -376 | -322 | 936 | -7.0 | 139 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -344 | -354 | 904 | -7.0 | 139 | có |
| balanced | rice/maize/rice | CONDITIONAL_PENDING_CHECK | -357 | -343 | 914 | -9.0 | 116 | có |
| salinity_avoidance | rice/rice/rice | CONDITIONAL_PENDING_CHECK | +0 | +0 | 1257 | -2.0 | 116 | có |

## Bến Tre (ven biển) — as_of 2015-11-15 — nước `full`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **73 mm** (trung bình các năm trước 159 mm; khô hơn 93% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1696 mm, năm hạn 1962 mm; thiếu nước 0 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1943 mm, thiếu nước 0 ngày, nóng 2 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1943 | 0 | 139 | - |
| low_risk | rice/fallow_cover/rice | CONDITIONAL_PENDING_CHECK | -643 | -792 | 1151 | +0.0 | 39 | có |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -783 | -821 | 1123 | +0.0 | 86 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -528 | -678 | 1265 | +0.0 | 116 | có |
| balanced | rice/maize/rice | CONDITIONAL_PENDING_CHECK | -548 | -647 | 1296 | +0.0 | 116 | có |
| salinity_avoidance | rice/rice/rice | CONDITIONAL_PENDING_CHECK | -120 | -125 | 1818 | +0.0 | 116 | có |

## Bến Tre (ven biển) — as_of 2015-11-15 — nước `canal_limited`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **73 mm** (trung bình các năm trước 159 mm; khô hơn 93% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN, R_WATER_STRESS; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1225 mm, năm hạn 1336 mm; thiếu nước 76 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1283 mm, thiếu nước 59 ngày, nóng 2 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1283 | 0 | 139 | - |
| low_risk | rice/fallow_cover/rice | CONDITIONAL_PENDING_CHECK | -443 | -504 | 779 | -19.0 | 39 | có |
| save_water | rice/maize/rice | CONDITIONAL_PENDING_CHECK | -390 | -283 | 1000 | -10.0 | 139 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -368 | -304 | 979 | -10.0 | 139 | có |
| balanced | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -353 | -327 | 956 | -48.0 | 86 | có |
| salinity_avoidance | rice/rice/rice | CONDITIONAL_PENDING_CHECK | +0 | +0 | 1283 | -8.0 | 116 | có |

## Bến Tre (ven biển) — as_of 2019-11-15 — nước `full`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **93 mm** (trung bình các năm trước 178 mm; khô hơn 78% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1696 mm, năm hạn 1962 mm; thiếu nước 0 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1811 mm, thiếu nước 0 ngày, nóng 2 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1811 | 0 | 139 | - |
| low_risk | rice/fallow_cover/rice | CONDITIONAL_PENDING_CHECK | -643 | -616 | 1196 | +0.0 | 39 | có |
| save_water | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -783 | -766 | 1045 | +0.0 | 86 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -528 | -548 | 1263 | +0.0 | 116 | có |
| balanced | rice/maize/rice | CONDITIONAL_PENDING_CHECK | -548 | -537 | 1274 | +0.0 | 116 | có |
| salinity_avoidance | rice/rice/rice | CONDITIONAL_PENDING_CHECK | -120 | -50 | 1761 | +0.0 | 116 | có |

## Bến Tre (ven biển) — as_of 2019-11-15 — nước `canal_limited`

- Mưa 15/11–30/4 thực của mùa khô sau as_of: **93 mm** (trung bình các năm trước 178 mm; khô hơn 78% số năm trước).
- Engine tại as_of: baseline `CONDITIONAL_PENDING_CHECK`; luật kích hoạt: R_PEST_CYCLE, R_SALINITY_UNKNOWN, R_WATER_STRESS; kịch bản: sc_clim, sc_dry, sc_hot, sc_rain_minus30, sc_salt_early, sc_wet_ref; cổng: G1=ok, G2=ok, G3=ok, G4=FAIL, G5=FAIL, G6=FAIL, G7=FAIL, G8=ok.
- Dự báo của engine (baseline): nhu cầu tưới năm thường 1225 mm, năm hạn 1336 mm; thiếu nước 76 ngày. **Thực tế** (mô phỏng thời tiết thực): tưới 1255 mm, thiếu nước 55 ngày, nóng 2 ngày.

| Phương án | Chuỗi cây | Status | Dự kiến Δtưới (mm) | Thực Δtưới (mm) | Thực tưới (mm) | Thực Δthiếu nước (ngày) | Ngày trùng mùa mặn | Tốt hơn baseline? |
|---|---|---|---|---|---|---|---|---|
| baseline | rice/rice/rice | CONDITIONAL_PENDING_CHECK | 0 | 0 | 1255 | 0 | 139 | - |
| low_risk | rice/fallow_cover/rice | CONDITIONAL_PENDING_CHECK | -446 | -496 | 759 | -9.0 | 39 | có |
| save_water | rice/maize/rice | CONDITIONAL_PENDING_CHECK | -390 | -346 | 908 | -4.0 | 139 | có |
| soil_support | rice/peanut/rice | CONDITIONAL_PENDING_CHECK | -368 | -354 | 901 | -4.0 | 139 | có |
| balanced | mungbean/rice/rice | CONDITIONAL_PENDING_CHECK | -353 | -275 | 980 | -50.0 | 86 | có |
| salinity_avoidance | rice/rice/rice | CONDITIONAL_PENDING_CHECK | +0 | +0 | 1255 | -4.0 | 116 | có |

## Kết luận (số liệu, không tô vẽ)

- Phương án tốt hơn baseline TRONG năm thực (tưới ít hơn và thiếu nước không nhiều hơn, ít nhất một chiều nghiêm ngặt): **58/60**.
- Dấu của Δtưới dự kiến trùng với Δtưới thực: **56/56** phương án (trung vị nhiều năm so với một năm thực; chủ yếu do màu cạn dùng ít nước hơn lúa trong mô hình).
- Phương án KHÔNG tốt hơn baseline (2): Cần Thơ (nội đồng) 2019 canal_limited save_water; Cần Thơ (nội đồng) 2019 canal_limited soil_support. Vụ `fallow_cover` không cộng ngày thiếu nước (đất trống khô không phải thiệt hại cây trồng).
- Cờ rủi ro của engine tại as_of GIỐNG HỆT nhau giữa năm 2015 (mùa khô thực rất khô) và 2019 ở **6/6** cặp (điểm × cấu hình nước). Hindcast không có forecast mùa nên engine chỉ có khí hậu nhiều năm: nó không phân biệt được năm cực khô với năm thường tại thời điểm lập kế hoạch.
- Cờ mặn R_SALINITY* trên baseline: 8/12 ca (đúng các ca ven biển; luôn bật vì lúa trùng mùa mặn điển hình, không dựa vào năm thực). Không có quan trắc để biết năm đó mặn thật hay không.
- Điều backtest KHÔNG chứng minh: lợi ích về năng suất/thu nhập (mô hình chưa hiệu chỉnh, gate G7) hay giảm thiệt hại do mặn. 'Tốt hơn' ở đây chỉ nghĩa là tiết kiệm nước tưới theo mô hình FAO-56 của chính engine.

## Hạn chế

- Không có quan trắc độ mặn/ECw: không thể chấm rủi ro mặn thật; chỉ so mức trùng cửa sổ mùa mặn điển hình (logic engine).
- NASA POWER là lưới ~50 km (có thể lẫn biển ở ô ven biển); mưa/ET0 không phải đo tại ruộng.
- Chấm điểm dùng chính mô hình nước FAO-56 của engine (chưa hiệu chỉnh, G7): đây là nhất quán nội bộ, KHÔNG phải kiểm chứng với năng suất/nước tưới đo thực.
- Một năm thực cho mỗi điểm: không có ý nghĩa thống kê; hai as_of × ba điểm × hai cấu hình là các ca không độc lập.
- Trần tưới `canal_limited` 500 mm/vụ là giả định mặc định của engine, không phải số đo.

