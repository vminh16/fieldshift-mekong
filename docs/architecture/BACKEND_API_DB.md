# 02 — Thiết kế Backend, API, DB (bản hackathon)

> **Vị trí code trong repo:** `apps/api/src/fieldshift/` — `api/v1/` (routes), `api/schemas/requests.py`, `application/use_cases/plan_rotation.py`, `domain/engines/{rotation_planner,future_outlook,field_state}.py`, `domain/catalog.py` + `resources/{crops,regions}.json`, `infrastructure/crop_models/fao56_water.py`, `infrastructure/data_sources/{context_builder,cache}.py`, `nasa/{power,nasadem}.py`, `local/soilgrids.py`, `infrastructure/persistence/sqlite.py`. Prefix API là `/v1` (không phải `/api/v1`). Cây thư mục `backend/` bên dưới là bản nháp ban đầu.

> Dựa trên `FieldShift_Mekong_Solution_Design_v2.md` + `01-phan-tich-du-lieu.md`. Mục tiêu: FE có **hợp đồng API cố định ngay hôm nay** để mock; backend lắp vào trong ngày thi.
> Nguyên tắc: Modular Monolith, ít file nhất, cache-first, mọi số có evidence. Không microservice, không queue, không auth phức tạp.

## 1. Stack đề xuất

| Thành phần | Chọn | Vì sao |
|---|---|---|
| Ngôn ngữ | Python 3.12 | Hệ sinh thái dữ liệu khí hậu; team data viết thẳng được |
| Web | FastAPI + Pydantic v2 | Sinh OpenAPI tự động (`/docs`) → FE đọc contract trực tiếp |
| DB | **SQLite** (1 file) + cột JSON | Zero-ops, demo offline. Đổi sang Postgres chỉ bằng URL nếu cần deploy nhiều người |
| HTTP client | `httpx` | Gọi POWER/OpenTopoData |
| Quản lý gói | `uv` | Đã có sẵn trên máy |
| Deploy demo | `uvicorn` trên laptop + tunnel (cloudflared/ngrok) hoặc Render/Railway | FE gọi qua 1 base URL |

Không dùng: PostGIS (geometry lưu GeoJSON trong JSON là đủ cho vài thửa), Celery/Redis (mô phỏng 3 vụ × ~20 chuỗi × 5 kịch bản chạy < 1 s bằng Python thuần), ORM nặng (SQLModel/SQLAlchemy chỉ nếu team quen).

## 2. Cấu trúc thư mục (rút gọn từ Phụ lục A)

```text
backend/
  app/
    main.py            # FastAPI app + routes (L1/L2)
    schemas.py         # Pydantic: PlanRequest, DecisionPackage, ... (contract)
    db.py              # sqlite3 + bảng
    domain/
      evidence.py      # Evidence, UnitValue, Status enums
      context.py       # Context Builder: POWER/SRTM/soil → FieldContext
      state.py         # Field State Estimator
      scenarios.py     # CLIMATOLOGY + STRESS_TEST (analog-year, delta)
      catalog.py       # load crops.json, season windows
      feasibility.py   # HARD/SOFT/UNKNOWN rules
      generator.py     # enumerate sequences 3 vụ
      water.py         # FAO-56 water balance (ET0 PM, Kc, rice paddy)
      planner.py       # Pareto + priorities + status
      explain.py       # lý do, rủi ro, checklist
    adapters/
      power.py         # NASA POWER client + cache
      terrain.py       # OpenTopoData SRTM
      soil.py          # SoilGrids + fallback prior
  data/
    crops.json         # catalog có source từng tham số
    regions.json       # RegionProfile ĐBSCL, season windows
    cache/             # JSON POWER đã tải
  tests/test_engine.py # invariant tests (baseline luôn có, không bịa EC, ...)
```

Port/Adapter: mỗi adapter là **một hàm** `fetch(...) -> dict` trả dữ liệu + evidence; domain chỉ nhận dict đã chuẩn hóa. Không cần lớp interface trừ khi có 2 implementation thật.

## 3. Mô hình DB (SQLite)

Bảng tối thiểu. Kết quả quyết định là **snapshot bất biến** (JSON), không chuẩn hóa thành nhiều bảng — đúng §13.3 "tái lập".

