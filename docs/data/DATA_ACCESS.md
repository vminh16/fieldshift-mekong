# Truy cập dữ liệu điểm — FieldShift Mekong

[TESTED] Kiểm tra ngày **13/11/2026**, từ máy làm việc của team; không có `~/.netrc`. Đã đọc `docs/01-phan-tich-du-lieu.md` và `docs/02-thiet-ke-backend-api-db.md`. Chỉ ghi trong `docs/research/` và `scripts/data/`; không sửa backend/tài liệu gốc, không commit.

[TESTED] `[TESTED]` = HTTP thực tế, dữ liệu tải thật hoặc kiểm tra cục bộ được nói rõ. `[UNVERIFIED]` = cần tài khoản, chưa chạy trọn luồng hoặc là ước tính; đọc được tài liệu/catalog **không** có nghĩa đã tải được dữ liệu.

[TESTED] **Đã tạo đủ dữ liệu yêu cầu tại Cần Thơ trong 980,4 giây (~16 phút 20 giây):** hai model, hai SSP, tasmax/pr, 2025–2050; **8 chuỗi × 312 tháng = 2.496 giá trị tháng**. File [cantho.json](demo-cache/nex_cmip6/cantho.json) 446.605 byte; CSV điểm gốc tổng 6.499.527 byte. Ba site còn lại có đủ năm 2025 cho ACCESS-CM2, hai SSP/hai biến (48 giá trị tháng/site). Kiểm tra độc lập đã tính lại toàn bộ tháng từ CSV, xác nhận đủ ngày/năm nhuận và đổi đơn vị: [verification.txt](verification.txt).

| Nguồn | Cách lấy điểm rẻ nhất đã xác định | Auth / mức kiểm chứng | Độ trễ truy cập; dung lượng | Script; lưu ý |
|---|---|---|---|---|
| NEX-GDDP-CMIP6 v2 | [TESTED] S3 public để tìm key/size; **NCCS NCSS CSV** để subset trên server | [TESTED] Không auth; đã lấy chuỗi ngày, tạo tháng | [TESTED] Thường 7–11 giây/năm/biến/điểm; request chậm nhất 193,21 giây, toàn bộ Cần Thơ 980,4 giây; CSV mẫu tasmax 30.985 byte/năm | [TESTED] `scripts/data/fetch_nex_cmip6.py`; pin `_v2.0.nc`, không trộn v1 |
| IMERG Late `GPM_3IMERGDL.07` | [TESTED] CMR tìm granule/URL hiện hành; DDS/DAS trên GES DISC cũ. [UNVERIFIED] Hyrax ASCII cửa sổ nhỏ chứa 4 điểm, **1 request/ngày**, rồi tách điểm | [TESTED] Data GET chuyển URS → 401 khi không auth. [UNVERIFIED] Tải dữ liệu cần Earthdata + archive consent | [TESTED] Metadata khoảng 1–3 giây; granule mới nhất 11/11/2026, global ~25,11 MiB. [UNVERIFIED] Chưa đo size/latency subset sau login | [TESTED] `scripts/data/fetch_imerg.py`; cloud URL từ CMR, có `--legacy`; không hard-code V07B |
| SMAP L4 `SPL4SMGP.008` | [TESTED] AppEEARS catalog có sản phẩm/layer. [UNVERIFIED] 1 task point chung với MODIS, không tải granule global | [TESTED] Product/layer GET 200 không auth. [UNVERIFIED] Submit/poll/download cần Earthdata | [TESTED] Catalog ~1–2 giây; CMR có granule 10/11/2026 21:00 UTC. [UNVERIFIED] Queue, CSV size chưa đo | [TESTED] `scripts/data/fetch_appeears.py`; sm_surface/rootzone là ẩm đất mô hình, không phải độ mặn |
| MOD13Q1.061 / MOD16A2GF.061 | [TESTED] AppEEARS catalog/layer. [UNVERIFIED] Cùng task 4 điểm với SMAP, giữ QA/metadata | [UNVERIFIED] Cần Earthdata cho task, chưa có job thật | [TESTED] CMR: MOD13Q1 mới nhất 16–31/10/2026; MOD16A2GF mới nhất **27–31/12/2025**. [UNVERIFIED] Queue/CSV size chưa đo | [TESTED] `scripts/data/fetch_appeears.py`; request đến 2026 không tạo ra ET gap-filled năm 2026 |
| ERA5 CDS timeseries | [TESTED] Dataset `reanalysis-era5-single-levels-timeseries` tồn tại, cho **CSV tại location**. [UNVERIFIED] Submit REST → poll → download | [TESTED] Public catalog/form 200; execution không key → 401. [UNVERIFIED] Cần ECMWF/CDS account, PAT và chấp nhận licence | [TESTED] Form/constraints hiện cho tới **04/11/2026**, GET ~1 giây. [UNVERIFIED] Queue/result size chưa đo | [TESTED] `scripts/data/fetch_era5_cds.py`; `~/.cdsapirc` hoặc `CDSAPI_KEY`, **không dùng Earthdata** |
| Mặn SIWRR / SIWRP / MRC | [TESTED] PDF bản tin công khai; SIWRR có cả kết quả thực đo Vàm Cỏ. [UNVERIFIED] Chưa có feed điểm 4 site dạng JSON/CSV được xác minh | [TESTED] SIWRR PDF/SIWRP HTML/MRC portal truy cập không auth; MRC data-services lỗi mạng từ máy này | [TESTED] PDF 1.153.136 byte/~1 giây; PDF mùa khô 6.110.139 byte/~1 giây. [UNVERIFIED] Không có latency cập nhật chuỗi quan trắc để cam kết | [TESTED] `scripts/data/probe_salinity.py`; cache `salinity=null`, không thay bằng 0 hay đổi ‰ thành EC tùy tiện |

