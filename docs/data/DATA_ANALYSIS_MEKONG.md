# 01 — Phân tích tài nguyên dữ liệu cho FieldShift-Mekong

> Ngày phân tích: 13/11/2026. Mọi dòng có nhãn **[ĐÃ TEST]** đã được gọi API thật hôm nay; nhãn **[CHƯA KIỂM]** là hiểu biết tài liệu, cần xác nhận trước khi dựa vào.
> Dữ liệu thô đã tải: `data/raw/power/{cantho,chaudoc,soctrang,bentre}.json` (NASA POWER daily 2001-01-01 → 2026-11-09, 12 biến).

## 0. Kết luận nhanh (đọc phần này trước)

1. **Danh sách Resources rất thiên về Mỹ.** 13/24 nguồn chỉ có dữ liệu cho nước Mỹ (WSS, CDL, PRISM, SSURGO, NAIP, NLCD, NLDAS, CoCoRaHS, NWIS, AMS, NASS, OpenET, LANDFIRE) → **không dùng được cho ĐBSCL** về mặt dữ liệu không gian. Đừng tốn thời gian vào chúng.
2. **Nguồn dùng được ngay, không cần tài khoản:** NASA POWER (khí hậu ngày + climatology + độ ẩm đất mô hình), SRTM qua OpenTopoData. → **Toàn bộ MVP có thể chạy chỉ với POWER + SRTM + catalog cây FAO-56.**
3. **Cần tài khoản NASA Earthdata (miễn phí, ~5 phút — đăng ký NGAY hôm nay):** SMAP, IMERG, GLDAS, MODIS/VIIRS, HLS, ECOSTRESS, GRACE, NASADEM. Không có tài khoản = mai không lấy được các nguồn này.
4. **Phát hiện quan trọng — thiết kế v2 cần sửa:**
   - **NASA POWER Projection API (CMIP6) trả `-999` cho mọi điểm châu Á đã thử** (Cần Thơ, TP.HCM, Hà Nội, Bangkok, Delhi), chỉ có dữ liệu ở điểm Mỹ. → Phase 2 "projection" **không dựa vào POWER Projection được**. Thay bằng `STRESS_TEST` (delta nhiệt/mưa) + analog-year từ lịch sử.
   - **IMERG Final chỉ tới 2025-09-30** (trễ ~13 tháng ở thời điểm hiện tại). Dữ liệu gần đây phải dùng **IMERG Late** (tới 2026-11-11).
   - **GLDAS chỉ tới 2026-07-31** → chỉ dùng làm lịch sử, không làm "trạng thái hiện tại".
   - **SoilGrids REST trả 503** khi test → **bắt buộc cache + fallback** (giá trị prior theo vùng, nhãn `ASSUMPTION`).
   - **Không có nguồn mặn (salinity) nào trong Resources.** Mặn phải đến từ người dùng nhập ECw hoặc kịch bản `STRESS_TEST` — đúng như nguyên tắc UC-03 trong thiết kế.
5. **Dữ liệu lịch sử tự nó đã kể được câu chuyện luân canh** (xem §3): mùa khô Feb–Apr thiếu nước ~450–550 mm/vụ (ET0 − mưa), 14–26 ngày/tháng Tmax ≥ 35 °C ở nội đồng, mưa mùa khô biến động 23–451 mm giữa các năm → cơ sở định lượng để so baseline 3 vụ lúa với chuỗi lúa–màu.

## 1. Đánh giá từng nguồn

Thang **Ưu tiên**: P0 = MVP phải có · P1 = nên có nếu kịp · P2 = trình diễn/bổ sung · ✗ = không dùng cho ĐBSCL.

### 1.1. Nguồn NASA / toàn cầu — dùng được