```sql
CREATE TABLE fields (
  id TEXT PRIMARY KEY,                 -- 'fld_...'
  name TEXT NOT NULL,
  region_id TEXT NOT NULL DEFAULT 'mekong',
  lat REAL NOT NULL CHECK (lat BETWEEN -90 AND 90),
  lon REAL NOT NULL CHECK (lon BETWEEN -180 AND 180),
  geometry JSON,                       -- GeoJSON polygon (tùy chọn)
  area_ha REAL CHECK (area_ha > 0),
  profile JSON NOT NULL,               -- FieldProfile: baseline, irrigation, drainage, soil_reported, constraints
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE observations (            -- phép đo của người dùng: ECw, pH, mưa, ngày thu hoạch...
  id TEXT PRIMARY KEY,
  field_id TEXT NOT NULL REFERENCES fields(id),
  variable TEXT NOT NULL,              -- 'canal_ecw', 'soil_ph', 'drainage', 'season_closed'
  value REAL, value_text TEXT,
  unit TEXT,                           -- 'dS/m', 'pH', ...
  observed_at TEXT NOT NULL,
  evidence_kind TEXT NOT NULL CHECK (evidence_kind IN ('OBSERVED_FIELD','REPORTED_BY_FARMER')),
  note TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE source_cache (            -- cache-aside cho NASA/khác
  key TEXT PRIMARY KEY,                -- 'power:daily:10.03:105.78:2001-01-01:2026-11-09:v2.10.1'
  source TEXT NOT NULL,                -- 'NASA_POWER', 'SRTM', 'SOILGRIDS'
  fetched_at TEXT NOT NULL,
  valid_until TEXT,
  meta JSON NOT NULL,                  -- version, resolution, coverage
  payload JSON NOT NULL
);

CREATE TABLE field_states (            -- snapshot FieldState theo as_of
  id TEXT PRIMARY KEY,
  field_id TEXT NOT NULL REFERENCES fields(id),
  as_of TEXT NOT NULL,
  state JSON NOT NULL,                 -- biến + provenance + unknowns
  created_at TEXT NOT NULL
);

CREATE TABLE decisions (               -- DecisionPackage bất biến; what-if/replan = bản mới
  id TEXT PRIMARY KEY,                 -- 'dec_...'
  field_id TEXT NOT NULL REFERENCES fields(id),
  parent_id TEXT REFERENCES decisions(id),   -- what-if/replan trỏ về bản gốc
  kind TEXT NOT NULL CHECK (kind IN ('PLAN','WHAT_IF','REPLAN')),
  request JSON NOT NULL,               -- PlanRequest
  field_state_id TEXT NOT NULL REFERENCES field_states(id),
  versions JSON NOT NULL,              -- {catalog, rules, water_model, planner, data}
  package JSON NOT NULL,               -- DecisionPackage đầy đủ (gồm outcomes, trajectories)
  created_at TEXT NOT NULL
);
CREATE INDEX ix_decisions_field ON decisions(field_id, created_at);
```

Catalog cây và vùng: **file JSON có version** (`data/crops.json`, `data/regions.json`), không cần bảng — đọc lúc khởi động. Chỉ đưa vào DB nếu có màn admin sửa catalog (YAGNI).

## 4. API (REST, prefix `/v1`)

| Method | Path | Mục đích | UC/AC |
|---|---|---|---|
| GET | `/health` | sống + trạng thái nguồn (cache tuổi bao nhiêu, API live?) | UC-09 |
| GET | `/sources` | danh sách nguồn, coverage, độ phân giải, `status: LIVE|CACHED|UNAVAILABLE` | PS-08 |
| GET | `/crops` | catalog cây (có `source`, `limitations`) | PS-02 |
| GET | `/regions/{id}` | season windows, cấu hình vùng | §2.2 |
| POST | `/fields` | tạo thửa (lat/lon, baseline, profile) | Journey 1–2 |
| GET | `/fields/{id}` | thửa + quan sát mới nhất | |
| PATCH | `/fields/{id}` | sửa profile/ưu tiên | |
| POST | `/fields/{id}/observations` | thêm đo ECw, pH, đóng vụ... | UC-08 |
| GET | `/fields/{id}/context?as_of=` | FieldContext: khí hậu tóm tắt, ẩm đất, địa hình, đất, **known/unknown** | Journey 3, Phase 0 exit |
| POST | `/plans` | `PlanRequest` → `DecisionPackage` (đồng bộ, < 2 s) | AC-01 |
| GET | `/plans/{id}` | đọc lại DecisionPackage | §13.3 |
| POST | `/plans/{id}/what-if` | `ScenarioOverride` hoặc đổi ưu tiên → DecisionPackage **mới** (`parent_id`) | §11.4, AC-09 |
| POST | `/plans/{id}/replan` | sau vụ 1: giữ lịch sử, đề xuất từ vụ 2 | AC-10 |
| GET | `/plans/{id}/twin?sequence_id=&scenario_id=&member=` | timeline theo tuần cho Twin, **cắt từ cùng package** | AC-09 |
| GET | `/plans/{id}/twin-compare?sequence_id=&scenario_id=&member=` | baseline và phương án cùng member/năm và trục tuần | AC-09 |
| GET | `/plans/{id}/export` | tóm tắt 1 trang (HTML in được) | §11.5 |