## NEX: AWS range chạy được, nhưng subset server tiết kiệm hơn

[TESTED] Bucket listing: [S3 root](https://nex-gddp-cmip6.s3.amazonaws.com/?list-type=2&delimiter=/). Layout thực:

```text
NEX-GDDP-CMIP6/<model>/<ssp>/r1i1p1f1/<variable>/
  <variable>_day_<model>_<ssp>_r1i1p1f1_gn_<year>_v2.0.nc
```

[TESTED] Ví dụ ACCESS-CM2/ssp245/2025: tasmax **246.259.972 byte**, pr **218.420.721 byte**; shape `(365,600,1440)`, chunk `(1,600,1440)`. HTTP `Range` trả **206**. Probe tasmax đọc 3 ngày/4 điểm, tải **2.045.700 byte / 43 GET / 16,574 giây** (gồm metadata). Probe pr đọc 2 ngày, **1.206.934 byte / 49 GET / 15,088 giây**. Kết quả và tọa độ ô trong `nex-range-probe.json`, `nex-pr-range-probe.json`, `nex-mpi-range-probe.json`.

[TESTED] Range là khả thi kỹ thuật nhưng không giảm nhiều byte cho **cả chuỗi năm**: mỗi ngày là một chunk nén toàn cầu, phải đọc chunk chứa điểm. Listing đủ 2 model × 2 SSP × 2 biến × 26 năm = **208 object, 47.681.004.654 byte** global. [UNVERIFIED] Chỉ phần truyền 47,68 GB trong 20 phút đã đòi ~39,7 MB/s liên tục, chưa tính hàng chục nghìn range GET/giải nén; không cam kết mốc 20 phút với S3 tại máy này. Không tải cả bộ global để thử.

[TESTED] [NCCS công bố dịch vụ THREDDS/NCSS của cùng NEX](https://nccs.smce.nasa.gov/data-collections/nex-gddp-cmip6/). Endpoint **phải có `/ncss/grid/`**; `/ncss/` đơn thuần trả 404 trong thử nghiệm. Ví dụ đã trả 365 dòng ngày, không auth:

```text
https://ds.nccs.nasa.gov/thredds/ncss/grid/AMES/NEX/GDDP-CMIP6/
ACCESS-CM2/ssp245/r1i1p1f1/tasmax/
tasmax_day_ACCESS-CM2_ssp245_r1i1p1f1_gn_2025_v2.0.nc
?var=tasmax&latitude=10.03&longitude=105.78
&time_start=2025-01-01T00%3A00%3A00Z&time_end=2025-12-31T23%3A59%3A59Z&accept=csv
```

[TESTED] Script lấy model **ACCESS-CM2, MPI-ESM1-2-HR**, `ssp245`, `ssp585`, tasmax/pr. Tháng tasmax = trung bình Tmax ngày trừ 273,15, đơn vị °C; tháng pr = tổng flux ngày × 86.400, mm/tháng. Script kiểm tra unit, số ngày từng tháng/năm nhuận, fill/NaN/âm, phiên bản; tháng không đủ dữ liệu sẽ lỗi, không âm thầm cộng thiếu. `probability=null`, evidence `PROJECTION`; không coi ngày mô phỏng là dự báo thời tiết.

[TESTED] Đã đối chiếu trực tiếp AWS range với NCSS: ACCESS-CM2 tasmax 3 ngày và pr 2 ngày tại **cả bốn điểm**, MPI-ESM1-2-HR tasmax 1 ngày tại Cần Thơ; ô lưới khớp và giá trị khớp trong sai số làm tròn CSV. Bằng chứng: `nex-range-comparison.json` (9 tổ hợp model/biến/site). Đây là kiểm tra tính nhất quán đường truy cập, không phải kiểm định độ chính xác mô hình khí hậu.

[TESTED] Ô NEX gần nhất đã đọc bằng AWS range:

| Site | Điểm yêu cầu lat,lon | Ô lat,lon |
|---|---|---|
| [TESTED] `cantho` | 10.03,105.78 | 10.125,105.875 |
| [TESTED] `chaudoc` | 10.70,105.12 | 10.625,105.125 |
| [TESTED] `bentre` | 10.10,106.45 | 10.125,106.375 |
| [TESTED] `soctrang` | 9.55,106.20 | 9.625,106.125 |

## IMERG: URL và đơn vị

[TESTED] CMR mới nhất trả `...20261111-S000000-E235959.V07C.nc4`, collection `C2723754859-GES_DISC`, link dịch vụ:

```text
https://opendap.earthdata.nasa.gov/collections/C2723754859-GES_DISC/granules/
GPM_3IMERGDL.07%3A3B-DAY-L.MS.MRG.3IMERG.20261111-S000000-E235959.V07C.nc4
```

[TESTED] DDS/DAS trên host `gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3/GPM_3IMERGDL.07/YYYY/MM/<filename>` xác nhận `precipitation[time=1][lon=3600][lat=1800]`, **mm/day**, fill `-9999.90039`; không nhân 24 thêm. `.ascii?precipitation%5B0:1:0%5D...` tới URS/401; dấu `[`/`]` không encode gây HTTP 400 từ Tomcat. Xem `imerg-legacy-probe.json`, `imerg-cloud-probe.json`.

[UNVERIFIED] Script chọn ô 0,1° gần nhất, tie chọn hướng bắc/đông; subset hình chữ nhật nhỏ đủ bốn điểm rồi tách scalar (không lấy trung bình vùng), cache raw theo granule/version. Dạng ASCII/parser và OAuth cookie đã kiểm tra bằng fixture/mock; **chưa xác minh giá trị thật sau login**, kể cả giới hạn tốc độ cho hàng nghìn ngày. Giá trị có mặt không đồng nghĩa đã qua QA; giữ nhãn `VALUE_PRESENT_QA_NOT_EVALUATED`. Giovanni là lựa chọn tương tác, chưa kiểm chứng API batch và không cần cho script này.

## AppEEARS: task đã chuẩn bị, chưa submit

[TESTED] Base `https://appeears.earthdatacloud.nasa.gov/api`; `/product` và `/product/{product}` 200. Layer name chính xác từ catalog:

| Product | Layer |
|---|---|
| [TESTED] `SPL4SMGP.008` | `Geophysical_Data_sm_surface`, `Geophysical_Data_sm_rootzone` |
| [TESTED] `MOD13Q1.061` | `_250m_16_days_NDVI`, `_250m_16_days_EVI` |
| [TESTED] `MOD16A2GF.061` | `ET_500m` |

[TESTED] JSON đầy đủ bốn điểm nằm ở [appeears-task.json](appeears-task.json): `task_type="point"`, `params.coordinates=[{id,category,latitude,longitude},...]`, `params.layers=[{product,layer},...]`, `params.dates=[{startDate:"01-01-2015",endDate:"11-10-2026"}]`. Dry-run đã đối chiếu từng layer với catalog.

[UNVERIFIED] Luồng theo [API chính thức](https://appeears.earthdatacloud.nasa.gov/api/): `POST /login` Basic username/password → Bearer token; `POST /task` JSON → lưu `task_id`; `GET /task/{id}` tới `status=done`; `GET /bundle/{id}`; `GET /bundle/{id}/{file_id}` tải file, kiểm SHA256/size. Script resume task, refresh token khi 401, lưu nguyên CSV/QA/XML và JSON từng site; chưa có lượt login/task/download thật. Probe login không credentials trả 415 khi body rỗng, 400 khi JSON `{}`; không coi đó là test đăng nhập.

[TESTED] Catalog layer cho biết NDVI scale 0,0001, ET scale 0,1 và các mã fill; script lưu **nguyên giá trị CSV dịch vụ**, không tự nhân scale lần hai. [UNVERIFIED] Cần đọc metadata bundle/QA thực tế trước khi nối vào engine. SMAP không có Jan–Mar 2015; MOD16A2GF 2026 chưa có trong CMR đã kiểm tra; request dài không bảo đảm phủ kín mọi sản phẩm.

## ERA5: account và request

[TESTED] Dataset point tồn tại; `era5-requests.json` có request bốn site: `variable=["2m_temperature","total_precipitation"]`, `date=["2015-01-01/2026-11-04"]`, `location={longitude,latitude}`, `data_format="csv"`. Form hiện hành có `date/location`; process schema riêng không liệt kê đủ hai widget này, nên script đọc **form catalog** để kiểm tra date bounds. Không dựa vào temporal extent STAC cũ đang dừng năm 2024.

[UNVERIFIED] Đăng ký ECMWF/CDS, chấp nhận CC-BY trên trang dataset; lấy **personal access token** từ profile. Theo [hướng dẫn CDS](https://cds.climate.copernicus.eu/how-to-api), `~/.cdsapirc` chứa `url: https://cds.climate.copernicus.eu/api`, `key: <PERSONAL-ACCESS-TOKEN>`; không phải cặp UID:key cũ. Script cũng đọc `CDSAPI_KEY`.

[TESTED] REST OpenAPI và source client ECMWF đã đọc; execution không token trả 401. [UNVERIFIED] Script gửi `POST /api/retrieve/v1/processes/{dataset}/execution {"inputs":request}` với `PRIVATE-TOKEN`; lưu `jobID`, poll `/jobs/{id}`, tải asset từ `/jobs/{id}/results`, xử lý CSV/ZIP và từ chối cache nếu số ngày trả về không phủ khoảng liên tục. Chưa kiểm tra submit hợp lệ, size, queue hoặc schema CSV thật. Không gửi PAT theo URL tải bên ngoài. Nếu point dataset ngừng hoạt động, dataset gốc `reanalysis-era5-single-levels` là hướng thay thế dùng bbox nhỏ/NetCDF; đường fallback này chưa triển khai/kiểm chứng.

## Mặn: có tài liệu quan trắc, chưa có feed điểm

[TESTED] [PDF SIWRR 16–18/04/2026](https://www.siwrr.org.vn/docs/2023/files/20260504-BC-danh-gia-va-du-bao-moi-truong-nuoc-Vam-Co-Ngay-lay-mau-18_04_2026--Du-bao-29_04_2026.pdf) HTTP 200, có bảng tên trạm VC01–VC10 và biểu đồ mặn thực đo, phần sau là dự báo. `pdftotext` đọc được văn bản; PDF mô tả vùng **Vàm Cỏ**, không phải bốn điểm demo. Bản sao/text trong `siwrr-vamco-2026-04.pdf/.txt` để kiểm tra thủ công, không tự gán số cho Cần Thơ/Bến Tre.

[TESTED] [PDF mùa khô SIWRR](https://www.siwrr.org.vn/docs/2023/files/20251124-Ban-tin-mua-kho-2025-2026-DB-HTVH-CL-CB-24-11-2025.pdf) tải được; phần lớn trang không trích được text (bản trích chỉ 734 byte), không phải API chuỗi quan trắc. [SIWRP ĐBSCL](https://siwrp.org.vn/news/khu-vuc-dbscl_435.html) HTTP 200; chưa tìm được feed chuỗi mặn máy đọc được trong phạm vi kiểm tra.

[TESTED] [MRC portal](https://portal.mrcmekong.org/) HTTP 200 nhưng là HTML app, không chứng minh có data feed. Host [MRC Swagger](https://data-services.mrcmekong.org/) và `/api/v1/hfwqm`, `/api/v1/hfwqm/export`, `/v3/api-docs` đều lỗi **No route to host** từ môi trường này. [UNVERIFIED] Endpoint water-quality có cung cấp salinity/EC, cần auth hay không, trạm phủ ĐBSCL và historical export đều chưa xác minh; không kết luận dịch vụ ngừng toàn cầu hoặc salinity không tồn tại.

[TESTED] Kết luận thực dụng: **chưa lấy được quan trắc mặn point time series không auth cho 4 demo site**. Script audit lưu `status=UNAVAILABLE`, `salinity=null`, URL/status/error; không đưa PDF dự báo thành `OBSERVED_FIELD`. [UNVERIFIED] Muốn dùng bản tin cần người kiểm tra trạm, thời điểm, quan trắc/dự báo, đơn vị và quyền sử dụng trước khi nhập tay.

## Chạy lại và cache

[TESTED] Các fetcher chính chỉ cần Python + `httpx`; đã chạy với `uv run --no-project --with httpx python ...`. Riêng **probe AWS HDF5** cần thêm `h5netcdf` + backend `h5py` (kéo numpy); không cần fsspec cho phương án NCSS. Không cần cài AWS CLI/CDS SDK/AppEEARS SDK.

[TESTED] Mặc định cache các script là `backend/data/cache/<source>/<site>.json`, source lần lượt `nex_cmip6`, `imerg_late`, `appeears`, `era5`, `salinity`. **Trong lượt này luôn override sang `docs/research/demo-cache`** khi có ghi cache, để không đụng backend. NEX/IMERG lưu thêm raw để resume; AppEEARS/CDS giữ task/job ID. Credential chỉ đọc, không lưu token/password trong cache.

[TESTED] Lệnh đã chạy không cần credentials:

```bash
uv run --no-project --with httpx python scripts/data/fetch_nex_cmip6.py --sites cantho --cache-root docs/research/demo-cache
uv run --no-project --with httpx python scripts/data/fetch_nex_cmip6.py --sites chaudoc bentre soctrang --models ACCESS-CM2 --start-year 2025 --end-year 2025 --workers 1 --cache-root docs/research/demo-cache
uv run --no-project --with httpx --with h5netcdf --with h5py python scripts/data/probe_nex_ranges.py
uv run --no-project --with httpx python scripts/data/fetch_imerg.py --probe --legacy --start 2026-11-10 --end 2026-11-10
uv run --no-project --with httpx python scripts/data/fetch_appeears.py --dry-run
uv run --no-project --with httpx python scripts/data/fetch_era5_cds.py --dry-run
uv run --no-project --with httpx python scripts/data/probe_salinity.py --cache-root docs/research/demo-cache
```

[UNVERIFIED] Sau khi có credentials, lệnh chạy thật (mặc định ghi backend cache):

```bash
# ~/.netrc: machine urs.earthdata.nasa.gov login USER password PASS
# chmod 600 ~/.netrc
uv run --no-project --with httpx python scripts/data/fetch_appeears.py
uv run --no-project --with httpx python scripts/data/fetch_imerg.py --start 2026-11-01 --end 2026-11-10
uv run --no-project --with httpx python scripts/data/fetch_era5_cds.py --start 2025-01-01 --end 2025-01-07
```

[TESTED] Bằng chứng HTTP/metadata: `access-probes.json`, các `*-probe.json`; request: `appeears-task.json`, `era5-requests.json`; tiến độ NEX: `nex-download.log`, `nex-other-sites.log`. Kết quả kiểm tra dữ liệu cuối cùng được ghi riêng trong `verification.txt`.

[TESTED] Tám file Python parse/lint thành công (`ruff check --no-cache scripts/data`). `verify_data_access.py` kiểm tra độc lập 2.496 tháng, mock bảo đảm Basic credential chỉ tới URS, parser IMERG scalar/window/fill/HTML, CSV/ZIP và từ chối ERA5 chỉ có ngày đầu/cuối thay vì khoảng liên tục. Fetch IMERG/AppEEARS thiếu `~/.netrc` đã được chạy và dừng trước submit/data cache; các test mock không thay thế lượt tải có credential.

[TESTED] Public CDS `costing` trả 200 cho cả danh sách hai ngày và chuỗi range `start/end`, nhưng cost khác nhau (144 so với 72 cho ví dụ 2 ngày/2 biến). Xem `era5-costing-probe.json`. [UNVERIFIED] Costing không chứng minh dữ liệu đủ khoảng; script dùng range và kiểm tra coverage sau tải, nên cần smoke-test tuần ngắn sau khi có PAT trước khi yêu cầu nhiều năm CSV.