| Nguồn | Sản phẩm cụ thể (short_name CMR) | Độ phân giải | Phủ thời gian / độ trễ **[ĐÃ TEST 13/11]** | Truy cập | Vai trò trong engine | Ưu tiên |
|---|---|---|---|---|---|---|
| **NASA POWER Daily** | REST `/api/temporal/daily/point`, community=AG | 0.5°×0.625° (MERRA-2), bức xạ 1° | 1981→ **2026-11-09** (trễ ~3–4 ngày), fill = -999 | **Không cần auth**, JSON | `climate_history`: T2M/Tmax/Tmin, mưa `PRECTOTCORR`, RH, gió `WS2M`, bức xạ, `T2MDEW` → **ET0 FAO-56 Penman-Monteith**; `GWETROOT/GWETTOP` (ẩm đất mô hình MERRA-2, 0–1) | **P0** |
| **NASA POWER Climatology** | `/api/temporal/climatology/point` | như trên | 2001–2025 (25 năm) | Không auth | Fallback `CLIMATOLOGY`, chuẩn tháng | **P0** |
| **NASA POWER Projection** | `/api/projection/daily|monthly/point` (NEX-GDDP-CMIP6, beta v2.6.4) | ~0.25° | **Trả -999 ở châu Á** (chỉ có dữ liệu ở Mỹ) | Không auth | ~~Climate projection~~ — **không dùng được** | ✗ (hiện tại) |
| **GPM IMERG** | `GPM_3IMERGDL` (Late, daily) · `GPM_3IMERGDF` (Final) | 0.1° (~11 km) | Late: 1998→**2026-11-11**; Final: →**2025-09-30** | Earthdata login; GES DISC OPeNDAP / Giovanni / AppEEARS **[CHƯA KIỂM]** | Kiểm chứng chéo mưa POWER; thống kê mưa cực đoan, chuỗi ngày khô | **P1** |
| **SMAP L4** | `SPL4SMGP` v008 (surface + root zone, 3-giờ) | 9 km EASE-2 | 2015-03-31→**2026-11-10** | Earthdata; NSIDC; file global ~100+ MB/3h → dùng AppEEARS point **[CHƯA KIỂM]** | `regional_soil_moisture` + anomaly so 2015–2025 | **P1** (P0 nếu có account) |
| **SMAP L3 Enhanced** | `SPL3SMP_E` v006 | 9 km | 2015→nay | Earthdata | Thay thế L4 (chỉ tầng mặt, có gap) | P2 |
| **MODIS NDVI/EVI** | `MOD13Q1` v061 (16 ngày) | 250 m | 2000→**2026-10-16** | Earthdata; AppEEARS point | `vegetation_history`: phát hiện **thời kỳ đất trống/ngập** và lịch vụ thực tế (3 đỉnh/năm = 3 vụ lúa) | **P1** |
| **VIIRS VI** | `VNP13A1` v002 | 500 m | 2012→nay | Earthdata | Dự phòng MODIS (Terra sắp hết tuổi thọ) | P2 |
| **MODIS ET** | `MOD16A2GF` v061 (8 ngày) | 500 m | 2000→nay | Earthdata | ET thực tế đối chiếu ET0×Kc | P2 |
| **MODIS LST** | `MOD11A2` v061 | 1 km | 2000→nay | Earthdata | Hotspot nhiệt (thay ECOSTRESS khi mây) | P2 |
| **Landsat / HLS** | `HLSL30`, `HLSS30`, `HLSL30_VI` v2.0 | 30 m | 2013/2015→**2026-11-05** | Earthdata; STAC (LP CLOUD) | NDVI cấp thửa; **mây mùa mưa rất nặng** ở ĐBSCL → chỉ tin ảnh mùa khô | P2 |
| **Sentinel-2 (ESA)** | L2A | 10–20 m | 2015→nay | Copernicus Data Space (đăng ký) | Như HLS; HLSS30 đã là Sentinel-2 hài hòa → **dùng HLS thay vì tích hợp riêng** | P2 |
| **ECOSTRESS** | `ECO_L2T_LSTE`, `ECO_L3T_JET` v003 | 70 m | 2018→**2026-10-06**, quỹ đạo ISS không đều | Earthdata; AppEEARS | Stress nhiệt/ET vi khí hậu; không đều → chỉ minh họa | P2 |
| **SRTM / NASADEM** | `SRTMGL1`, `NASADEM_HGT` | 30 m | tĩnh (2000) | **OpenTopoData `srtm30m` không auth [ĐÃ TEST]** (Cần Thơ 2 m, Sóc Trăng 1 m); LP DAAC cần login; OpenTopography cần API key | `terrain_features`: cao độ tương đối, trũng. **ĐBSCL quá phẳng (0–3 m) → xói mòn theo dốc gần như không áp dụng**; dùng cho "vùng trũng/dễ ngập" có nhãn `regional_context` | **P0** (1 call) |
| **GLDAS Noah** | `GLDAS_NOAH025_3H`, `_M` v2.1 | 0.25° | 2000→**2026-07-31** (trễ ~3.5 tháng) | Earthdata | Chuỗi ẩm đất/ET lịch sử dài hơn SMAP; **không** dùng làm state hiện tại | P2 |
| **GRACE/GRACE-FO** | `TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4` | 0.5° (thực ~300 km) | 2002→nay, tháng | Earthdata; PO.DAAC | Xu hướng tổng trữ nước **cấp lưu vực** (câu chuyện suy giảm nước ngầm/sụt lún) — chỉ `basin` scale, **không** cấp thửa | P2 (storytelling) |
| **GEDI L4A** | biomass | footprint 25 m | 2019→ | Earthdata | Ruộng lúa không có tán cao → **gần như không liên quan**; chỉ cho vườn cây/rừng ngập mặn quanh ruộng | ✗/P2 |
| **ERA5 (ECMWF)** | hourly reanalysis | 0.25° | 1940→nay (trễ ~5 ngày) | Cần tài khoản CDS + API key | Thay/kiểm chứng POWER; độ phân giải tốt hơn POWER (0.25° vs 0.5°) | P2 |
| **FAO GAEZ v4** | suitability, soil constraints, yield potential | ~9 km / 1 km | tĩnh + kịch bản | Web portal **[200 OK]**, tải raster thủ công | Prior **độ phù hợp cây** (lúa, ngô, đậu nành, đậu phộng...) + ràng buộc đất → cơ sở cho `SOFT` rule; trích giá trị điểm rồi đưa vào seed | **P1** |
| **USDA Ag Data Commons** | tập dữ liệu nghiên cứu | — | — | Web | Phần lớn dữ liệu Mỹ; chỉ dùng **tham khảo tham số cây** (Kc, nhu cầu nước) nếu có bộ phù hợp | P2 |