Lỗi: `{"error": {"code": "LOCATION_INVALID", "message": "...", "gate": "G1"}}`. **Gate fail ≠ HTTP lỗi**: thiếu EC vẫn trả 200 với `decision_status = CONDITIONAL_PENDING_CHECK` (§13.2 fail-safe).

### 4.1. Enum dùng chung (FE phải xử lý đủ)

```text
DecisionStatus   = RECOMMEND_FOR_CONSIDERATION | CONDITIONAL_PENDING_CHECK | NOT_FEASIBLE | INSUFFICIENT_EVIDENCE
ScenarioKind     = FORECAST | CLIMATE_PROJECTION | CLIMATOLOGY | STRESS_TEST
EvidenceKind     = OBSERVED_FIELD | OBSERVED_REMOTE_ESTIMATE | MODEL_ESTIMATE | FORECAST | PROJECTION | ASSUMPTION | LITERATURE_RULE
ValueOrigin      = measured_at_field | reported_by_farmer | estimated_from_regional_data | inferred_by_model | assumed_scenario | unknown
RuleSeverity     = HARD | SOFT | UNKNOWN_REQUIRES_CHECK
ClaimType        = QUANTITATIVE_MODEL | POTENTIAL_QUALITATIVE | UNAVAILABLE
DisplayLabel(VI) = "Đo tại ruộng" | "Ước lượng vùng" | "Dự kiến" | "Kịch bản" | "Chưa biết"
```

### 4.2. Kiểu giá trị — quy tắc "không có số giả"

Mọi số hiển thị đều là `Measure`, không bao giờ là số trần:

```json
{ "value": 412.5, "unit": "mm", "origin": "inferred_by_model",
  "evidence_ids": ["ev_power_daily", "ev_fao56_kc_rice"], "label": "Dự kiến" }
```
Thiếu dữ liệu: `{ "value": null, "unit": "dS/m", "origin": "unknown", "reason": "CANAL_ECW_NOT_MEASURED", "label": "Chưa biết" }`.

### 4.3. `POST /plans` — request

```json
{
  "field_id": "fld_cantho_01",
  "as_of": "2026-11-14",
  "horizon_seasons": 3,
  "baseline": ["rice", "rice", "rice"],
  "priorities": ["save_water", "avoid_crop_failure", "soil_health"],
  "constraints": { "no_new_machinery": true, "budget_limit_vnd": null, "irrigation": "canal_limited" },
  "outlook_modes": ["CLIMATOLOGY", "STRESS_TEST"]
}
```

### 4.4. `POST /plans` — response `DecisionPackage` (rút gọn, đủ để FE mock)

