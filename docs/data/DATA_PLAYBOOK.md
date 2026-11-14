# Sổ tay dữ liệu FieldShift-Mekong (cho cả người không làm kỹ thuật)

> Đọc 5 phút đầu: mục 1 và 2. Người triển khai đọc thêm mục 3–5.
> Trạng thái thật từng nguồn (đã lấy được chưa, file ở đâu, lệnh chạy lại) nằm trong [`data_inventory.json`](data_inventory.json); các job chạy qua đêm và cách kiểm tra sáng mai: [`OVERNIGHT_HANDOFF.md`](OVERNIGHT_HANDOFF.md). Ảnh cho slide: [`images/`](images/).

## 0. Kết quả đã kiểm chứng tối 13/11/2026

| Nguồn | Đã có | Con số đáng nói |
|---|---|---|
| NASA POWER | 4 điểm × 9.444 ngày (2001→09/11/2026) | Nguồn tính toán chính |
| IMERG tháng (Final) | 4 điểm × 297 tháng (2001→09/2025) | Khớp mưa POWER theo tháng **r = 0,83**; IMERG ướt hơn POWER **~25 mm/tháng** ⇒ engine có thể *ước tính dư* nhu cầu tưới một chút — nói rõ khi thuyết trình |
| IMERG ngày (Late) | đang tải (2023→nay), đã có 440 ngày | Theo ngày khớp kém hơn (r ≈ 0,63) — mưa nhiệt đới rất cục bộ |
| ERA5 (Open-Meteo) | 4 điểm × 9.443 ngày | Đối chiếu nhiệt độ/mưa với POWER |
| GLDAS | 4 điểm × 307 tháng (2001→07/2026) | Data Rods đã ngừng; lấy bản tháng qua OPeNDAP |
| NEX-GDDP-CMIP6 | **đủ 4 điểm**, 2025–2050 | Engine có kịch bản khí hậu cho mọi ruộng mẫu |
| FAO GAEZ v4 | 41 lớp/điểm (phù hợp cây + hạn chế đất) | Không có lớp riêng cho đậu xanh |
| Worldview | 12 ảnh mùa khô 2016/2020/2024 + mùa mưa 2024 | Ảnh NDVI 3/2016 thấy rõ vùng ven biển khô nâu |
| SMAP, MODIS NDVI/ET | AppEEARS đang xử lý | Tự tải khi xong |
| ECOSTRESS, HLS | AppEEARS đang xử lý | Tự tải khi xong |
| SoilGrids | Gọi được nhưng **không có giá trị** tại 4 điểm | Engine dùng giá trị mặc định của vùng, gắn nhãn *Giả định* |

## 1. Sản phẩm cần biết gì về thửa ruộng — và ai trả lời

Hãy hình dung cán bộ khuyến nông hỏi 8 câu trước khi khuyên nông dân đổi vụ. Mỗi câu có một (vài) nguồn dữ liệu trả lời:

