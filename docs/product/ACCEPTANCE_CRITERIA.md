# Acceptance criteria — Product, not just demo UI

These are **future acceptance gates**, not claims about current scaffold readiness.

1. Field A vs Field B khác dữ liệu nước/đất/nguồn lực => engine có thể tạo kết quả khác **có lý do và evidence**.
2. Baseline (đang canh tác) luôn được trả và so sánh dưới cùng tập kịch bản với phương án thay thế.
3. `UNKNOWN` không thành zero/default value hoặc giới hạn loại cây hard-coded khi thiếu chứng cứ.
4. Có kế hoạch nhiều vụ/chuỗi, có đánh giá ảnh hưởng theo trạng thái giữa các vụ khi được mô hình hỗ trợ.
5. `FORECAST`, `CLIMATE_PROJECTION`, `CLIMATOLOGY`, `STRESS_TEST` tách đúng; chỉ gán xác suất khi có cơ sở.
6. Chỉ ra lợi ích tiềm năng sức khỏe đất và giới hạn, không hứa SOC/NPK/năng suất định lượng chưa hiệu chỉnh.
7. Outcome có nguồn và phiến bản mô hình; what-if tạo snapshot mới; twin dùng đúng output backend.
8. Các rule/nông học được đánh giá bởi chuyên gia và có unit/golden tests.
9. Có kiểm thử trên dữ liệu hồi cứu với `as_of` để tránh data leakage; đánh giá mô hình độc lập với điểm do chính mô hình sinh.
10. Cán bộ khuyến nông hiểu thời vụ, rủi ro, điều kiện thực hiện và việc cần đo trước khi xuống giống.

**Scaffold-specific:** API `GET /v1/health` trả status `ok`, `POST /v1/plans` trả 501 rõ ràng; frontend chạy được, không hiển thị recommendation bịa đặt.