```json
{
  "decision_id": "dec_01",
  "parent_id": null,
  "field_id": "fld_cantho_01",
  "as_of": "2026-11-14",
  "versions": { "catalog": "crops-2026.11.0", "rules": "rules-1", "water_model": "fao56-v1", "planner": "pareto-v1", "data": "power-v2.10.1@2026-11-09" },
  "gates": [
    { "gate": "G5", "passed": false, "message": "Chưa đo ECw nước kênh; không khẳng định an toàn mặn." },
    { "gate": "G6", "passed": false, "message": "Không có dự báo mùa được kiểm chứng; dùng climatology + kịch bản." }
  ],
  "scenarios": [
    { "scenario_id": "sc_clim", "kind": "CLIMATOLOGY", "name": "Trung bình 2001–2025", "probability": null, "probability_semantics": "NONE", "assumptions": [], "evidence_ids": ["ev_power_daily"] },
    { "scenario_id": "sc_dry2016", "kind": "STRESS_TEST", "name": "Lặp lại mùa khô 2016", "probability": null, "probability_semantics": "NONE_ASSUMPTION", "assumptions": ["analog_year_2016"], "evidence_ids": ["ev_power_daily"] },
    { "scenario_id": "sc_salt_early", "kind": "STRESS_TEST", "name": "Mặn đến sớm 4 tuần", "probability": null, "probability_semantics": "NONE_ASSUMPTION", "assumptions": ["salinity_onset_minus_4w_user_defined"], "evidence_ids": [] }
  ],
  "baseline": { "sequence_id": "seq_rice_rice_rice", "status": "EVALUATED" },
  "options": [
    {
      "sequence_id": "seq_rice_mungbean_rice",
      "is_baseline": false,
      "strategy_tag": "save_water",
      "decision_status": "CONDITIONAL_PENDING_CHECK",
      "seasons": [
        { "index": 1, "window": "dong_xuan", "crop": "rice", "sow": "2026-11-25", "harvest": "2027-03-05" },
        { "index": 2, "window": "xuan_he", "crop": "mungbean", "sow": "2027-03-15", "harvest": "2027-05-25" },
        { "index": 3, "window": "he_thu", "crop": "rice", "sow": "2027-06-05", "harvest": "2027-09-10" }
      ],
      "metrics": {
        "sc_clim":    { "irrigation_need": {"value": 610, "unit": "mm", "origin": "inferred_by_model", "label": "Dự kiến"},
                        "water_stress_days": {"value": 6, "unit": "day", "origin": "inferred_by_model", "label": "Dự kiến"},
                        "heat_stress_days_sensitive_stage": {"value": 2, "unit": "day", "origin": "inferred_by_model", "label": "Dự kiến"} },
        "sc_dry2016": { "irrigation_need": {"value": 740, "unit": "mm", "origin": "assumed_scenario", "label": "Kịch bản"} }
      },
      "delta_vs_baseline": { "sc_clim": { "irrigation_need": {"value": -380, "unit": "mm"} } },
      "soil_benefit": { "claim_type": "POTENTIAL_QUALITATIVE", "value": null, "indicators": ["legume_n_fixation_potential", "crop_diversity_+1"] },
      "reasons": [
        { "text": "Vụ giữa (T3–T5) thiếu nước khí hậu ~480 mm; đậu xanh cần ít nước hơn lúa.", "evidence_ids": ["ev_power_daily", "ev_fao56_kc_mungbean"] }
      ],
      "risks": [
        { "code": "DRAINAGE_UNCONFIRMED", "severity": "UNKNOWN_REQUIRES_CHECK", "text": "Cây cạn cần thoát nước tốt; chưa xác nhận." },
        { "code": "SALINITY_UNKNOWN", "severity": "UNKNOWN_REQUIRES_CHECK", "text": "Chưa đo ECw." }
      ],
      "triggers": [
        { "condition": "canal_ecw > 2.0 dS/m trước 2027-03-15", "measure": "ECw nước kênh", "unit": "dS/m", "action": "Không gieo vụ 2; tái lập kế hoạch" }
      ],
      "checklist": ["Đo ECw nước kênh (dS/m)", "Kiểm tra thoát nước sau mưa 24 h", "Xác nhận nguồn giống đậu xanh & đầu ra"]
    }
  ],
  "excluded": [
    { "sequence_id": "seq_rice_watermelon_rice", "rule_id": "R_SEASON_OVERLAP", "severity": "HARD",
      "reason": "Thu hoạch dưa hấu vượt cửa sổ vụ 3", "inputs_used": ["season_windows.he_thu", "crops.watermelon.duration"], "how_to_resolve": "Gieo vụ 2 sớm hơn 10 ngày" }
  ],
  "evidence": {
    "ev_power_daily": { "kind": "OBSERVED_REMOTE_ESTIMATE", "source": "NASA POWER Daily (MERRA-2)", "version": "v2.10.1",
      "spatial_scale": "regional", "resolution": "0.5x0.625 deg", "time_scope": ["2001-01-01", "2026-11-09"],
      "limitations": ["Ô lưới ~50 km, không phải đo tại thửa"] },
    "ev_fao56_kc_mungbean": { "kind": "LITERATURE_RULE", "source": "FAO-56 Table 12", "limitations": ["Giá trị tham khảo chung, chưa hiệu chỉnh giống địa phương"] }
  },
  "disclaimer": "Công cụ hỗ trợ tham khảo, không thay thế quyết định của nông dân và cán bộ khuyến nông."
}
```
*Số trong ví dụ là minh họa định dạng, không phải kết quả mô phỏng.*