### 1.2. Nguồn chỉ có dữ liệu cho nước Mỹ — **không dùng cho ĐBSCL**

| Nguồn | Vì sao không dùng | Giá trị gián tiếp (nếu có) |
|---|---|---|
| Web Soil Survey, SSURGO/STATSGO2 | Chỉ đất Mỹ | Mẫu thuộc tính đất (texture, drainage class, hydrologic group) → **dùng làm schema** `local_soil` |
| CDL CropScape | Chỉ Mỹ | Ý tưởng: phát hiện chuỗi luân canh lịch sử từ ảnh phân loại → ở VN thay bằng chu kỳ NDVI MODIS |
| PRISM | Chỉ Mỹ | — |
| NAIP | Ảnh hàng không Mỹ | — |
| NLCD, LANDFIRE | Lớp phủ Mỹ | Thay bằng ESA WorldCover (ngoài danh sách) nếu cần |
| NLDAS | Bắc Mỹ | **Dùng GLDAS** (bản toàn cầu tương đương) |
| CoCoRaHS | Mưa cộng đồng Bắc Mỹ | Ý tưởng: cho nông dân tự nhập mưa/EC → `OBSERVED_FIELD` |
| NWIS | Thủy văn Mỹ | Ở VN tương đương: trạm mặn/mực nước của Đài KTTV Nam Bộ / MRC (ngoài danh sách) |
| AMS Market News, NASS QuickStats | Giá/thống kê Mỹ | → `EconomicModel` **tắt** trong MVP, cho người dùng nhập giá |
| OpenET | Tây nước Mỹ | Thay bằng ET0 POWER + MOD16 |