| # | Câu hỏi đời thường | Nguồn chính (NASA in đậm) | Dùng ở phần nào của sản phẩm |
|---|---|---|---|
| 1 | **Mấy chục năm qua ở đây nóng, mưa, nắng, gió thế nào?** | **NASA POWER** (đối chiếu: **IMERG**, ERA5) | Tính "cây cần bao nhiêu nước mỗi ngày" (ET₀), xếp 24 năm thời tiết thật thành các kịch bản năm thường / năm hạn / năm ướt |
| 2 | **Mưa thật sự rơi bao nhiêu, có đợt hạn dài không?** | **GPM IMERG** (vệ tinh đo mưa, ô ~10 km) | Kiểm tra lại mưa của POWER (ô ~50 km); đếm chuỗi ngày không mưa; biểu đồ mưa trong bài thuyết trình |
| 3 | **Đất đang khô hay ướt so với mọi năm?** | **SMAP** (vệ tinh đo ẩm đất, ô 9 km), **GLDAS**, POWER GWETROOT | "Trạng thái ruộng hôm nay": đầu vụ đất khô hơn bình thường → cảnh báo cây cạn thiếu nước |
| 4 | **Thực tế ở đây đang trồng mấy vụ, vụ nào bỏ trống?** | **MODIS/VIIRS NDVI** (độ xanh cây, 250 m), **HLS = Landsat + Sentinel-2** (30 m) | Xác nhận chuỗi vụ hiện tại (3 đỉnh xanh/năm = 3 vụ lúa); minh họa "ruộng xanh/trống theo tháng" |
| 5 | **Cây có đang bị nóng/thiếu nước không?** | **ECOSTRESS** (nhiệt độ bề mặt & bốc hơi, 70 m), **MODIS LST/ET** | Đối chiếu số ngày nóng ≥35 °C engine tính; ảnh minh họa điểm nóng |
| 6 | **Ruộng cao hay trũng?** | **SRTM** (độ cao, 30 m) | Cảnh báo trũng/khó thoát nước (chỉ là gợi ý — ĐBSCL quá phẳng, phải hỏi nông dân) |
| 7 | **Đất loại gì, chua không, có hợp cây này không?** | SoilGrids (ISRIC), **FAO GAEZ** | Giá trị đất tham khảo; độ phù hợp cây theo FAO để giải thích vì sao chọn đậu xanh/đậu nành |
| 8 | **Mùa tới và 20–30 năm tới có thể ra sao?** | Dự báo mùa ECMWF (qua Open-Meteo), **NEX-GDDP-CMIP6** (NASA) | Kịch bản "Dự báo (chưa kiểm định)" và "Kịch bản khí hậu 2041–2050" để thử độ bền của phương án |
| — | **Nước kênh có mặn không?** | **Không có vệ tinh nào đo được** độ mặn nước kênh. Tín hiệu gián tiếp: lưu lượng sông Mekong (GloFAS). Chính xác: **đo tại ruộng bằng máy EC** | Ruộng ven biển luôn "cần kiểm tra" cho tới khi nhập số đo; khi nhập, phương án tự cập nhật |

**Một câu để nói khi thuyết trình:** *"Chúng tôi dùng NASA POWER để tính cây cần bao nhiêu nước mỗi ngày trong 24 năm, IMERG và SMAP để kiểm tra mưa và độ ẩm đất thật, MODIS/Landsat để xác nhận ruộng đang trồng mấy vụ, và CMIP6 để thử phương án trong khí hậu 2040s. Cái gì vệ tinh không đo được — như mặn nước kênh — chúng tôi nói rõ là 'chưa biết' và hướng dẫn đo."*

## 2. Danh sách 24 nguồn của đề bài — dùng được gì ở Việt Nam

Ký hiệu: ✅ dùng, đã/đang lấy · 🟡 dùng được, cần thời gian/tài khoản · ⚪ có cho VN nhưng không cần · ❌ chỉ có cho Mỹ