### 4.5. `GET /plans/{id}/twin` — timeline

```json
{ "decision_id": "dec_01", "sequence_id": "seq_rice_mungbean_rice", "scenario_id": "sc_clim",
  "step": "week",
  "series": [
    { "date": "2026-11-25", "season_index": 1, "crop": "rice", "stage": "establishment",
      "root_zone_water": {"value": 0.82, "unit": "fraction_TAW", "label": "Dự kiến"},
      "salinity": {"value": null, "origin": "unknown", "label": "Chưa biết"},
      "stress_risk": "LOW",
      "irrigation_cum": {"value": 40, "unit": "mm", "label": "Dự kiến"} }
  ] }
```
Twin **chỉ cắt dữ liệu đã lưu** — không tải lại nguồn hoặc chạy mô hình (AC-09). `scenario_id`
mặc định `sc_clim`; `member` là chỉ số nguyên từ 0, chung giữa mọi chuỗi trong cùng kịch bản.
Bỏ `member` → chọn member có tổng tưới ở vị trí giữa (nếu số member chẵn, chọn vị trí giữa trên),
giữ cách chọn mặc định trước đây. Twin bổ sung `member`, `analog_year`, `members` và `events`.
FORECAST có `analog_year: null` và `member_label` (ID ensemble gốc); năm POWER dùng nối dữ liệu
không được hiển thị thành một năm dự báo quan trắc.

`members = [{member, year, irrigation_mm, label_vi}]` liệt kê tất cả member của chuỗi/kịch bản.
Với analog, `label_vi` đánh dấu **Năm hạn / Năm bình thường / Năm ướt** bằng thứ hạng tổng mưa
**tháng 12 năm bắt đầu → tháng 4 năm kế tiếp** trong toàn bộ analog `sc_clim`, không dùng lượng
tưới để gán tên năm (không gọi năm ít khô nhất trong `sc_dry` là năm ướt). Các năm còn
lại mang nhãn `Năm tham chiếu`; số lượng ít có thể không đủ cả ba nhãn. Nhãn khô/ướt ghi khoảng
năm, ví dụ `Năm hạn như 2015–2016`. FORECAST chỉ dùng nhãn member, không gán nhãn hạn từ năm analog
nối đuôi. CLIMATE_PROJECTION vẫn ghi năm analog nền; không diễn giải đó là năm tương lai.

Weekly rows bổ sung các **Measure** `ponding_mm` (trung bình các ngày trồng lúa trong tuần),
`irrigation_week`, `rain_week` (tổng mm trong tuần) và `root_depth_m` (độ sâu rễ tại ngày đầu có cây
trong tuần, từ đường cong tăng trưởng FAO-56). `root_zone_water` giữ nguyên; `ponding_mm.value`
là null với `reason=NOT_PADDY` cho cây cạn/nghỉ đất. Hàng ngày của adapter FAO-56 có `ponding_mm`
cho lúa, `depletion_mm` và `taw_mm` cho cây cạn (và bucket nghỉ đất), cùng `root_depth_m`.
Các trường nước không áp dụng cho chế độ cây hiện tại là null.

`events = [{date, type, season_index, crop}]`: `sow` / `harvest` giữ ngày lịch chính xác và vụ/cây;
`salinity_season_start` / `salinity_season_end` là ranh giới mùa mặn theo vùng/kịch bản trong
horizon chung, có `season_index: null, crop: null`. Đây là mùa mặn giả định theo lịch vùng,
không phải số đo ECw. Số đo kênh vẫn null nếu chưa đo.

`GET /plans/{id}/twin-compare` trả `{baseline: twin, option: twin}`. Khi thiếu `member`, **chọn
member trung vị của option rồi dùng cùng member đó cho baseline**. Hai series dùng lưới 7 ngày
từ `as_of` tới ngày thu hoạch cuối trong shortlist; ngày giống nhau kể cả khi đổi ngày gieo hay
độ dài vụ. `irrigation_cum` ở endpoint mới cộng dồn **cả kế hoạch**. Tuần không có cây có
`season_index/crop/stage: null`, các Measure về cây/nước ruộng null (`NO_ACTIVE_CROP`); mưa vẫn
được tính và tưới tuần bằng 0. Tuần có thu hoạch rồi gieo cây khác vẽ cây sau, cộng tưới của cả hai.
Endpoint `/twin` giữ tuần bắt đầu tại ngày gieo từng vụ và `irrigation_cum` cộng dồn **trong vụ**.
Khoảng trống giữa vụ không có ước lượng ẩm đất bổ sung.

