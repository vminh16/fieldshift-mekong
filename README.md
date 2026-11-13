# FieldShift-Mekong

**Climate-Adaptive Crop Rotation Decision Support System**  
NASA Space Apps Challenge 2026 · Field Shift: Adapting Farms with NASA Data

> **Trạng thái:** Repository scaffold (bộ khung kỹ thuật), **chưa phải sản phẩm dự báo hay khuyến nghị nông học đã hoạt động**. HTTP health check và giao diện khởi động có thể chạy; các module lập kế hoạch, NASA adapters, mô hình cây trồng và Digital Twin hiện chưa được triển khai. Không sử dụng dữ liệu demo để ra quyết định canh tác thật.

## 1. Vấn đề và đầu ra sản phẩm

FieldShift hỗ trợ nông dân/cán bộ khuyến nông tại ĐBSCL **tạo, so sánh và hiểu các chiến lược luân canh cho nhiều vụ sắp tới**, trên cơ sở dữ liệu NASA, đặc tính đất/cây, nguồn nước, nguồn lực và ưu tiên của nông hộ. Ứng dụng cần đánh giá các điều kiện khí hậu/nước có thể xảy ra, nêu rõ rủi ro, đánh đổi và thông tin phải xác minh trước khi áp dụng.

**Kết quả sản phẩm kỳ vọng:** `DecisionPackage` gồm (1) chuỗi hiện tại để đối chứng, (2) 2–4 chiến lược thay thế **có điều kiện**, (3) lịch vụ và tính khả thi, (4) kết quả so sánh cùng kịch bản, (5) bằng chứng và mức bất định, (6) việc cần kiểm tra tại ruộng và (7) dữ liệu trạng thái/trajectory cho Digital Twin. Đây là **đích kiến trúc**, không phải kết quả do scaffold hiện tại trả về.

Nguyên tắc bất biến:

- **Rotation Planning Engine** chịu trách nhiệm lựa chọn phương án; **Digital Twin chỉ xem và tương tác với kết quả từ engine**.
- `FORECAST` (dự báo), `CLIMATE_PROJECTION` (kịch bản khí hậu), `CLIMATOLOGY` (thống kê nền) và `STRESS_TEST` (giả định thử nghiệm) **không được đánh đồng**.
- Không coi dữ liệu vệ tinh theo ô lưới là phép đo trực tiếp tại thửa; giữ nguyên nguồn, độ phân giải, thời điểm và độ tin cậy.
- Dữ liệu thiếu (ví dụ EC nước kênh) phải được biểu diễn là **chưa biết** và nêu điều kiện kiểm chứng; không tự sinh số đo.
- Sức khỏe đất, năng suất/lợi nhuận chưa có mô hình được xác thực chỉ được nêu là **đánh giá tiềm năng có điều kiện**.
- Không xây chatbot, bản đồ khí hậu hoặc hoạt cảnh 3D thành lõi thay cho bài toán đề xuất **chuỗi** cây trồng.

**Tài liệu nguồn sự thật:**

- [Problem Statement](docs/product/PROBLEM_STATEMENT.md) — đề bài, phạm vi, pain points.
- [Solution Design v2](docs/architecture/SOLUTION_DESIGN.md) — nghiệp vụ, kiến trúc, contracts, use cases và quality gates.
- [Repository Blueprint](docs/architecture/REPOSITORY_BLUEPRINT.md) — cây thư mục và dependency rules.
- [CARP Research](docs/research/CARP_RESEARCH_2026.md) — bối cảnh nghiên cứu, giải pháp đối chiếu, giới hạn khoa học.
- [Product Scope](docs/product/PRODUCT_SCOPE.md) · [Acceptance Criteria](docs/product/ACCEPTANCE_CRITERIA.md).

## 2. Kiến trúc ở mức hệ thống

```text
Nông hộ / cán bộ khuyến nông
          │
          ▼
     Web application (React) ── HTTP/OpenAPI ──► API (FastAPI)
                                                       │
                                        Application use cases
                                                       │
                         ┌─────────────────────────────┴─────────────────────┐
                         ▼                                                   ▼
               Rotation Planning Domain                            Domain ports (interfaces)
              - Field State Estimator                                         ▲
              - Future Outlook Engine                                        │
              - Feasibility / Candidate Generator                            │
              - Crop–Soil Response / Risk-aware Planner     Infrastructure adapters
              - Evidence / Explanation                     NASA · local · models · storage
                         │
                         ▼
                 DecisionPackage + trajectories
                         │
                         └────────► Web: comparison / what-if / Digital Twin viewer
```

Backend = **modular monolith** theo `API → Application → Domain ← Infrastructure`, frontend theo features. Không bắt buộc microservices, message broker hay cloud cụ thể ở giai đoạn đầu. Interface (port) cho phép thay mô hình dự báo/cây trồng mà không viết lại planner.

