# FieldShift-Mekong — API contract v1 (cho FE & Digital Twin)

- Base URL: `VITE_API_BASE_URL` (mặc định `http://localhost:8000`), prefix **`/v1`**. JSON UTF-8. Swagger: `/docs`.
- Nguồn sự thật máy đọc: [`openapi.json`](openapi.json). Response thật để mock: [`fixtures/`](fixtures/) (Cần Thơ nội đồng, Sóc Trăng ven biển). TS types: [`types.ts`](types.ts).
- 4 ruộng mẫu có sẵn (chạy offline): `fld_cantho`, `fld_chaudoc`, `fld_bentre`, `fld_soctrang`.
- **Quy tắc thay đổi:** backend chỉ **thêm** field/endpoint, không đổi tên/xóa. FE phải bỏ qua field lạ và `scenario.kind` lạ.

## 1. Ba quy tắc FE bắt buộc

1. **Mọi con số là `Measure`**: `{value, unit, origin, label, evidence_ids, reason?}`. Hiển thị `value + unit` và chip `label` (`Đo tại ruộng` / `Ước lượng vùng` / `Dự kiến` / `Kịch bản` / `Chưa biết`). `value === null` → hiển thị **"Chưa biết"** + `reason`, **không** hiển thị 0.
2. **FE không tính khuyến nghị/trạng thái/số nước.** Chỉ được định dạng (mm → m³/ha ×10; dS/m → ‰ ×0.64 chỉ để hiển thị).
3. **So sánh luôn cùng kịch bản**: khi chọn `scenario_id`, baseline và phương án cùng lấy `metrics[scenario_id]` / twin cùng `scenario_id` + `member`.

## 2. Endpoints

| Method | Path | Dùng cho | Ghi chú |
|---|---|---|---|
| GET | `/health` | trạng thái API | |
| GET | `/sources` | danh sách nguồn dữ liệu & trạng thái | |
| GET | `/crops` | catalog cây (`name_vi`, thời gian sinh trưởng…) | |
| GET | `/regions/mekong` | cửa sổ vụ, mùa mặn, ruộng mẫu | |
| GET | `/fields` | danh sách ruộng | |
| POST | `/fields` | tạo ruộng `{name, lat 8–11.5, lon 104–107.5, area_ha?, profile}` | 201 |
| GET | `/fields/{id}` | ruộng + observations | |
| DELETE | `/fields/{id}` | xoá ruộng cùng observations, field_states, decisions của nó | 204; 404 `FIELD_NOT_FOUND` |
| PATCH | `/fields/{id}` | sửa `{name?, lat?, lon?, area_ha?, geometry?, profile?}` (merge profile) | lat/lon khi vẽ lại ranh giới |
| POST | `/fields/{id}/observations` | đo ECw: `{variable:"canal_ecw", value, unit:"dS/m", observed_at:"YYYY-MM-DD", evidence_kind:"OBSERVED_FIELD"}` | 0–60 dS/m, sai → 422 `ECW_OUT_OF_RANGE` |
| GET | `/fields/{id}/context?as_of=` | trạng thái ruộng + khí hậu tháng + evidence | ~0.1–15 s lần đầu |
| GET | `/fields/{id}/plans` | lịch sử decision của ruộng | |
| POST | `/plans` | **lập kế hoạch** → DecisionPackage | 2–4 s, 201 |
| GET | `/plans/{id}` | đọc lại decision (bất biến) | |
| POST | `/plans/{id}/what-if` | `{priorities?, override?}` → decision **mới** (`parent_id`) | chỉ đổi priorities → nhanh |
| POST | `/plans/{id}/evaluate` | `{crops: CropId[], sow_timing?: ("early"\|"standard")[], override?: ScenarioOverride}` (đúng số vụ của decision; `override` có thì thêm kịch bản `sc_whatif`) → decision **mới** WHAT_IF, `baseline` = chuỗi người dùng chọn, `request.evaluate_chain` | mô phỏng chuỗi tự chọn; 422 `CHAIN_LENGTH_MISMATCH`; twin qua `/twin?sequence_id=<baseline.sequence_id>` |
| POST | `/plans/{id}/replan` | `{as_of, completed:[{crop, sow, harvest, note?}]}` → decision mới cho các vụ còn lại | `history`, `changed_since_parent` |
| GET | `/plans/{id}/status` | `{status:"OK"|"REPLAN_REQUIRED", fired:[…]}` so trigger với quan trắc mới | |
| GET | `/plans/{id}/twin?sequence_id=&scenario_id=&member=` | quỹ đạo tuần của 1 phương án | `member` mặc định = năm trung vị |
| GET | `/plans/{id}/twin-compare?sequence_id=&scenario_id=&member=` | `{baseline, option}` **cùng năm thời tiết** | dùng cho Twin so sánh |
| GET | `/plans/{id}/export` | trang HTML 1 trang để in/chia sẻ | mở tab mới |