Lưu trữ: `package.member_trajectories[sequence_id][scenario_id]` chứa các weekly aggregates số
gọn cho mọi member và hai lưới tuần; các aggregate được lấy ngay từ **lần Evaluator đã chạy**.
`package.trajectories` giữ lát mặc định để tương thích. Cả hai không xuất hiện trong response
`POST/GET /plans`; priority-only what-if giữ nguyên chúng. Decision cũ chưa có member data vẫn
đọc được Twin mặc định, nhưng chọn member/compare trả 404 `MEMBER_NOT_FOUND` và cần lập plan mới.
Member âm/không nguyên trả 422; member vượt phạm vi hoặc sequence/scenario không có trả 404.

### 4.5.1. Phân bố và câu tóm tắt cho simulation UI

Baseline **và mỗi option** bổ sung:

```json
{"distribution": {"sc_clim": [
  {"member": 0, "year": 2001, "irrigation_mm": 1747, "water_stress_days": 0, "heat_stress_days": 4}
]}}
```

Mỗi scenario đều có phân bố. `year` là **năm bắt đầu analog** cho CLIMATOLOGY, STRESS_TEST và
CLIMATE_PROJECTION; FORECAST có `year: null` cùng `member_label`. Đây là kết quả toàn chuỗi
từ các Evaluator runs đã tính metrics, không chạy thêm mô phỏng. Số liệu mỗi dot là int.
Để median của dots bằng chính xác p50 mm hiện hữu (kể cả ensemble chẵn), grid làm tròn mm được
dịch tối đa 0,5 mm về p50 trước khi làm tròn; chênh lệch mỗi dot so với tổng mô hình tối đa 1 mm.
Không thay đổi metrics/p50/p90 hay kết quả chọn phương án. Stress days giữ số nguyên chính xác.

Mỗi option có `summary_vi`: tên vụ/cây thay đổi + lý do đầu tiên trong `reasons`, thêm yêu cầu
xác nhận thoát nước **chỉ khi** đã có rule `R_DRAINAGE_UNKNOWN`. Không tạo thêm khẳng định
năng suất, lợi nhuận hay an toàn mặn. Fixtures thật: `contracts/fixtures/plan_cantho.json`,
`twin_cantho.json`, `twin_compare_cantho.json` (các số trong ví dụ trên chỉ minh họa định dạng).

### 4.6. `POST /plans/{id}/what-if`

```json
{ "override": { "rain_delta_pct": -30, "temp_delta_c": 1.5, "salinity_onset_shift_weeks": -4,
                "sow_shift_days": { "2": -10 }, "irrigation_cap_mm": null },
  "priorities": null }
```
Chỉ đổi `priorities` → chạy lại planner trên outcome cũ; đổi thời tiết/mặn → chạy lại water + planner; đổi ngày gieo → feasibility + mô phỏng lại (§11.4). Kết quả luôn là decision mới có `parent_id`.

## 5. Engine MVP — thuật toán cụ thể

