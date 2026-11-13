# FieldShift-Mekong — Repository Blueprint v1.0

**Mục đích:** cấu trúc repo cho sản phẩm hỗ trợ quyết định luân canh theo `FieldShift_Mekong_Solution_Design_v2.md`. Đây là **đề xuất thiết kế repo**, không phải khẳng định đã hiện thực hóa các engine/mô hình trong cây thư mục.

**Kiến trúc được chọn:** monorepo, modular monolith, API làm trung tâm điều phối; backend theo `API → Application → Domain ← Infrastructure (adapters)`; frontend theo feature. Chỉ tách service độc lập khi có bằng chứng vận hành đòi hỏi.

**Nguyên tắc sản phẩm:** Rotation Planning Engine quyết định; Crop–Soil Response Engine ước lượng kết quả; Digital Twin chỉ trình bày/sử dụng cùng những kết quả đó. `FORECAST`, `CLIMATE_PROJECTION`, `CLIMATOLOGY`, `STRESS_TEST` phải khác biệt trong hợp đồng dữ liệu.

## 1. Cây thư mục đề xuất

```text
fieldshift-mekong/
├── README.md                         # Setup, run, demo flow, kiến trúc 1 trang
├── CONTRIBUTING.md                   # Branch, code review, tiêu chí merge
├── .env.example                      # Chỉ placeholder, không chứa secret
├── .gitignore
├── .pre-commit-config.yaml
├── Makefile                          # dev / test / lint / format / contracts
├── .github/
│   ├── CODEOWNERS
│   └── workflows/
│       ├── ci.yml                    # Lint, typing, test, contract checks
│       └── deploy.yml                # Build/deploy có kiểm soát, khi cần
│
├── apps/
│   ├── api/                          # Một backend deployable duy nhất
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   ├── migrations/               # Migration schema DB (ví dụ Alembic)
│   │   ├── src/fieldshift/
│   │   │   ├── __init__.py
│   │   │   ├── main.py               # Entry point HTTP
│   │   │   ├── settings.py           # Validate env config
│   │   │   │
│   │   │   ├── api/                  # Delivery layer: không chứa thuật toán
│   │   │   │   ├── dependencies.py
│   │   │   │   ├── schemas/          # Request/response transport schemas
│   │   │   │   └── v1/
│   │   │   │       ├── fields.py
│   │   │   │       ├── plans.py
│   │   │   │       ├── scenarios.py
│   │   │   │       └── health.py
│   │   │   │
│   │   │   ├── application/          # Orchestration + transaction boundaries
│   │   │   │   ├── use_cases/
│   │   │   │   │   ├── create_field_profile.py
│   │   │   │   │   ├── plan_rotation.py
│   │   │   │   │   ├── evaluate_what_if.py
│   │   │   │   │   ├── replan_rotation.py
│   │   │   │   │   └── get_decision_package.py
│   │   │   │   └── dto.py
│   │   │   │
│   │   │   ├── domain/               # Business rules, không import API/DB/NASA SDK
│   │   │   │   ├── models/
│   │   │   │   │   ├── field.py       # FieldProfile, FieldState
│   │   │   │   │   ├── crop.py        # Crop, SeasonWindow, RotationAction
│   │   │   │   │   ├── rotation.py    # RotationSequence, AdaptivePolicy
│   │   │   │   │   ├── scenario.py    # Scenario, ScenarioKind, ScenarioSet
│   │   │   │   │   ├── outcome.py     # Outcome, trajectory
│   │   │   │   │   └── decision.py    # DecisionPackage, Recommendation
│   │   │   │   ├── value_objects/
│   │   │   │   │   ├── evidence.py    # Provenance, quality, known/unknown
│   │   │   │   │   ├── units.py       # Units, spatial/temporal resolution
│   │   │   │   │   └── constraints.py
│   │   │   │   ├── ports/             # Protocol/ABC được domain định nghĩa
│   │   │   │   │   ├── earth_data.py
│   │   │   │   │   ├── outlook.py
│   │   │   │   │   ├── crop_response.py
│   │   │   │   │   └── repositories.py
│   │   │   │   └── engines/
│   │   │   │       ├── field_state.py
│   │   │   │       ├── future_outlook.py
│   │   │   │       ├── feasibility.py
│   │   │   │       ├── candidate_generator.py
│   │   │   │       ├── crop_soil_response.py
│   │   │   │       ├── rotation_planner.py
│   │   │   │       └── explanation.py
│   │   │   │
│   │   │   └── infrastructure/       # Implement các domain ports
│   │   │       ├── data_sources/
│   │   │       │   ├── nasa/
│   │   │       │   │   ├── power.py
│   │   │       │   │   ├── imerg.py
│   │   │       │   │   ├── smap.py
│   │   │       │   │   ├── hls.py
│   │   │       │   │   ├── nasadem.py
│   │   │       │   │   └── projection.py
│   │   │       │   ├── forecasts/    # GEOS-S2S/Copernicus khi đã kiểm tra
│   │   │       │   └── local/        # SoilGrids, nguồn mặn/thuỷ văn, FAO
│   │   │       ├── crop_models/
│   │   │       │   ├── fao56_water.py
│   │   │       │   ├── salinity_risk.py
│   │   │       │   └── soil_indicators.py
│   │   │       ├── persistence/
│   │   │       │   ├── postgres.py
│   │   │       │   └── object_store.py
│   │   │       ├── jobs/             # Cùng codebase, entrypoint job/worker
│   │   │       │   ├── ingest_observations.py
│   │   │       │   └── execute_plan.py
│   │   │       └── observability/
│   │   │           └── logging.py
│   │   └── tests/
│   │       ├── unit/                 # Domain/engines thuần, nhanh
│   │       ├── integration/          # Adapter, DB, geospatial I/O
│   │       ├── contract/             # API/port schemas, backward compat
│   │       └── fixtures/             # Small deterministic data, no live APIs
│   │
│   └── web/                          # Một frontend deployable duy nhất
│       ├── package.json
│       ├── Dockerfile
│       ├── src/
│       │   ├── app/                  # Router, providers, app shell
│       │   ├── features/
│       │   │   ├── field-profile/
│       │   │   ├── rotation-planner/
│       │   │   ├── scenario-explorer/
│       │   │   ├── decision-compare/
│       │   │   ├── digital-twin/     # Viewer/timeline, KHÔNG tính recommendation
│       │   │   └── evidence-checklist/
│       │   ├── shared/
│       │   │   ├── api/generated/    # Generated OpenAPI client, do not edit
│       │   │   ├── components/
│       │   │   └── utils/
│       │   └── main.tsx
│       └── tests/
│           └── components/
│
├── configs/                           # Phiên bản hóa, validate trong CI
│   ├── regions/mekong.yaml            # Mùa vụ, logic vùng, phạm vi áp dụng
│   ├── crops/catalog.yaml             # Chỉ cây có nguồn/phiên bản đủ tin
│   ├── rules/feasibility.yaml         # HARD/SOFT/UNKNOWN_REQUIRES_CHECK
│   └── scenarios/defaults.yaml        # Stress tests rõ là giả định
│
├── contracts/                         # Build-generated từ API schemas
│   ├── openapi.json                   # Không chỉnh thủ công
│   └── README.md                      # Cách generate và kiểm tra breaking changes
│
├── data/
│   ├── README.md                      # Lineage, nguồn, license, giới hạn, storage
│   ├── catalog/sources.yaml           # NASA/local: product/version/time/resolution
│   └── samples/                       # Bộ demo tối thiểu, công khai nguồn
│       └── sample_field.json
│   # Không commit raw rasters, credentials, data cache, PII
│
├── docs/
│   ├── product/
│   │   ├── PROBLEM_STATEMENT.md
│   │   ├── PRODUCT_SCOPE.md
│   │   └── ACCEPTANCE_CRITERIA.md
│   ├── architecture/
│   │   ├── SOLUTION_DESIGN.md         # Bản v2 làm nguồn sự thật
│   │   ├── DATA_FLOW.md
│   │   └── adr/
│   │       └── 0001-modular-monolith.md
│   ├── data/
│   │   ├── SOURCES.md
│   │   └── PROVENANCE_AND_QUALITY.md
│   └── operations/
│       ├── RUNBOOK.md
│       └── DEPLOYMENT.md
│
├── infra/
│   ├── compose.yaml                   # API + Web + DB; queue optional
│   └── README.md                      # Local/dev/prod topology, secrets
│
├── scripts/
│   ├── bootstrap.sh
│   ├── validate_configs.py
│   └── smoke_test.sh
│
└── tests/
    └── e2e/                           # User flow: field → plans → twin → what-if
```

