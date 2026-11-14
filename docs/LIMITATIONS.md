# Giới hạn đã biết của FieldShift-Mekong (MVP)

Trang này liệt kê những gì hệ thống **chưa làm được hoặc chưa kiểm chứng**, để người dùng và giám khảo không đọc kết quả mạnh hơn bằng chứng. Mỗi mục ghi rõ ảnh hưởng và hướng xử lý. Bảng luật đầy đủ: [RULES.md](RULES.md).

## Luật và tham số

| Giới hạn | Ảnh hưởng | Hướng xử lý |
|---|---|---|
| **`R_MACHINERY` không hoạt động.** `machinery_required` đang rỗng ở cả 8 cây trong `resources/crops.json`, vì nhóm chưa có nguồn khuyến nông cụ thể về yêu cầu cơ giới cho từng cây ở ĐBSCL. Nhóm chủ động giữ trống, không tự gán | Ràng buộc "không đầu tư máy mới" (`no_new_machinery`) hiện **không loại** chuỗi nào. AC-07 chỉ được kiểm chứng trên danh mục cây giả lập (`tests/integration/test_data_integrity.py`), chưa đúng với danh mục thật | Điền `machinery_required` khi có tài liệu khuyến nông hoặc MARD trích dẫn được, rồi sinh lại fixture |
| Một số ngưỡng là **heuristic do nhóm đặt** (số ngày stress nhiệt/nước, mưa gây úng, số ngày trùng mùa mặn, lịch khung vụ) | Trên 4 điểm demo, quét ngưỡng ngày nóng 3/5/10, ngày thiếu nước 5/7/14 và mưa úng 400/600/800 mm **không làm đổi** shortlist hay trạng thái. Lịch khung vụ và khung mùa mặn chưa được quét | Xem nhãn `[B]` trong RULES.md và [SENSITIVITY_REPORT.md](SENSITIVITY_REPORT.md) |
| TAW đất và hệ số Kc lấy theo giá trị chuẩn vùng hoặc FAO-56, chưa hiệu chỉnh tại thực địa | Ở mọi lần quét, phương án đứng đầu **vẫn giữ lúa Đông Xuân và chỉ đổi vụ Xuân Hè**, nhưng cây màu cụ thể của vụ Xuân Hè đổi qua lại (ngô ↔ đậu phộng): các cây màu có cùng `value_index` nên chỉ được tách bằng chênh lệch ~1 ngày stress p90. Top-1 đổi ở 2/12 ca (TAW 120/200) và 6/12 ca (Kc ±10%); shortlist đổi ở 6/12 và 5/12 ca (Jaccard thấp nhất 0,43). Kc ±10% làm nhu cầu tưới dao động khoảng ±8% | Hiệu chỉnh theo số đo đất và ET thực tế (MODIS ET, ECOSTRESS); coi các cây màu Xuân Hè trong shortlist là gần tương đương |
| Độ thấm ruộng lúa cố định 2 mm/ngày (thực tế 1–5) | Nhu cầu tưới tuyệt đối của baseline dao động từ −13% đến +46%. Ở 1 mm/ngày, top-1 đổi cây màu Xuân Hè ở 2/12 ca. **Không trích con số mm tưới như thể đó là số đo** | Chỉ dùng để so sánh tương đối giữa các phương án |
| **Trọng số giá trị vụ và giá trị cây là heuristic nhóm `[B]`, không có trích dẫn.** `production_value_index` = Σ theo vụ (trọng số vụ × `value_index` của cây). Trọng số vụ: Đông Xuân 1,3; Xuân Hè 1,0; Thu Đông 0,85 (`regions.json`). Giá trị cây: lúa 1,0; ngô/đậu xanh/mè/đậu phộng/dưa hấu 0,8; đậu nành 0,6 (cạnh tranh nhập khẩu); bỏ hóa 0 (`crops.json`). Nhóm không trích được bảng niên giám thống kê hay công bố của viện nào cho đúng các con số này | Chỉ số này là một tiêu chí Pareto và là khóa xếp hạng của "Giảm rủi ro", "Hỗ trợ đất" và "Thay đổi ít". Nó làm engine không còn bỏ vụ Đông Xuân để tiết kiệm nước. Đây **không** phải năng suất, giá hay lợi nhuận (G7 vẫn trượt). "Tiết kiệm nước" vẫn hiện phương án cực trị về nước (đổi vụ Đông Xuân) kèm chỉ số giá trị thấp hơn | Thay bằng năng suất theo vụ × giá (Tổng cục Thống kê hoặc sở NN tỉnh) khi có nguồn trích dẫn được |