### Cây thư mục rút gọn

```text
apps/api/                FastAPI, use cases, domain engines, infrastructure adapters
apps/web/                React + Vite, UI theo feature, Digital Twin viewer
configs/                 Regions, crop catalog, rules, scenario defaults (có version)
contracts/               OpenAPI sinh tự động từ API, không sửa tay
data/catalog/            Danh mục nguồn, provenance và phạm vi dữ liệu
data/samples/            Fixtures minh họa, KHÔNG phải dữ liệu ruộng thực
 docs/product/           Problem Statement, scope, acceptance criteria
 docs/architecture/      Solution Design, ADR, luồng dữ liệu, blueprint
 docs/data/              Data sources, provenance & quality
 docs/operations/        Runbook & deployment guidance
infra/                   Docker Compose / topology
scripts/                 Config checks, OpenAPI generation, smoke tests
tests/e2e/               Test hành trình người dùng (sẽ bổ sung)
.github/workflows/       CI và workflow build kiểm tra thủ công
```

## 3. Chạy thử scaffold

Yêu cầu: **Python 3.11+**, **Node.js 22+**, npm; Docker Compose là tùy chọn. Cần Internet để cài dependencies lần đầu; **không cần NASA credentials để chạy trang và health endpoint**.

### Cách A — Local, không Docker

Ở thư mục gốc repo:

```bash
# Backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e './apps/api[dev]'
cp .env.example .env
make api-dev
```

Mở terminal thứ hai:

```bash
cd apps/web
npm install
npm run dev
```

- Web: http://localhost:5173
- API health: http://localhost:8000/v1/health
- API docs: http://localhost:8000/docs

Frontend chỉ hiển thị tình trạng scaffold/API; **chưa có API trả khuyến nghị luân canh**. Endpoint tương lai trả `501 Not Implemented` để tránh nhầm lẫn với kết quả thật.

### Cách B — Docker Compose

```bash
cp .env.example .env
docker compose -f infra/compose.yaml up --build
```

Mở web ở http://localhost:5173 và API health ở http://localhost:8000/v1/health. Đây là cấu hình **phát triển cục bộ**, không phải cấu hình triển khai public production. Docker/Compose không được yêu cầu cho test unit.

### Lệnh phát triển

```bash
make test            # Backend unit + HTTP smoke tests, không dùng API NASA
make lint            # Python Ruff + frontend TypeScript check
make config-check    # Kiểm tra cấu trúc YAML/JSON cấu hình và catalog
make contracts       # Sinh contracts/openapi.json từ FastAPI
make check           # test + lint + config-check
```

`make lint` cần cài Node dependencies bằng `cd apps/web && npm install`. `make contracts` yêu cầu backend dependencies đã cài. Vì môi trường đóng gói không truy cập được npm registry, bản ZIP chưa chứa `package-lock.json`. Lần đầu trên máy có mạng, `npm install` sẽ sinh lockfile; **commit lockfile**, sau đó chuyển CI/Docker/bootstrap sang `npm ci` để đảm bảo cài đặt tái lập.

## 4. Luồng sản phẩm cần hoàn thiện (KHÔNG phải chức năng đã có)

1. **Field profile:** chọn thửa, nhập chuỗi hiện tại, nguồn nước, đất/địa hình, lao động, ngân sách và mức rủi ro chấp nhận.
2. **Data context:** nạp NASA POWER, GPM, SMAP/HLS/NASADEM cùng dữ liệu đất, cây và nước địa phương; phân biệt thông tin vùng với thửa.
3. **Future outlook:** forecast khi có và đủ tin cậy; nếu không, trả về climatology / stress test; climate projection dùng cho kiểm tra chiến lược dài hạn, không giả là dự báo ngày cụ thể.
4. **Candidate generator:** tạo chuỗi nhiều mùa (gồm giữ nguyên và có thể nghỉ đất), áp dụng luật thời vụ và ràng buộc; `UNKNOWN_REQUIRES_CHECK` không bị coi là khả thi chắc chắn.
5. **Crop–soil response:** đánh giá từng chuỗi dưới cùng tập kịch bản, mang trạng thái liên vụ khi mô hình hỗ trợ; tách chỉ báo đất chưa được kiểm chứng khỏi dự báo định lượng.
6. **Planner:** loại những lựa chọn không khả thi, phân tích đánh đổi, rủi ro và ưu tiên nông hộ; xuất shortlist và checklist.
7. **Twin & what-if:** chỉ đọc trạng thái/trajectory từ backend; thay đổi điều kiện tạo một phiên đánh giá mới, không ghi đè snapshot cũ.
8. **Replan:** sau vụ, cập nhật quan trắc rồi lập kế hoạch cho phần chân trời còn lại.