> Các thư mục trên là **đích phát triển**. Lúc khởi tạo repo có thể chỉ tạo file/thư mục đã dùng, không cần tạo 100 file rỗng.

## 2. Dependency rules — bắt buộc

```text
Web ──HTTP──> API routes ──> Application use cases ──> Domain ports + engines
                                              ▲                  ▲
                                              └── Infrastructure adapters ┘
```

- `domain/` không import `api/`, `infrastructure/`, SDK NASA, ORM, frontend.
- `application/` điều phối theo use case; không tính toán các luật nông học trong controller.
- `infrastructure/` hiện thực các port; **không** tự quyết định chọn chuỗi cây.
- `api/` chỉ validate transport, auth, invoke use case, serialize response.
- `web/features/digital-twin/` chỉ nhận `DecisionPackage`, `Scenario`, `trajectory` từ backend; không tự áp dụng công thức crop/yield.
- `contracts/` là artefact sinh từ API schemas làm nguồn chuẩn, không tạo hai schema thủ công khác nhau.

## 3. Ownership từng engine

| Engine/module | Trách nhiệm | Không làm |
|---|---|---|
| `field_state.py` | Chuyển quan sát + profile thành state có evidence | Tự chọn cây |
| `future_outlook.py` | Tổng hợp forecast / projection / climatology / stress test, giữ semantics | Gọi stress test là dự báo |
| `feasibility.py` | Luật hard/soft/unknown theo dữ kiện và điều kiện vùng | Loại bằng ngưỡng thiếu căn cứ |
| `candidate_generator.py` | Sinh chuỗi ứng viên theo thời vụ, baseline, ràng buộc | Xếp hạng bằng số liệu giả |
| `crop_soil_response.py` | Đánh giá hậu quả của sequence × scenario qua model ports, xuất trajectory | Khẳng định độ chính xác ngoài kiểm định |
| `rotation_planner.py` | Đánh đổi, rủi ro, shortlist, trigger replan | Tính forecast hoặc trực tiếp gọi NASA API |
| `explanation.py` | Tạo lý do, source, checklist | Tự sinh evidence hoặc số liệu mới |