Lỗi: `{"detail": {"code": "...", "message": "..."}}` — 404 `FIELD_NOT_FOUND`/`DECISION_NOT_FOUND`/`TRAJECTORY_NOT_FOUND`, 422 `PLAN_INPUT_INVALID`/`NOTHING_TO_REPLAN`/validation, 503 `NASA_POWER_UNAVAILABLE` (mất mạng + không có cache gần).

## 3. Request chính

```jsonc
// POST /v1/plans
{
  "field_id": "fld_cantho",
  "as_of": "2026-11-14",            // optional, mặc định hôm nay
  "horizon_seasons": 3,             // 1–3
  "baseline": null,                 // optional, mặc định profile.baseline ["rice","rice","rice"]
  "priorities": ["save_water", "avoid_crop_failure", "soil_health"], // + "supplemental_income" | "minimal_change"
  "constraints": { "no_new_machinery": true, "max_changed_seasons": 1, "max_fallow_seasons": 1,
                   "irrigation": null, "irrigation_cap_mm": null, "budget_level": null }
}
// POST /v1/plans/{id}/what-if
{ "priorities": ["soil_health"],     // chỉ priorities -> xếp lại, không mô phỏng lại
  "override": { "rain_delta_pct": -30, "temp_delta_c": 1.5, "salinity_onset_shift_weeks": -4, "sow_shift_days": { "1": 7 }, "irrigation_cap_mm": 300 } }
```
`geometry` (FE `frontend/`): GeoJSON **Feature** — `geometry` là `Polygon` (ranh giới đã khoanh) hoặc `Point` (chỉ ghim), `properties: {place_name, area_source: "drawn"|"reported"}`. Backend lưu nguyên, không đọc. `null` = ruộng mẫu/chưa có hình.
`profile`: `{baseline: CropId[], irrigation: "full"|"canal_limited"|"rainfed", drainage: "good"|"poor"|"unknown", coastal_salinity_risk: bool, equipment: string[], history: []}`.
`CropId`: `rice | maize | soybean | mungbean | sesame | peanut | watermelon | fallow_cover`.

## 4. DecisionPackage (POST/GET /plans)

```text
decision_id, parent_id, kind (PLAN|WHAT_IF|REPLAN), field_id, as_of, generated_at, versions{…}
field_state            trạng thái ruộng: Measure cho canal_ecw, root_zone_wetness, upstream_discharge (context_only), elevation_m…; drainage/irrigation
gates[]                {gate G1..G8, passed, message}  -> passed=false hiển thị trong "Giới hạn"
windows[]              cửa sổ vụ {id, name_vi, sow_from, sow_to}
scenarios[]            {scenario_id, kind, name, probability: null, probability_semantics, assumptions[], quality_flags?, issue_time? (FORECAST)}
baseline               Option (is_baseline=true) — luôn có
options[]              2–4 Option (hoặc ít hơn + notes giải thích)
excluded[]             chuỗi bị loại {crops, rule_id, severity HARD, reason}
stats                  {generated, calendar_feasible, pareto_front, timings_ms…}
evidence{}             ev_* -> {kind, source, spatial_scale, resolution?, time_scope?, limitations[]}
notes[], disclaimer, history[]
```