> **Gợi ý tùy chọn (MAY, không làm nếu thiếu giờ):** vì kiến trúc dùng adapter theo vùng, có thể thêm 1 "thửa demo ở Iowa" dùng CDL/SSURGO để chứng minh tính mở rộng toàn cầu (hạng mục *Global Connection*). Chỉ làm khi MVP ĐBSCL đã xong.

### 1.3. Nguồn ngoài danh sách nhưng thiết kế v2 cần

| Nguồn | Trạng thái | Xử lý |
|---|---|---|
| SoilGrids (ISRIC) | **503 khi test** | Cache-aside; fallback prior vùng (đất phù sa sét nặng, pH 4.5–6, nhãn `ASSUMPTION`); hoặc dùng soil constraint của GAEZ |
| Mặn ĐBSCL (bản tin KTTV/Bộ NN, MRC) | Không có API ổn định | Người dùng nhập ECw; kịch bản "mặn sớm N tuần" là `STRESS_TEST` |
| Catalog cây (FAO-56 Kc & thời gian sinh trưởng, FAO-33/AquaCrop, khuyến nông) | Tài liệu | Seed JSON có `source` từng tham số |
| Dự báo mùa (GEOS-S2S) | Không có API điểm đơn giản | **Bỏ khỏi MVP**; `FORECAST` = "không khả dụng" → kích hoạt gate G6 (tốt cho demo tính trung thực) |

## 2. Kế hoạch truy cập dữ liệu (cho ngày mai)