## 4. Data lifecycle và provenance

- **Raw external:** NASA/SoilGrids/quan trắc địa phương → object storage hoặc cache quản lý riêng (không commit Git).
- **Normalized/features:** ingestion jobs chuẩn hóa đơn vị, CRS, ngày `observed_at`, `available_at`, `issue_time`, ô lưới, `source_version`; lưu metadata trong DB.
- **Decision snapshots:** với mỗi `PlanRequest`, lưu `as_of`, profile version, crop/rule/model versions, scenario set ID, input hashes, DecisionPackage, trajectory pointer. Không sửa ngược snapshot cũ.
- **Backtest:** tính `as_of` theo ngày giả định; cấm vô tình đưa dữ liệu công bố sau ngày đó vào mô hình.
- **Unknown:** `null/UNKNOWN` phải được giữ nguyên ngữ nghĩa; mỗi scenario có `kind` và chỉ có trọng số xác suất khi hợp lệ.

## 5. API surface ở mức conceptual

| API | Use case | Outcome |
|---|---|---|
| `POST /v1/fields` | Tạo hồ sơ thửa | `field_id`, fields_missing |
| `GET /v1/fields/{id}` | Xem hồ sơ thửa | Profile + evidence |
| `POST /v1/plans` | Sinh kế hoạch (có thể trả `job_id`) | DecisionPackage hoặc job |
| `GET /v1/plans/{id}` | Lấy kết quả quyết định | Immutable DecisionPackage |
| `POST /v1/plans/{id}/what-if` | Tạo đánh giá kịch bản mới | DecisionPackage phiên bản mới |
| `POST /v1/plans/{id}/replan` | Cập nhật state, lập kế hoạch lại | Plan version mới |
| `GET /v1/plans/{id}/trajectory` | Hiển thị twin | Scenario/time-series per candidate |