1. **Context**: POWER daily (cache) → ET0 PM FAO-56 ngày (công thức đầy đủ, Ra theo vĩ độ & ngày năm); SRTM 1 điểm; soil prior.
2. **Scenarios** (giữ thứ tự ngày thật): `sc_clim` = chạy **trên từng năm 2001–2025** rồi lấy trung vị/P10/P90 (đây là phân bố lịch sử, *không* gọi là xác suất tương lai); `sc_dry` = analog năm khô (2005/2016/2024); `sc_hot` = +1.5 °C lên Tmax/Tmin rồi tính lại ET0; `sc_rain_minus30`; `sc_salt_early` = dời ngày mặn bắt đầu (tham số vùng, `ASSUMPTION`).
3. **Generator**: mỗi cửa sổ vụ × {cây trong catalog đủ tham số} × {gieo sớm/chuẩn/muộn ±10 ngày} → enumerate 3 vụ (≈ 7³×3³ ≤ 9 261, cắt bằng HARD rules trước → còn vài chục).
4. **Feasibility**: HARD = trùng lịch/vượt cửa sổ, thiếu máy bắt buộc; SOFT = giai đoạn nhạy cảm trùng tháng ≥35 °C, stress nước; UNKNOWN = ECw chưa đo cho cây nhạy mặn, thoát nước chưa xác nhận cho cây cạn.
5. **Water balance** ngày: cây cạn — bucket TAW/RAW, Ks (FAO-56 ch.8); lúa — lớp nước ruộng + thấm/rò (tham số vùng, ví dụ 2–4 mm/ngày, nhãn `ASSUMPTION`) + nước làm đất. Đầu ra: `irrigation_need`, `water_stress_days`, `heat_stress_days_sensitive_stage`. Không tính yield tuyệt đối (G7).
6. **Planner**: tiêu chí trên cùng scenario → Pareto front → gắn `strategy_tag` (save_water / low_risk / soil_support / balanced) → chọn 2–4 đa dạng, baseline luôn có. Ưu tiên nông dân **chỉ sắp xếp**, không tạo điểm tổng.
7. **Explain**: 2–3 lý do từ tiêu chí có delta lớn nhất + evidence_ids; rủi ro từ rules SOFT/UNKNOWN; checklist từ UNKNOWN.

## 6. Test invariant tối thiểu (`tests/test_engine.py`)

- Baseline luôn xuất hiện trong mọi package.
- Không option nào `RECOMMEND_FOR_CONSIDERATION` khi vi phạm HARD hoặc constraint cứng (AC-07).
- ECw chưa đo + cây nhạy mặn → `CONDITIONAL_PENDING_CHECK`, `salinity.value is None` (AC-02).
- Không có `FORECAST` scenario khi không có nguồn forecast; text không chứa "dự báo chắc chắn" (AC-03).
- Twin series = slice của package (AC-09).
- `-999` từ POWER → `UNKNOWN`, không thành 0.
- Cùng request + cùng cache → cùng package (reproducibility).

## 7. Việc FE có thể làm ngay

- Mock từ JSON §4.4/§4.5 (copy nguyên văn).
- Render theo `label` + `origin`, không tự tính số.
- Xử lý đủ 4 `DecisionStatus`, hiển thị `gates` thất bại như thông tin (không phải lỗi).
- Mặc định Decision View (baseline cạnh option, cùng `scenario_id`), Twin là tab phụ.

## 8. Lịch 2 ngày thi

| Thời điểm | Backend/Data | Kết quả kiểm tra |
|---|---|---|
| 14/11 sáng | `uv init`, schemas.py theo §4, db.py, adapters POWER/SRTM đọc cache, `/fields`, `/context` | FE gọi được `/context` thật |
| 14/11 chiều | crops.json + regions.json (có nguồn), scenarios, water balance, feasibility, generator | test invariant pass |
| 14/11 tối | planner + explain + `/plans` + `/twin` | E2E Cần Thơ & Sóc Trăng ra package khác nhau đúng lý do |
| 15/11 sáng sớm | `/what-if`, `/export`, ghép FE, deploy, quay video demo | demo offline chạy |
| **15/11 trước 11:00** | **Nộp bài** + khai báo AI tools & nguồn dữ liệu | |

## 9. Chênh lệch giữa bản triển khai và thiết kế (cập nhật 13/11)

- `source_cache` **không** làm bảng: cache là file JSON trong `backend/data/cache/<source>/` (đơn giản hơn, copy được, demo offline).
- Thêm endpoint `GET /fields`, `GET /fields/{id}/plans`.
- `PlanRequest.constraints` thêm `max_changed_seasons` (mặc định 1 theo UC-01) và `max_fallow_seasons` (mặc định 1). Nếu không có hai ràng buộc này, phương án "nghỉ đất cả 3 vụ" sẽ thắng vì tốn ít nước nhất, do chưa có mô hình thu nhập.
- Response `POST /plans` **không** kèm `trajectories`; FE lấy qua `/twin`. Mỗi option có thêm `rules` (toàn bộ luật đã áp), `strategy_name_vi`, `metrics[sid].per_season`, `irrigation_need_bad_year` (P90).
- Kịch bản thực tế: `sc_clim` (24 năm 2001–2025), `sc_dry` (3 mùa khô khô nhất tại điểm đó), `sc_hot` (+1.5 °C), `sc_rain_minus30`, `sc_salt_early` (mặn sớm 4 tuần), `sc_wet_ref`, và `sc_whatif` khi người dùng tự đặt.
- Trigger mặn hiển thị cả dS/m và ‰ (1 dS/m ≈ 0.64 ‰).
- JSON mẫu **thật** cho FE: `docs/fixtures/`.