| Bước | Làm gì | Ai/khi nào |
|---|---|---|
| 1 | Đăng ký Earthdata Login: https://urs.earthdata.nasa.gov → tạo `~/.netrc` (`machine urs.earthdata.nasa.gov login … password …`) → approve app "NASA GESDISC DATA ARCHIVE" và "LP DAAC" trong profile | **Hôm nay** |
| 2 | Pre-fetch & cache POWER daily cho các điểm demo | **Đã xong** (4 điểm) |
| 3 | AppEEARS (https://appeears.earthdatacloud.nasa.gov) gửi 1 request *point* cho 4 điểm: `SPL4SMGP` (sm_surface, sm_rootzone), `MOD13Q1` (NDVI), `MOD16A2GF` (ET) 2015–2026. Kết quả async (vài phút–vài giờ) → CSV | Hôm nay/sáng mai |
| 4 | IMERG Late daily cho 4 điểm qua Giovanni "time series, area-averaged" hoặc OPeNDAP | Sáng mai, nếu kịp |
| 5 | SRTM: 1 call OpenTopoData cho mỗi thửa | Lúc tạo thửa (runtime) |

Nguyên tắc: **demo chạy từ cache** (thiết kế UC-09/NFR Portability). API live chỉ là đường refresh. Mạng hội trường hackathon thường yếu.

## 3. Phân tích NASA POWER 25 năm (2001–2025) tại 4 điểm ĐBSCL

Điểm chọn đại diện cho các bối cảnh nước/mặn khác nhau (theo yêu cầu MVP §2.2):

| Điểm | lat, lon | Bối cảnh |
|---|---|---|
| Cần Thơ | 10.03, 105.78 | Nội đồng, nước ngọt |
| Châu Đốc (An Giang) | 10.70, 105.12 | Đầu nguồn, lũ |
| Bến Tre | 10.10, 106.45 | Ven biển, xâm nhập mặn |
| Sóc Trăng (Trần Đề) | 9.55, 106.20 | Ven biển, mặn mạnh |

ET0 = FAO-56 Penman–Monteith tính từ biến POWER (xấp xỉ Rn đơn giản hóa — cần thay bằng công thức đầy đủ với Ra theo vĩ độ/ngày khi code). `EVPTRNS` là ET thực tế mô hình MERRA-2.

### 3.1. Trung bình tháng — Cần Thơ (nội đồng)

| | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Mưa (mm) | 19 | 10 | 24 | 56 | 165 | 222 | 241 | 208 | 250 | 228 | 137 | 44 |
| ET0 (mm) | 138 | 167 | 212 | 194 | 152 | 122 | 114 | 116 | 107 | 109 | 107 | 116 |
| Tmax (°C) | 31.7 | 34.8 | 36.7 | 36.7 | 33.6 | 31.0 | 30.1 | 30.0 | 29.8 | 29.9 | 30.0 | 30.1 |
| Ngày Tmax ≥ 35 °C | 1.8 | 14.0 | 25.6 | 22.0 | 8.0 | 0.6 | 0 | 0 | 0 | 0 | 0 | 0 |
| GWETROOT (0–1) | 0.64 | 0.56 | 0.52 | 0.54 | 0.61 | 0.74 | 0.81 | 0.85 | 0.88 | 0.91 | 0.88 | 0.77 |

Châu Đốc gần giống Cần Thơ (nóng hơn: 18 và 26 ngày ≥35 °C ở tháng 2–3). Bến Tre ôn hòa hơn (≤14.5 ngày ≥35 °C, tháng 4).

### 3.2. Thống kê năm

| Điểm | Mưa năm TB ± SD (mm) | Năm khô nhất | Năm ướt nhất | Chuỗi ngày khô dài nhất (<1 mm) trung vị / max | Ngày mưa ≥50 mm/năm |
|---|---|---|---|---|---|
| Cần Thơ | 1605 ± 561 | 959 (2014) | 2928 (2020) | 38 / 122 | 1.1 |
| Châu Đốc | 1526 ± 599 | 918 (2002) | 2988 (2020) | 36 / 81 | 1.2 |
| Sóc Trăng | 1753 ± 316 | 1224 (2015) | 2558 (2020) | 46 / 126 | 1.1 |
| Bến Tre | 1627 ± 405 | 1096 (2014) | 2701 (2020) | 41 / 126 | 0.5 |

**Mưa mùa khô (Dec–Apr), Cần Thơ, theo năm:** 2002: 40 · 2005: 23 · 2010: 46 · 2014: 40 · **2016: 37** · 2017: 340 · 2020: 112 · 2022: 412 · **2024: 47** · 2025: 252 (mm). Biến động gấp ~18 lần giữa năm khô và ướt.

### 3.3. Ý nghĩa cho engine (đây là "evidence" để trình bày)

1. **Cửa sổ rủi ro nước rõ ràng: Feb–Apr.** Thiếu hụt khí hậu (ET0 − mưa) ≈ 157 + 188 + 138 ≈ **480 mm** riêng 3 tháng ở Cần Thơ. Vụ lúa cuối Đông Xuân / đầu Xuân Hè phụ thuộc hoàn toàn vào tưới kênh — đúng lúc mặn xâm nhập. → Cơ sở cho chuỗi **lúa – màu – lúa** (thay vụ giữa bằng cây cạn ít nước: đậu xanh, mè, ngô).
2. **Stress nhiệt nội đồng**: 14–26 ngày/tháng Tmax ≥ 35 °C ở Feb–Apr → rủi ro lép hạt nếu lúa trổ bông lúc này (ngưỡng tham khảo ~35 °C lúc trổ, cần trích nguồn khi đưa vào catalog). → `SOFT` rule "giai đoạn nhạy cảm trùng tháng nóng".
3. **Năm khô lịch sử là kịch bản stress có thật**: 2005, 2016, 2024 → dùng **analog-year** (giữ nguyên thứ tự ngày, thỏa yêu cầu §6.3 "giữ tương quan thời gian"). 2022 = analog ướt.
4. **Bằng chứng mặn ≠ mưa**: năm 2020 là năm xâm nhập mặn lịch sử ở ĐBSCL nhưng mưa mùa khô Cần Thơ 2020 (112 mm) **không thấp bất thường** — mặn do dòng chảy thượng nguồn Mekong, không do mưa tại chỗ. → Minh chứng cho nguyên tắc "không suy EC từ mưa/POWER/IMERG"; nên đưa vào slide.
5. **Xu hướng Tmax 2001–2025** gần 0 hoặc trái dấu giữa các ô (−0.27 → +0.24 °C/thập kỷ) → **không** đưa claim "nóng lên X °C" từ POWER điểm; dùng stress test +1/+2 °C có nhãn.
6. **Cảnh báo chất lượng**: ô lưới Sóc Trăng có Tmax thấp bất thường (28–31 °C, gần như 0 ngày ≥35 °C) và EVPTRNS rất thấp → ô MERRA-2 0.5° **lẫn biển**. Phải gắn `quality_flag = COASTAL_CELL_MIXED` và nên kiểm chứng bằng ERA5/IMERG. Đây đúng là ví dụ "dữ liệu lưới là `regional_context`, không phải đo tại thửa".
7. Dữ liệu POWER 2001–2026 **không thiếu** (chỉ 6 ngày thiếu bức xạ) → pipeline đơn giản, nhưng vẫn phải xử lý `-999` → `UNKNOWN`, không thay 0.

## 4. Ánh xạ dữ liệu → khối engine (MVP)

| Khối thiết kế v2 | Dữ liệu MVP | Nhãn evidence |
|---|---|---|
| Context Builder | POWER daily (cache), SRTM point, SoilGrids/prior | `OBSERVED_REMOTE_ESTIMATE` (POWER/SRTM), `MODEL_ESTIMATE` (GWETROOT), `ASSUMPTION` (prior đất) |
| Field State | GWETROOT 30 ngày gần nhất + anomaly vs climatology; người dùng: ECw, thoát nước, tưới | `estimated_from_regional_data`, `reported_by_farmer` |
| Scenario Engine | `CLIMATOLOGY` (25 năm), `STRESS_TEST`: analog khô 2016/2024, nóng +1.5 °C, mưa −30 %, mặn sớm 4 tuần | `probability = null` cho stress test |
| Water Balance | ET0 (PM) × Kc (FAO-56) − mưa hiệu quả; lúa: + làm đất + thấm | `LITERATURE_RULE` + `MODEL_ESTIMATE` |
| Feasibility | Season windows, thời gian sinh trưởng, ECw ngưỡng FAO-29 (có điều kiện), thoát nước | `HARD`/`SOFT`/`UNKNOWN_REQUIRES_CHECK` |
| Soil Impact | Rule định tính (họ đậu, tàn dư, đa dạng) | `POTENTIAL_QUALITATIVE` |
| Twin | trajectory ngày/tuần từ Water Balance | cùng `scenario_id` |

## 5. Rủi ro dữ liệu & xử lý

| Rủi ro | Xác suất | Xử lý |
|---|---|---|
| Mạng hội trường yếu / API NASA chậm | Cao | Cache-first, file JSON trong repo, demo offline |
| Chưa có Earthdata account | Trung bình | Đăng ký hôm nay; MVP vẫn chạy với POWER + SRTM |
| AppEEARS chậm | Trung bình | Gửi request hôm nay |
| SoilGrids 503 | Đã xảy ra | Prior vùng có nhãn `ASSUMPTION` |
| POWER Projection không có dữ liệu châu Á | Đã xác nhận | Bỏ `CLIMATE_PROJECTION` khỏi MVP; nêu rõ trong UI/slide là giới hạn đã kiểm tra |
| Ô lưới ven biển lẫn biển | Đã thấy (Sóc Trăng) | Quality flag + dịch điểm vào đất liền 0.25° hoặc dùng ERA5 |

## 6. Lưu ý thể lệ (quan trọng)

Thể lệ NASA Space Apps Hà Nội 2026, mục IV.2: *"phần lõi sản phẩm phải được phát triển trong thời gian thi (14–15/11); mọi tài nguyên bên thứ ba và công cụ AI đã dùng phải được nêu rõ trong bài nộp."*
- Hôm nay (13/11) an toàn: nghiên cứu dữ liệu, tài liệu thiết kế, hợp đồng API, đăng ký tài khoản, tải/cache dữ liệu công khai.
- Rủi ro: viết code lõi (engine, backend) trước 14/11. Nên để code lõi vào ngày thi và ghi khai báo AI tools (Claude Code, Codex...) trong bài nộp.
- Hạn nộp chấm Hà Nội: thể lệ ghi **11:00** (mục IV.1) nhưng bảng lịch ghi **12:00** 15/11 → **lấy 11:00** cho an toàn.