Mỗi bước có ownership và giao diện chi tiết tại [Solution Design v2](docs/architecture/SOLUTION_DESIGN.md).

## 5. Quy tắc module / dependency

- `domain/`: Python thuần, không import FastAPI, SDK NASA, database, frontend; business rules và port interfaces nằm ở đây.
- `application/`: orchestration; không viết trực tiếp phương trình cây trồng trong controller/use-case.
- `infrastructure/`: hiện thực ports (NASA adapters, forecast adapters, crop models, persistence); **không tự chọn chuỗi**.
- `api/`: input/output validation, auth, error mapping; không có logic đề xuất.
- `web/features/digital-twin/`: viewer; không có mô hình tính năng suất, stress hay khuyến nghị độc lập.
- `contracts/openapi.json`: chỉ sinh từ API (`make contracts`), frontend không tự tạo schemas trùng lặp.

## 6. Hợp đồng dữ liệu và mức độ bằng chứng

Một `DecisionPackage` **khi engine triển khai** tối thiểu phải chứa `plan_id`, `field_snapshot`, `as_of`, `baseline`, `candidates`, `scenarios`, `outcomes`, `evidence`, `uncertainty`, `warnings`, `checks_required`, `model_versions` và tham chiếu trajectories. Mỗi giá trị đầu vào quan trọng phải mang thông tin nguồn/timestamp/độ phân giải và trạng thái `OBSERVED`, `ESTIMATED`, `ASSUMED` hoặc `UNKNOWN`.

Không đưa giá trị giả vào dữ liệu thật. `data/samples/sample_field.json` là tình huống **synthetic demo**. Dữ liệu lớn, ảnh vệ tinh, khoá API và thông tin định danh nông hộ không được commit vào Git.

## 7. Kiểm thử và tiêu chí hoàn thành

**Scaffold hiện có:** API health, frontend shell, config validation, HTTP test, domain contract tests, CI mẫu, Dockerfiles và Compose dev. Không có mô hình nông học đã kiểm định hoặc data adapters live.

**Mốc nghiệm thu sản phẩm:**

- Có thể tạo ít nhất 3 phương án **chuỗi** cho thửa mẫu, bao gồm baseline, và giải thích vì sao khả thi / cần kiểm tra / không khả thi.
- Hai thửa khác điều kiện nước/đất/nguồn lực có thể cho đánh giá và shortlist khác nhau theo **nguyên nhân có thể truy vết**, không hard-code theo ví dụ demo.
- Dữ liệu tương lai đúng nhãn; kết quả thiếu EC không chứa giá trị mặn bịa đặt.
- Cùng mô hình + nguồn + inputs + scenario ID tạo output lặp lại được; what-if tạo snapshot mới.
- Frontend và Twin nhận **cùng một nguồn kết quả**, không tự tạo thuật toán thay thế.
- Backend unit, integration, contract và frontend E2E tests; đánh giá chuyên gia nông học đối với những quy tắc làm thay đổi khuyến nghị.

Xem [Acceptance Criteria](docs/product/ACCEPTANCE_CRITERIA.md) và [Contributing](CONTRIBUTING.md).

## 8. Bảo mật và production readiness

Tài liệu này là **starter template**; để đưa vào production cần thêm: authentication/authorization và phân quyền dữ liệu thửa, database + migrations thật, secret manager, caching và retry có giới hạn, observability, backup, retention policy, kiểm định mô hình, deploy pipeline có kiểm soát, error budget và quy trình ứng phó sự cố. Không triển khai app scaffold hiện tại công khai như một công cụ tư vấn nông nghiệp.

**Tài liệu vận hành:** [Runbook](docs/operations/RUNBOOK.md) · [Deployment](docs/operations/DEPLOYMENT.md) · [Data Quality](docs/data/PROVENANCE_AND_QUALITY.md).

## 9. Thứ tự triển khai khuyến nghị

1. **Foundation:** chạy API/Web, chốt `PlanRequest`/`DecisionPackage`, fixtures, CI, API contracts.
2. **Planning core:** field state + feasibility + candidate generator + decision engine + explanation.
3. **Data and response:** NASA + local adapters, model cây/nước đã được kiểm thử, forecast/scenario phân biệt đúng.
4. **Experience:** comparison, Digital Twin viewer, what-if, replan, evidence cards.
5. **Hardening:** auth, persistence, tracing, deploy, backup, field validation.

Không phát triển 3D/ML lớn trước khi có đường đi **Data → Candidate → Evaluation → Recommendation → Explanation** chạy thực sự và được kiểm thử.

---

Nguồn: [NASA Space Apps 2026 — Field Shift](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/). Các đề xuất kỹ thuật và thuật toán trong repo thuộc thiết kế FieldShift, không phải yêu cầu bắt buộc do NASA áp đặt.