## Changes in exp/api

- Available optional sources are wired in `application/use_cases/outlook_context.py`; domain engines consume normalized dictionaries and never import adapters. Existing fields/endpoints remain available; scenario metrics and `delta_vs_baseline` include every supplied scenario. `outlook_modes` retains its existing request metadata behavior; available sources are added automatically.
- `sc_forecast` is `FORECAST`, from [Open-Meteo Seasonal / ECMWF SEAS5](https://open-meteo.com/en/docs/seasonal-forecast-api), **non-NASA, [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/)**. `issue_time` comes from model initialization metadata, with `available_at`, `source`, ensemble/omitted member IDs, forecast window, assumptions and quality flags. Up to 180 days of Tmax/Tmin/rain members are spliced onto cycling POWER analog years; dew point/radiation/wind always use analog days. Incomplete/invalid members (including negative API rain) are omitted, never zero-filled. Probability is null; skill is not evaluated for Mekong. G6 passes only for a present forecast issued within 35 days of `as_of`; past `as_of`, future-issued/unavailable/stale forecasts fall back to climatology/stress tests (and any available projections).
- `sc_proj_<model>_<ssp>` is `CLIMATE_PROJECTION`: NEX-GDDP-CMIP6 v2 monthly Tmax differences and rain ratios, 2041–2050 relative to 2025–2034, applied to analog days. Tmin/dew point/radiation/wind stay unchanged. Probability is null. Cần Thơ has ACCESS-CM2/MPI-ESM1-2-HR × ssp245/ssp585; the other demo sites have only 2025, so projections are skipped with notes. These are long-term sensitivity scenarios, not forecasts for the plan dates.
- Field state adds `upstream_discharge` (m³/s, `context_only: true`), `upstream_discharge_anomaly` (%) and `upstream_discharge_trend` (m³/s/day), linked to `ev_glofas`. [Open-Meteo Flood / Copernicus GloFAS](https://open-meteo.com/en/docs/flood-api), non-NASA/CC-BY 4.0, at Tân Châu (10.80, 105.24): trailing seven-day mean vs the same calendar window in available 2001–2020 years. Latest value/trend remain available if history is missing; missing/stale values are null with reasons. Historical `as_of` does not use a subsequently retrieved run. Below-climatology discharge adds a coastal SOFT note recommending earlier ECw measurement; it never sets ECw or resolves `R_SALINITY_UNKNOWN`. These modeled regional values need local verification.
- `GET /v1/plans/{id}/status` returns `{decision_id, status: OK|REPLAN_REQUIRED, fired: [...]}` from new observations whose `observed_at` is strictly after the snapshot's `as_of` and whose record was created at/after the decision. Each trigger adds `variable`, `op` (`gt`/`eq`), `threshold`, `unit`, and `season_index` alongside its text. ECw comparisons require dS/m; drainage uses `value_text=poor` and a null unit. Status checks baseline and option triggers without modifying the stored decision; it does not automatically replan.
- Priority-only what-if reorders stored option summaries with the same strategy order used by a full run. The diverse shortlist is priority-independent (§6.7), so no data loading or simulation is necessary. The new immutable child preserves state, evidence, overrides and trajectories; `computation.mode=PRIORITIES_ONLY` reports zero simulations. Weather/management overrides retain the full evaluation path.
- G8 `EVIDENCE_COMPLETE` recursively checks numeric Measures in baseline/options, including deltas. Empty or unresolved evidence references cause `value=null`, `reason=EVIDENCE_INCOMPLETE_G8` and G8 failure with affected paths. Deltas add evidence/origin/label without changing their existing value/unit fields.
- Runtime caches use the existing cache-aside module. Bundled gzip responses for four seasonal cells and shared GloFAS current/history support offline tests; processed projection JSONs are packaged under `resources/projections/`. Refresh the Open-Meteo bundles manually with `python scripts/data/bundle_outlook.py` (network required). Attribution/limitations are in `ev_seasonal_forecast`, `ev_nex_cmip6`, `ev_glofas` and `data/catalog/sources.yaml`. Forecast skill and local hydrological/agronomic validity have **not** been evaluated.
