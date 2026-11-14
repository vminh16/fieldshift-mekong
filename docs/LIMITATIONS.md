# Giới hạn đã biết của FieldShift-Mekong (MVP)

Trang này liệt kê những gì hệ thống **chưa làm được hoặc chưa kiểm chứng**, để người dùng và giám khảo không đọc kết quả mạnh hơn bằng chứng. Mỗi mục ghi rõ ảnh hưởng và hướng xử lý. Bảng luật đầy đủ: [RULES.md](RULES.md).

## Luật và tham số

| Giới hạn | Ảnh hưởng | Hướng xử lý |
|---|---|---|
| **`R_MACHINERY` không hoạt động.** `machinery_required` đang rỗng ở cả 8 cây trong `resources/crops.json`, vì nhóm chưa có nguồn khuyến nông cụ thể về yêu cầu cơ giới cho từng cây ở ĐBSCL. Nhóm chủ động giữ trống, không tự gán | Ràng buộc "không đầu tư máy mới" (`no_new_machinery`) hiện **không loại** chuỗi nào. AC-07 chỉ được kiểm chứng trên danh mục cây giả lập (`tests/integration/test_data_integrity.py`), chưa đúng với danh mục thật | Điền `machinery_required` khi có tài liệu khuyến nông hoặc MARD trích dẫn được, rồi sinh lại fixture |
| Một số ngưỡng là **heuristic do nhóm đặt** (số ngày stress nhiệt/nước, mưa gây úng, số ngày trùng mùa mặn, lịch khung vụ) | Có thể đổi trạng thái của phương án | Xem nhãn `[B]` trong RULES.md và kết quả quét trong [SENSITIVITY_REPORT.md](SENSITIVITY_REPORT.md) |
| TAW đất và hệ số Kc lấy theo giá trị chuẩn vùng hoặc FAO-56, chưa hiệu chỉnh tại thực địa | Shortlist đổi ở 25% trường hợp khi thay TAW 120/200 hoặc Kc ±10% (phương án đứng đầu không đổi) | Hiệu chỉnh theo số đo đất và ET thực tế (MODIS ET, ECOSTRESS) |
| Độ thấm ruộng lúa cố định 2 mm/ngày (thực tế 1–5) | Nhu cầu tưới tuyệt đối của baseline dao động từ −13% đến +46%. **Không trích con số mm tưới như thể đó là số đo** | Chỉ dùng để so sánh tương đối giữa các phương án |

## Dữ liệu

| Giới hạn | Ảnh hưởng |
|---|---|
| **Không có số đo mặn.** Khung mùa mặn (15/01–15/06) lấy từ báo cáo lịch sử, áp chung cho vùng ven biển | Phương án nhạy mặn luôn ở trạng thái `CONDITIONAL_PENDING_CHECK` cho tới khi người dùng nhập ECw |
| SoilGrids trả `null` ở cả 4 điểm demo | Đất chỉ được hiển thị là "chưa biết", không tham gia tính toán |
| Lưới NASA POWER khoảng 50 km, SRTM chỉ dùng làm bối cảnh vùng | Kết quả là bối cảnh vùng, không phải giá trị đo tại thửa |
| Dự báo mùa ECMWF SEAS5 chưa được đánh giá độ chính xác cho ĐBSCL | Chỉ dùng làm một kịch bản, không gán xác suất |
| Thửa không khai hồ sơ được tính với giả định tưới đủ và baseline lúa liên tục | Được gắn nhãn `assumed_default` và làm gate G2 trượt, không ghi là "nông dân khai" |

## Đánh giá quá khứ

Kết quả chi tiết nằm trong [BACKTEST_REPORT.md](BACKTEST_REPORT.md). Khi chạy ngược tại 15/11/2015, trước mùa khô kỷ lục 2015–16, engine đưa ra **cùng các cảnh báo** như khi chạy tại 15/11/2019. Lý do là khi chạy ngược quá khứ không có dự báo mùa, và các kịch bản chỉ dựa trên phân bố lịch sử, nên engine **không phân biệt được trước** một năm hạn bất thường. Tỷ lệ phương án dùng ít nước hơn baseline trong thời tiết thật cao, nhưng phần lớn là do cây cạn vốn dùng ít nước hơn lúa trong cùng mô hình.

## Mô hình

- **Không có mô hình năng suất hay lợi nhuận đã hiệu chỉnh** (gate G7 luôn trượt). Hệ thống chỉ so sánh nước, stress, lịch vụ và lợi ích đất tiềm năng (định tính).
- Không có mô hình sâu bệnh theo thời tiết. `R_PEST_CYCLE` chỉ là luật định tính cho trường hợp lúa liên tục.
- Kết quả là **gợi ý để cân nhắc cùng cán bộ khuyến nông**, không thay thế khuyến cáo chuyên môn.