## Dữ liệu

| Giới hạn | Ảnh hưởng |
|---|---|
| **Không có số đo mặn.** Khung mùa mặn (15/01–15/06) lấy từ báo cáo lịch sử, áp chung cho vùng ven biển | Phương án nhạy mặn luôn ở trạng thái `CONDITIONAL_PENDING_CHECK` cho tới khi người dùng nhập ECw |
| SoilGrids trả `null` ở cả 4 điểm demo | Đất chỉ được hiển thị là "chưa biết", không tham gia tính toán |
| Lưới NASA POWER khoảng 50 km, SRTM chỉ dùng làm bối cảnh vùng | Kết quả là bối cảnh vùng, không phải giá trị đo tại thửa |
| Dự báo mùa ECMWF SEAS5 chưa được đánh giá độ chính xác cho ĐBSCL | Chỉ dùng làm một kịch bản, không gán xác suất |
| Thửa không khai hồ sơ được tính với giả định tưới đủ và baseline lúa liên tục | Được gắn nhãn `assumed_default` và làm gate G2 trượt, không ghi là "nông dân khai" |

## Đánh giá quá khứ

Kết quả chi tiết nằm trong [BACKTEST_REPORT.md](BACKTEST_REPORT.md) và [YEAR_OUTLOOK_REPORT.md](YEAR_OUTLOOK_REPORT.md). Khi chạy ngược tại 15/11/2015, trước mùa khô kỷ lục 2015–16, engine vẫn đưa ra **cùng các cờ luật** như khi chạy tại 15/11/2019, vì luật dựa trên khí hậu nhiều năm và lịch mùa mặn. Tín hiệu theo năm nay đến từ ENSO (xem mục dưới): tại 15/11/2015 engine báo El Niño mạnh và mùa khô các năm tương tự chỉ ~69 % năm thường (Cần Thơ); hướng khô/ướt đúng ở 12/15 ca hindcast, trật cả 3 điểm năm 2018–19 (El Niño yếu nhưng mưa nhiều). Trong thời tiết thật, 58/60 phương án tốt hơn baseline về nước tưới mà không tăng thiếu nước. 2 phương án không tốt hơn đều ở Cần Thơ 2019 khi giới hạn nước kênh: tưới ít hơn nhưng thiếu nước thêm 1 ngày. Trước đây có 34/42; 6 phương án thua là do vụ `fallow_cover` bị cộng ngày "thiếu nước" của đất trống, lỗi này đã được sửa. Kết quả này phần lớn là do cây cạn vốn dùng ít nước hơn lúa trong cùng mô hình.

## Năm ENSO (`year_outlook`, `sc_enso_analog`)