| Nguồn trong đề | Có cho VN? | Quyết định | Vì sao / thay bằng gì |
|---|---|---|---|
| SMAP | ✅ | **Dùng** | Ẩm đất mặt + vùng rễ, ô 9 km, mỗi 3 giờ, trễ ~2–3 ngày. Lấy qua AppEEARS (tài khoản Earthdata) |
| GPM IMERG | ✅ | **Dùng** | Mưa vệ tinh ô 0,1° (~11 km). Late: trễ ~14 giờ; Final (chuẩn nghiên cứu): trễ ~3,5–5 tháng. Ảnh Worldview dùng cho slide |
| Landsat | ✅ | **Dùng qua HLS** | HLS gộp Landsat + Sentinel-2, 30 m, ~3 ngày/lần; mùa mưa ĐBSCL nhiều mây → chủ yếu dùng ảnh mùa khô |
| MODIS / VIIRS | ✅ | **Dùng** | NDVI/EVI 250 m 16 ngày, ET 500 m; VIIRS là bản kế nhiệm khi MODIS ngừng |
| NASA POWER | ✅ | **Dùng — nguồn chính** | Không cần tài khoản; 1981→nay, trễ ~3–4 ngày; ô ~50 km |
| SRTM | ✅ | **Dùng** | 30 m; lấy tức thì qua OpenTopoData |
| ECOSTRESS | ✅ | **Dùng (minh họa)** | 70 m; phủ 52°B–52°N nên có ĐBSCL; thời điểm chụp không đều, hay bị mây |
| GLDAS | ✅ | **Dùng (đối chiếu)** | Ô 0,25°, mô hình đất–nước toàn cầu, trễ vài tháng → dùng cho lịch sử, không cho "hôm nay". Dịch vụ Data Rods đã ngừng → lấy bản tháng qua OPeNDAP |
| NLDAS | ❌ | Thay bằng GLDAS | Chỉ Bắc Mỹ |
| FAO GAEZ | ✅ | **Dùng (độ phù hợp cây)** | Raster toàn cầu; đọc giá trị tại điểm qua dịch vụ ảnh của FAO hoặc tải tay |
| ERA5 (ECMWF) | ✅ | **Dùng (đối chiếu)** | Ô 0,25°; lấy không cần tài khoản qua Open-Meteo Archive |
| Sentinel-2 (ESA) | ✅ | **Dùng qua HLS** | Không cần tích hợp riêng |
| GEDI | ⚪ | Không dùng | Đo chiều cao tán rừng — ruộng lúa không có tán cao |
| USDA Ag Data Commons | ⚪ | Tham khảo tham số cây | Dữ liệu chủ yếu của Mỹ |
| Web Soil Survey, SSURGO/STATSGO2 | ❌ | Thay bằng SoilGrids + hỏi nông dân | Đất Mỹ |
| CDL CropScape | ❌ | Thay bằng chu kỳ NDVI MODIS | Bản đồ cây trồng Mỹ |
| PRISM | ❌ | Thay bằng POWER/IMERG/ERA5 | Khí hậu Mỹ |
| NAIP | ❌ | Thay bằng HLS/Sentinel-2 | Ảnh máy bay Mỹ |
| NLCD, LANDFIRE | ❌ | Thay bằng ESA WorldCover (nếu cần) | Lớp phủ Mỹ |
| CoCoRaHS | ❌ | Ý tưởng: nông dân tự nhập mưa | Mạng đo mưa Bắc Mỹ |
| NWIS | ❌ | Thay bằng GloFAS (lưu lượng Mekong) + bản tin mặn SIWRR | Thủy văn Mỹ |
| AMS Market News, NASS QuickStats | ❌ | Kinh tế để ngoài MVP; cho nhập giá | Giá/thống kê Mỹ |
| OpenET | ❌ | Thay bằng ET₀ POWER + MODIS ET + ECOSTRESS ET | Chỉ miền Tây nước Mỹ |

**Bổ sung ngoài danh sách (đã dùng):** SoilGrids (đất), Open-Meteo/ECMWF SEAS5 (dự báo mùa), GloFAS (lưu lượng sông → tín hiệu mặn), NEX-GDDP-CMIP6 (khí hậu tương lai — vẫn là dữ liệu NASA), bản tin mặn SIWRR (tham khảo, PDF).

## 3. "Đọc một nguồn" trong 30 giây — các khái niệm cần biết