**Option**
```text
sequence_id, is_baseline, strategy_tag (save_water|low_risk|soil_support|balanced), strategy_name_vi, summary_vi
decision_status        RECOMMEND_FOR_CONSIDERATION | CONDITIONAL_PENDING_CHECK | NOT_FEASIBLE | INSUFFICIENT_EVIDENCE
seasons[]              {index, window, window_name_vi, crop, crop_name_vi, sow_timing, sow, harvest}
metrics[scenario_id]   {irrigation_need, irrigation_need_bad_year, water_stress_days, heat_stress_days_sensitive_stage, yield(null), profit(null)}  (Measure)
delta_vs_baseline[scenario_id]  {irrigation_need:{value,unit}, water_stress_days, heat_stress_days_sensitive_stage}   (baseline: {})
distribution[scenario_id][]     {member, year|null, member_label?, irrigation_mm, water_stress_days, heat_stress_days}  -> dotplot "mỗi chấm = 1 năm"
soil_benefit           {claim_type:"POTENTIAL_QUALITATIVE", value:null, indicators[]}
rules[]                {rule_id, severity HARD|SOFT|UNKNOWN_REQUIRES_CHECK, season_index, reason, how_to_resolve, inputs_used[], evidence[]}
reasons[]              {text, evidence_ids[]}         risks[] {code, severity, season_index, text}
triggers[]             {condition, variable, op, threshold, unit, season_index, measure, action}   (text có cả dS/m và ‰)
checklist[]            string
```

Scenario kinds → nhãn UI: `CLIMATOLOGY` "Lịch sử", `STRESS_TEST` "Thử thách", `FORECAST` "Dự báo (chưa kiểm định)", `CLIMATE_PROJECTION` "Kịch bản khí hậu". Scenario ids hiện có: `sc_clim`, `sc_dry`, `sc_hot`, `sc_rain_minus30`, `sc_salt_early`, `sc_wet_ref`, `sc_forecast`, `sc_proj_<model>_<ssp>` (chỉ Cần Thơ), `sc_whatif` (trong what-if).

## 5. Digital Twin

`GET /plans/{id}/twin-compare?sequence_id=<option.sequence_id>&scenario_id=sc_clim[&member=N]`

```text
{ baseline: Twin, option: Twin }      // cùng member/năm, cùng trục ngày
Twin = {
  decision_id, sequence_id, scenario_id, member, analog_year, step: "week",
  members[]  {member, year, irrigation_mm, label_vi}   // label_vi: "Năm bình thường" | "Năm hạn như 2004–2005" | "Năm ướt như 2021–2022" | "Năm tham chiếu"
  events[]   {date, type: sow|harvest|salinity_season_start|salinity_season_end, season_index, crop}
  series[]   theo tuần: {date, season_index, crop, stage,
               root_depth_m, root_zone_water (0–1), ponding_mm (lúa; null với cây cạn),
               rain_week, irrigation_week, irrigation_cum,   // Measure, mm
               stress_risk?, salinity: Measure + in_salinity_season (bool)}
}
```
Gợi ý vẽ: mặt cắt ruộng SVG — `ponding_mm` = nước mặt ruộng lúa; `root_zone_water` = ẩm vùng rễ (cây cạn); `root_depth_m` = độ sâu rễ; `salinity.value=null` → "?"/"Chưa đo", `in_salinity_season` → nền gạch chéo; 2 đường `irrigation_cum` (hiện tại vs phương án) = nước tiết kiệm. Đổi năm: chọn trong `members` (ưu tiên những `label_vi` khác "Năm tham chiếu").

## 6. Luồng màn hình gợi ý

1. `GET /fields` → chọn ruộng → (`PATCH /fields/{id}`, `POST …/observations`) → `GET …/context`
2. `POST /plans` → màn **Quyết định** (baseline + options, chọn scenario)
3. Chọn phương án → `GET /plans/{id}/twin-compare` → **Mô phỏng**
4. `POST /plans/{id}/what-if` → decision mới (giữ bản gốc để so)
5. Checklist/triggers/evidence → `GET /plans/{id}/export` (chia sẻ Zalo/in)
6. Sau vụ: `POST /plans/{id}/replan`; định kỳ `GET /plans/{id}/status`