**Lưu ý:** API bên trên mới là bản thiết kế; GET/POST, job mode và response schemas phải được chốt thành OpenAPI trước khi frontend/backend triển khai song song.

## 6. Production-readiness tối thiểu

1. **Local reproducibility:** `make dev`, `make test`, `make lint`, `.env.example`, compose; không hard-code khóa API.
2. **CI gates:** lint/format/type check, unit + integration + contract tests, schema/config validation, dependency/security scan; protect `main` và review PR.
3. **Deterministic product tests:** 2 field profiles khác nhau; ít nhất một thay đổi khả thi/rủi ro có nguyên nhân; baseline luôn xuất hiện; tình huống thiếu EC không sinh con số EC giả; WHAT-IF có snapshot riêng.
4. **Scientific checks:** các mô hình nước/cây có unit tests và golden tests từ ví dụ có nguồn; dữ liệu demo synthetic gắn nhãn, không sử dụng như evidence thực nghiệm.
5. **Observability:** `request_id`, `plan_id`, `scenario_id`, `model_version`, latency theo bước, cảnh báo fallback, API failures; không log PII/secret nguyên dạng.
6. **Operational resilience:** timeouts, retry có giới hạn, cache freshness, idempotency cho planning jobs, database migrations, backup, health endpoints.
7. **Security & privacy:** auth/authorization trước khi lưu thửa của nhiều nông hộ, quyền truy cập theo tài khoản/HTX, phân loại thông tin vị trí thửa, secrets từ môi trường và quản lý quyền.

## 7. Lộ trình tạo repo (không tạo mọi thứ ngay)

- **Milestone 1 — Skeleton:** README + SOLUTION_DESIGN, API/web boots, compose, CI, `PlanRequest` / `DecisionPackage`, fixtures, một E2E đi xuyên toàn app (chưa có mô hình ngoài).
- **Milestone 2 — Product core:** Crop catalog + feasibility + candidate generator + planner + explanation; baseline và shortlist có lý do; không giả vờ có forecast.
- **Milestone 3 — Data & response:** POWER/GPM + SoilGrids + field input adapters, FAO56 water, scenario generator, snapshots, model tests.
- **Milestone 4 — Experience & adaptive:** digital twin viewer, what-if, forecast adapter (khi kiểm tra availability/skill), optional salinity data, rolling replan.
- **Milestone 5 — Operational:** observability, security, CI/CD, monitoring, backups, accessibility, field validation.

## 8. Hai anti-pattern cần tránh

- **Một file `predict.py` ôm mọi việc:** tải NASA, forecast, chấm đất, sinh chuỗi, rank và vẽ UI → khó kiểm định, khó thay mô hình và dễ drift.
- **Hai engine khoa học độc lập ở backend và frontend:** UI tự tính một bộ stress/năng suất khác backend → khuyến nghị và mô phỏng mâu thuẫn. Chỉ backend xuất trajectories và outcomes; frontend là viewer.

**Kiến trúc đã chốt:** một codebase backend có các port/adapters riêng; một web frontend; không tách microservice, feature-store, MLflow, Kubernetes hay hàng chục package khi chưa có nhu cầu thật.