| Từ | Nghĩa đời thường | Ví dụ |
|---|---|---|
| **Ô lưới / độ phân giải** | Vệ tinh/mô hình chia mặt đất thành ô vuông và cho **một con số trung bình cho cả ô** | POWER ô ~50 km ⇒ một số cho cả vùng cỡ cả tỉnh Cần Thơ; SRTM 30 m ⇒ cỡ một thửa nhỏ |
| **Độ trễ** | Dữ liệu ngày hôm nay bao lâu sau mới có | POWER ~3–4 ngày; IMERG Late ~14 giờ; GLDAS ~vài tháng |
| **ET₀** | Lượng nước "trời hút đi" mỗi ngày từ một thảm cỏ chuẩn (mm/ngày); cây cần ≈ ET₀ × hệ số cây | Tháng 3 ở Cần Thơ ~7 mm/ngày |
| **NDVI** | Độ xanh của cây nhìn từ vệ tinh, 0 (đất trống/nước) → ~0,9 (cây rậm) | 3 đỉnh NDVI/năm = 3 vụ lúa |
| **LST** | Nhiệt độ **bề mặt** (lá/đất), khác nhiệt độ không khí | Ruộng khô trưa nắng có thể >40 °C |
| **Tái phân tích (reanalysis)** | Mô hình thời tiết "điền đầy" quá khứ bằng mọi quan trắc có được | ERA5, MERRA-2 (nguồn của POWER), GLDAS |
| **ECw, ‰** | Độ mặn nước: dS/m (máy EC) hoặc ‰ (phần nghìn, cách cán bộ VN hay nói). 1 dS/m ≈ 0,64 ‰ | Lúa bắt đầu giảm năng suất khi nước tưới > ~2 dS/m (~1,3 ‰) |
| **Kịch bản ≠ dự báo** | Kịch bản là "nếu năm tới giống năm 2016 thì sao"; dự báo là "năm tới có khả năng thế này" | Sản phẩm luôn ghi rõ loại |

## 4. Mỗi nguồn: lấy gì, ở đâu, đi vào đâu (cho người triển khai)

> Các lệnh chạy từ thư mục gốc repo với `.venv` đã kích hoạt. Tài khoản Earthdata nằm trong `~/.netrc` (không commit). Dữ liệu thô vào `.fieldshift/cache/` (không commit); dữ liệu đã xử lý, nhỏ, dùng được ngay vào `apps/api/src/fieldshift/resources/observations/<nguồn>/<điểm>.json.gz`.

| Nguồn | Sản phẩm / biến | Cách lấy | Đầu ra | Engine dùng để |
|---|---|---|---|---|
| NASA POWER | Daily AG: T2M_MAX/MIN, PRECTOTCORR, RH2M, WS2M, ALLSKY_SFC_SW_DWN, T2MDEW, GWETROOT | Tự động khi lập kế hoạch (`infrastructure/data_sources/nasa/power.py`) | cache + `resources/demo_cache/power/` | ET₀ FAO-56, cân bằng nước, 24 kịch bản năm |
| SRTM | srtm30m | Tự động (`nasa/nasadem.py`) | cache | độ cao ruộng |
| SoilGrids | clay, sand, pH, SOC 0–30 cm | Tự động (`local/soilgrids.py`) | cache | đất tham khảo |
| ECMWF SEAS5 | 6 tháng tới, nhiều thành viên | Tự động (`forecasts/open_meteo_seasonal.py`) | cache | kịch bản FORECAST |
| GloFAS | lưu lượng Mekong tại Tân Châu | Tự động (`data_sources/glofas.py`) | cache | tín hiệu mặn sớm (chỉ tham khảo) |
| NEX-GDDP-CMIP6 | tasmax, pr; ACCESS-CM2, MPI-ESM1-2-HR; SSP2-4.5, SSP5-8.5 | `scripts/data/fetch_nex_cmip6.py` (~16 phút/điểm) | `resources/projections/<điểm>.json` | kịch bản CLIMATE_PROJECTION |
| IMERG | Monthly Final `GPM_3IMERGM`; Daily Late `GPM_3IMERGDL` | `scripts/data/fetch_imerg.py` | `resources/observations/imerg/` | đối chiếu mưa POWER; chuỗi ngày khô |
| SMAP + MODIS | `SPL4SMGP.008` sm_surface/rootzone; `MOD13Q1.061` NDVI/EVI; `MOD16A2GF.061` ET | `scripts/data/fetch_appeears.py` (AppEEARS, bất đồng bộ) | `resources/observations/appeears/` | ẩm đất hôm nay vs mọi năm; lịch vụ thực tế; ET thực |
| ECOSTRESS + HLS | `ECO_L2T_LSTE.002`, HLS L30/S30 | AppEEARS task thứ 2 | `resources/observations/…` | minh họa stress nhiệt; NDVI 30 m mùa khô |
| GLDAS | Noah 2.1 tháng: ẩm đất 0–10/10–40 cm, bốc hơi, mưa | `scripts/data/fetch_gldas.py` (OPeNDAP; Data Rods đã ngừng) | `resources/observations/gldas/` | chuỗi ẩm đất dài 2001→ |
| ERA5 | tmax, tmin, mưa, ET₀ | Open-Meteo Archive (không tài khoản) | `resources/observations/era5/` | đối chiếu POWER |
| FAO GAEZ v4 | độ phù hợp cây, ràng buộc đất | dịch vụ ảnh FAO / tải tay | ghi chú điểm | giải thích độ phù hợp cây |
| Worldview | ảnh true color, IMERG, NDVI | Snapshot URL | `docs/data/images/` | slide thuyết trình |