- **Không phải dự báo.** Năm tương tự là các năm lịch sử cùng nhóm pha ENSO (ONI NOAA, không phải NASA) tại cùng tháng giữa; liên hệ với mưa tháng 12–4 chỉ ở mức r ≈ −0,4 đến −0,7 trên ~24 mùa (IMERG). Có năm El Niño vẫn mưa nhiều (2018–19).
- **Không nhìn trước:** chỉ dùng ONI có cửa sổ 3 tháng đã kết thúc trước tháng của `as_of` (15/11 → ASO). Vì vậy 2019 (ASO +0,31) được coi là trung tính dù sau đó lên El Niño yếu. NOAA hiệu chỉnh lại giá trị cũ; file bundled là bản 2026.
- "Mạnh/yếu" chỉ là nhãn; năm tương tự lấy theo nhóm pha (El Niño, trung tính, La Niña), tối đa 5 năm gần ONI hiện tại nhất. Dưới 3 năm → `UNAVAILABLE`, engine chạy y như trước (hindcast trước ~2012 thường rơi vào trường hợp này).
- Khi có, `sc_enso_analog` **thay `sc_dry` làm tiêu chí "năm khô"** khi sàng lọc. Hindcast cho thấy shortlist đổi ở 4/15 ca (chỉ Cần Thơ) và tưới thực của phương án đứng đầu không giảm (bằng 13 ca, nhiều hơn 2 ca): tín hiệu ENSO hiện giúp **cảnh báo** năm khô tốt hơn là giúp **chọn** phương án tốt hơn.
- **Thời điểm mặn không đổi theo ENSO**: kịch bản năm tương tự giữ khung mặn điển hình; engine không suy ra mặn đến sớm từ El Niño (dùng `sc_salt_early` để thử).
- Mưa mùa khô theo điểm dùng IMERG monthly (ô ~11 km) chỉ cho 4 điểm demo; thửa khác dùng NASA POWER (~50 km). Mô phỏng nước của năm tương tự vẫn chạy trên ngày POWER.

## Mô hình

- **Không có mô hình năng suất hay lợi nhuận đã hiệu chỉnh** (gate G7 luôn trượt). Hệ thống chỉ so sánh nước, stress, lịch vụ và lợi ích đất tiềm năng (định tính).
- Không có mô hình sâu bệnh theo thời tiết. `R_PEST_CYCLE` chỉ là luật định tính cho trường hợp lúa liên tục.
- **Liên vụ chỉ truyền độ ẩm đất.** Khoảng nghỉ giữa hai vụ được mô phỏng như đất trống không tưới. Muối tích tụ, tàn dư và dinh dưỡng **không** được truyền giữa các vụ, nên lợi ích đất chỉ là định tính.
- **Vụ bỏ hóa không cộng ngày stress.** Đất trống khô không phải thiệt hại cây trồng, nên vụ `water_regime == "none"` cộng 0 vào tổng ngày thiếu nước và ngày nắng nóng. Số đếm thô vẫn được giữ trong kết quả mô phỏng (`bare_soil_*`). Lợi ích của vụ nghỉ (cắt vòng đời rầy nâu, đất nghỉ) vẫn chỉ là định tính.
- **"Nghỉ vụ ba / xả lũ"** chỉ đưa ra cho ruộng không có rủi ro mặn (`coastal_salinity_risk = false`, dùng làm phép thử vùng nội đồng/đầu nguồn). Engine **không biết** ruộng có nằm trong vùng xả lũ hay không. Lợi ích nhận phù sa chỉ ghi có điều kiện và ở dạng định tính (`POTENTIAL_QUALITATIVE`). Phương án này là một tập quán canh tác được chọn theo luật, không phải điểm trên mặt Pareto.
- **"Né mặn: xuống giống sớm"** chỉ đưa ra cho ruộng ven biển. Số ngày tránh được là số ngày trùng khung mặn **điển hình** của vùng mà engine tính từ chính ngày gieo/thu hoạch, so với gieo chuẩn. Với cả hai khung (điển hình và mặn đến sớm 4 tuần), Sóc Trăng và Bến Tre đều giảm 23 ngày. Phương án này **không loại bỏ** rủi ro mặn: vụ Đông Xuân vẫn trùng khung mặn và vẫn cần đo ECw (`R_SALINITY_UNKNOWN`).
- **`confidence` của baseline** chỉ bị giới hạn bởi biến chưa biết và trạng thái (baseline không so với chính nó). Mức HIGH của baseline nghĩa là "đủ dữ liệu", không có nghĩa là "tốt nhất".
- **Beam search cho chân trời trên 3 vụ** chỉ giữ ngày gieo tốt nhất cho mỗi tiền tố chuỗi cây, nên có thể bỏ sót tổ hợp ngày gieo. Không tuyên bố tối ưu toàn cục. Chân trời 1–3 vụ vẫn vét cạn.
- Kết quả là **gợi ý để cân nhắc cùng cán bộ khuyến nông**, không thay thế khuyến cáo chuyên môn.
