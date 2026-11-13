# Contributing

## Pull request workflow

1. Tạo nhánh `feat/*`, `fix/*`, `docs/*` hoặc `infra/*` từ `main`.
2. Mô tả use case và yêu cầu trong [Problem Statement](docs/product/PROBLEM_STATEMENT.md) hoặc [Solution Design](docs/architecture/SOLUTION_DESIGN.md).
3. Viết test cho thay đổi domain, adapter và transport contract; không sử dụng NASA live cho unit test.
4. Chạy `make check`, kiểm tra thay đổi schemas / configs / contract versions.
5. Mở PR, cần ít nhất một reviewer; thay đổi ngưỡng nông học hoặc khoa học cần người có chuyên môn duyệt.

## Review gates

- Không thêm hai engine cùng tính recommendation hoặc ước lượng crop outcome riêng biệt ở client.
- Không dùng tên `forecast` cho kịch bản SSP, stress test hoặc historical replay.
- Không tự điền giá trị `UNKNOWN` hoặc biến chỉ số đất định tính thành lời hứa năng suất.
- Không đưa file `.env`, dữ liệu hộ trồng hoặc raster lớn vào Git.
- Thay đổi source/license, nhãn nguồn và độ phân giải phải cập nhật data catalog.
- Thay đổi outcome phải có evidence và test đối chứng baseline.

## Code conventions

Backend Python 3.11+, type hints, Ruff, pytest. Frontend React/TypeScript, feature-first, không business logic trong UI. Domain không import infrastructure/API. Khi bổ sung port, có ít nhất một fake adapter cho unit tests và một integration test cho adapter thực.

CI hiện là ví dụ chạy test/build, chưa thiết lập branch protection tự động: quản trị repo cần bật required checks/approval trong GitHub Settings.