## 5. Thứ tự làm ngày thi (gợi ý)

1. **Sáng sớm:** kiểm tra các job chạy đêm qua đã xong (`data_inventory.json` → `status`), chạy lại lệnh "resume" nếu job nào dừng.
2. **Nối vào engine (ưu tiên giá trị cho giám khảo):**
   - IMERG → thêm vào bằng chứng "mưa POWER khớp IMERG X%" và cảnh báo chuỗi ngày khô.
   - SMAP → "đất hôm nay khô/ướt hơn mọi năm" trong trạng thái ruộng.
   - MODIS NDVI → "vệ tinh xác nhận ruộng đang trồng 3 vụ" (kiểm tra chuỗi hiện tại).
   - CMIP6 đủ 4 điểm → kịch bản khí hậu cho mọi ruộng mẫu.
3. **Slide:** ảnh Worldview + 1 hình "dữ liệu NASA đi vào đâu" (mục 1 của file này).
4. **Không làm** trong 2 ngày: dữ liệu Mỹ, GEDI, Sentinel-2 riêng, tự xây mô hình mặn.

## 6. Những câu KHÔNG được nói (giám khảo hay bắt lỗi)

- "Vệ tinh đo được độ mặn ruộng" — sai. SMAP đo ẩm đất, không đo mặn nước kênh.
- "Dự báo chính xác thời tiết năm 2027" — sai. Ta dùng kịch bản và dự báo mùa **chưa kiểm định**.
- "NDVI cho biết đất khỏe" — sai. NDVI là độ xanh của cây, không phải chất lượng đất.
- "Số liệu tại thửa ruộng" khi dùng POWER/IMERG/SMAP — sai. Đó là **trung bình ô lưới** (vài km đến ~50 km).

Nguồn kiểm chứng thông tin trong bảng: [HLS v2.0 phủ gần toàn cầu (NASA Landsat)](https://landsat.gsfc.nasa.gov/article/a-new-and-improved-harmonized-landsat-and-sentinel-2-dataset) · [ECOSTRESS phủ 52°B–52°N (Earthdata)](https://www.earthdata.nasa.gov/data/catalog/lpcloud-eco-l2-lste-002) · [IMERG Early/Late/Final (GPM FAQ)](https://gpm.nasa.gov/resources/faq/what-are-differences-between-imerg-early-late-and-final-runs-and-which-should-be-used) · [SMAP L4 v8 (NSIDC)](https://nsidc.org/data/spl4smgp) · [GAEZ v4 (FAO)](https://www.fao.org/gaez/gaezv4/en) · [Data Rods (Earthdata)](https://www.earthdata.nasa.gov/learn/articles/data-rods-for-hydrology) — đã ngừng theo [hướng dẫn di chuyển GES DISC](https://github.com/nasa/gesdisc-tutorials/blob/main/user-guidance/GES_DISC_Migration_to_Earthdata_Website_and_Earthdata_Cloud.md).
