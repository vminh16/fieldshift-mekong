# Giới hạn đã biết của FieldShift-Mekong (MVP)

Trang này liệt kê những gì hệ thống **chưa làm được hoặc chưa kiểm chứng**, để người dùng và giám khảo không đọc kết quả mạnh hơn bằng chứng. Mỗi mục ghi rõ ảnh hưởng và hướng xử lý. Bảng luật đầy đủ: [RULES.md](RULES.md).

## Luật và tham số

| Giới hạn | Ảnh hưởng | Hướng xử lý |
|---|---|---|
| **`R_MACHINERY` không hoạt động.** `machinery_required` đang rỗng ở cả 8 cây trong `resources/crops.json`, vì nhóm chưa có nguồn khuyến nông cụ thể về yêu cầu cơ giới cho từng cây ở ĐBSCL. Nhóm chủ động giữ trống, không tự gán | Ràng buộc "không đầu tư máy mới" (`no_new_machinery`) hiện **không loại** chuỗi nào. AC-07 chỉ được kiểm chứng trên danh mục cây giả lập (`tests/integration/test_data_integrity.py`), chưa đúng với danh mục thật | Điền `machinery_required` khi có tài liệu khuyến nông hoặc MARD trích dẫn được, rồi sinh lại fixture |
| Một số ngưỡng là **heuristic do nhóm đặt** (số ngày stress nhiệt/nước, mưa gây úng, số ngày trùng mùa mặn, lịch khung vụ) | Trên 4 điểm demo, quét ngưỡng ngày nóng 3/5/10, ngày thiếu nước 5/7/14 và mưa úng 400/600/800 mm **không làm đổi** shortlist hay trạng thái. Lịch khung vụ và khung mùa mặn chưa được quét | Xem nhãn `[B]` trong RULES.md và [SENSITIVITY_REPORT.md](SENSITIVITY_REPORT.md) |
| TAW đất và hệ số Kc lấy theo giá trị chuẩn vùng hoặc FAO-56, chưa hiệu chỉnh tại thực địa | Ở mọi lần quét, phương án đứng đầu **vẫn giữ lúa Đông Xuân và chỉ đổi vụ Xuân Hè**, nhưng cây màu cụ thể của vụ Xuân Hè đổi qua lại (ngô ↔ đậu phộng): các cây màu có cùng `value_index` nên chỉ được tách bằng chênh lệch ~1 ngày stress p90. Sau A7: top-1 đổi ở 2/12 ca (TAW 120/200) và 4/12 ca (Kc ±10%); shortlist đổi ở 4/12 ca cho cả hai nhóm. Kc ±10% làm nhu cầu tưới dao động khoảng ±8% | Hiệu chỉnh theo số đo đất và ET thực tế (MODIS ET, ECOSTRESS); coi các cây màu Xuân Hè trong shortlist là gần tương đương |
| Độ thấm ruộng lúa cố định 2 mm/ngày (thực tế 1–5) | Nhu cầu tưới tuyệt đối của baseline dao động từ −13% đến +46%. Sau A7, quét độ thấm làm top-1 đổi ở 4/12 ca. **Không trích con số mm tưới như thể đó là số đo** | Chỉ dùng để so sánh tương đối giữa các phương án |
| **Trọng số giá trị vụ và giá trị cây là heuristic nhóm `[B]`, không có trích dẫn.** `production_value_index` = Σ theo vụ (trọng số vụ × `value_index` của cây). Trọng số vụ: Đông Xuân 1,3; Xuân Hè 1,0; Thu Đông 0,85 (`regions.json`). Giá trị cây: lúa 1,0; ngô/đậu xanh/mè/đậu phộng/dưa hấu 0,8; đậu nành 0,6 (cạnh tranh nhập khẩu); bỏ hóa 0 (`crops.json`). Nhóm không trích được bảng niên giám thống kê hay công bố của viện nào cho đúng các con số này | Chỉ số này là một tiêu chí Pareto và là khóa xếp hạng của "Giảm rủi ro", "Hỗ trợ đất" và "Thay đổi ít". Nó làm engine không còn bỏ vụ Đông Xuân để tiết kiệm nước. Đây **không** phải năng suất, giá hay lợi nhuận (G7 vẫn trượt). "Tiết kiệm nước" vẫn hiện phương án cực trị về nước (đổi vụ Đông Xuân) kèm chỉ số giá trị thấp hơn | Thay bằng năng suất theo vụ × giá (Tổng cục Thống kê hoặc sở NN tỉnh) khi có nguồn trích dẫn được |

## Dữ liệu

| Giới hạn | Ảnh hưởng |
|---|---|
| **Không có số đo mặn.** Khung nhiều năm 15/01–15/06; riêng 2026–27, El Niño kèm dẫn SIWRR qua báo dùng 01/12/2026–15/06/2027 (ASSUMPTION, 45 ngày sớm hơn) | Phương án nhạy mặn luôn ở trạng thái `CONDITIONAL_PENDING_CHECK` cho tới khi người dùng nhập ECw |
| SoilGrids trả `null` ở cả 4 điểm demo | Đất chỉ được hiển thị là "chưa biết", không tham gia tính toán |
| Lưới NASA POWER khoảng 50 km; SRTM là bối cảnh và chỉ vào áp suất/bức xạ trời quang trong ET₀ | Kết quả là bối cảnh vùng, không phải giá trị đo tại thửa |
| Dự báo mùa ECMWF SEAS5 chưa được đánh giá độ chính xác cho ĐBSCL | Chỉ dùng làm một kịch bản, không gán xác suất |
| Thửa không khai hồ sơ được tính với giả định tưới đủ và baseline lúa liên tục | Được gắn nhãn `assumed_default` và làm gate G2 trượt, không ghi là "nông dân khai" |

## Đánh giá quá khứ

Kết quả chi tiết nằm trong [BACKTEST_REPORT.md](BACKTEST_REPORT.md) và [YEAR_OUTLOOK_REPORT.md](YEAR_OUTLOOK_REPORT.md), đã chạy lại sau A7. Hướng mưa đúng **12/15** ca có đủ năm tương tự; cả ba ca sai đều là 2018–19 (El Niño yếu nhưng mưa nhiều). So với engine coi mọi năm như nhau, top-1 có ENSO **không giảm tưới ở ca nào**, tăng ở 1 ca và bằng ở 14 ca. Đây là tín hiệu thống kê để thảo luận, chưa chứng minh giúp chọn phương án tốt hơn.

Trong backtest 2016/2020, **59/60** phương án dùng ít nước tưới mà không tăng thiếu nước so với baseline theo **cùng mô hình** FAO-56; một ca Cần Thơ 2019, giới hạn nước kênh, không đạt. Kết quả phần lớn do cây cạn/nghỉ vụ vốn cần ít nước hơn lúa. Đây là nhất quán nội bộ, không phải kiểm định với nước tưới, năng suất hay thiệt hại đo thực. Các ca không độc lập và chưa có số đo mặn để đánh giá an toàn mặn.

## Năm ENSO (`year_outlook`, `sc_enso_analog`)

- **Không phải dự báo.** Năm tương tự là các năm lịch sử cùng nhóm pha ENSO (ONI NOAA, không phải NASA) tại cùng tháng giữa; liên hệ với mưa tháng 12–4 chỉ ở mức r ≈ −0,4 đến −0,7 trên ~24 mùa (IMERG). Có năm El Niño vẫn mưa nhiều (2018–19).
- **Không nhìn trước:** chỉ dùng ONI có cửa sổ 3 tháng đã kết thúc trước tháng của `as_of` (15/11 → ASO). Vì vậy 2019 (ASO +0,31) được coi là trung tính dù sau đó lên El Niño yếu. NOAA hiệu chỉnh lại giá trị cũ; file bundled là bản 2026.
- "Mạnh/yếu" chỉ là nhãn; năm tương tự lấy theo nhóm pha (El Niño, trung tính, La Niña), tối đa 5 năm gần ONI hiện tại nhất. Dưới 3 năm → `UNAVAILABLE`, engine chạy y như trước (hindcast trước ~2012 thường rơi vào trường hợp này).
- Khi có, `sc_enso_analog` **thay `sc_dry` làm tiêu chí "năm khô"** khi sàng lọc. Sau A7, hindcast cho thấy shortlist đổi ở 2/15 ca (chỉ Cần Thơ) và tưới mô phỏng trên thời tiết thực của phương án đứng đầu không giảm (bằng 14 ca, nhiều hơn 1 ca): tín hiệu ENSO hiện giúp **cảnh báo** năm khô tốt hơn là giúp **chọn** phương án tốt hơn.
- **ENSO riêng lẻ không dời khung mặn.** Chỉ kế hoạch mùa 2026–27 với tín hiệu El Niño và bằng chứng SIWRR qua báo mới dùng khung sớm hơn. Ngày 01/12 là cách nhóm rời rạc hóa thông tin “từ tháng 12”, không phải dự báo ngày mặn tại ruộng. Kết thúc 15/06 vẫn lấy nền nhiều năm. `salinity_window`/Twin công khai cả ngày đang dùng và ngày nền; `sc_salt_early` thử thêm 4 tuần sớm hơn.
- Mưa mùa khô theo điểm dùng IMERG monthly (ô ~11 km) chỉ cho 4 điểm demo; thửa khác dùng NASA POWER (~50 km). Mô phỏng nước của năm tương tự vẫn chạy trên ngày POWER.

## Mô hình

- **Không có mô hình năng suất hay lợi nhuận đã hiệu chỉnh** (gate G7 luôn trượt). Hệ thống chỉ so sánh nước, stress, lịch vụ và lợi ích đất tiềm năng (định tính).
- Không có mô hình sâu bệnh theo thời tiết. `R_PEST_CYCLE` chỉ là luật định tính cho trường hợp lúa liên tục.
- **Liên vụ chỉ truyền độ ẩm đất.** Khoảng nghỉ giữa hai vụ được mô phỏng như đất trống không tưới. Muối tích tụ, tàn dư và dinh dưỡng **không** được truyền giữa các vụ, nên lợi ích đất chỉ là định tính.
- **Vụ bỏ hóa không cộng ngày stress.** Đất trống khô không phải thiệt hại cây trồng, nên vụ `water_regime == "none"` cộng 0 vào tổng ngày thiếu nước và ngày nắng nóng. Số đếm thô vẫn được giữ trong kết quả mô phỏng (`bare_soil_*`). Lợi ích của vụ nghỉ (cắt vòng đời rầy nâu, đất nghỉ) vẫn chỉ là định tính.
- **"Nghỉ vụ ba / xả lũ"** chỉ đưa ra cho ruộng không có rủi ro mặn (`coastal_salinity_risk = false`, dùng làm phép thử vùng nội đồng/đầu nguồn). Engine **không biết** ruộng có nằm trong vùng xả lũ hay không. Lợi ích nhận phù sa chỉ ghi có điều kiện và ở dạng định tính (`POTENTIAL_QUALITATIVE`). Phương án này là một tập quán canh tác được chọn theo luật, không phải điểm trên mặt Pareto.
- **“Gieo đầu khung vụ”** (`salinity_avoidance`) chỉ có cho ven biển: giữ chuỗi cây, gieo đầu khung engine. Ngày 15/11/2026 là **đợt 1**, không phải khung gieo sớm né mặn 10–30/10/2026 (đã qua). Khung mặn 2026–27 đang dùng làm số ngày tránh được của phương án này chỉ còn 7 ngày, không còn 23 ngày như khi dùng nền nhiều năm. Còn rủi ro mặn và vẫn phải đo ECw (`R_SALINITY_UNKNOWN`). Sóc Trăng/Bến Tre top-1 nghỉ vụ Xuân Hè có 84 ngày cây trùng khung mặn so với 177 ngày baseline; đó là đếm lịch, không chứng minh giảm thiệt hại mặn.
- **`confidence` của baseline** chỉ bị giới hạn bởi biến chưa biết và trạng thái (baseline không so với chính nó). Mức HIGH của baseline nghĩa là "đủ dữ liệu", không có nghĩa là "tốt nhất".
- **Beam search cho chân trời trên 3 vụ** chỉ giữ ngày gieo tốt nhất cho mỗi tiền tố chuỗi cây, nên có thể bỏ sót tổ hợp ngày gieo. Không tuyên bố tối ưu toàn cục. Chân trời 1–3 vụ vẫn vét cạn.
- Kết quả là **gợi ý để cân nhắc cùng cán bộ khuyến nông**, không thay thế khuyến cáo chuyên môn.


## A2: xuất xứ khuyến cáo

- [Công văn 2504/TTTV-TTBVTV, 19/6/2026](https://storage-vnportal.vnpt.vn/cmu-khdn/5342/Vanban/2026.6.19-cv-chi-dao-sx-trong-trot-ung-pho-elnino-2026_-_nqmanh_19062026180253__19062026180725_signed.pdf): tải và đọc PDF gốc ngày 14/11; `ev_official_2504`, `VERIFIED_PRIMARY_PDF`. Trích hướng giảm vụ/chuyển màu có điều kiện và phân biệt lịch tháng 10 với đợt 1 tháng 11; chưa phải khuyến cáo riêng cho thửa.
- [Tiền Phong 05/10/2026 dẫn SIWRR](https://tienphong.vn/khuyen-cao-mien-tay-ung-pho-han-man-gay-gat-mua-kho-sap-toi-post1882122.tpo): đã đọc bài báo ngày 14/11; `ev_siwrr_2026_press`, `PRESS_REPORT_ONLY`. Chưa đọc bản tin SIWRR gốc. Dùng thông tin thời gian, không biến ranh mặn theo sông thành ECw tại ruộng.

## A7: xung đột Tmax POWER–ERA5

Xem [HEAT_BIAS_REPORT.md](HEAT_BIAS_REPORT.md) để tái lập số trước/sau cho cả 4 điểm. Khi chênh lệch trung bình tháng tuyệt đối > **2 °C**, có ít nhất 60 cặp ngày trước as_of, chỉ đếm nóng trên Tmax POWER đã trừ chênh lệch so với ERA5. Giữ nguyên POWER gốc và cả hai evidence; `source_conflicts` ghi chính sách và số liệu theo tháng. Ngoài bundle ERA5, giữ POWER, trạng thái UNAVAILABLE. Chưa kiểm định phân bố cực trị ngày: Cần Thơ tháng 3 sau chỉnh vẫn 2,8 ngày ≥35 °C/năm so với ERA5 0,5; không gọi đây là sự thật tại ruộng.

**ET₀ không đổi:** giữ vector khí tượng POWER gốc để tránh ghép Tmax đã chỉnh với Tmin/điểm sương/bức xạ chưa chỉnh đồng bộ. A7 làm tưới baseline cố định thay đổi **0 mm** ở cả bốn điểm; sai lệch ET₀/tưới tuyệt đối vẫn chưa được khắc phục. Baseline nóng nhạy cảm (trung vị) Cần Thơ 14,5→0 ngày, Châu Đốc 21→2,5, Bến Tre 0,5→0, Sóc Trăng 0→0. Châu Đốc đổi top-1 ngô→đậu phộng vì tiêu chí stress đổi; tưới trung vị của top-1 tăng 1.208→1.323 mm (+115 mm) vì đổi chuỗi. Đây không phải lợi ích nước do hiệu chỉnh ET₀.

Nhãn độ tin cậy và số kịch bản đạt tiêu chí là so sánh **nội bộ mô hình**, không phải xác suất thành công. `production_value_index` được giải thích cuối cùng như điểm tham khảo do nhóm tự đặt; không phải ước tính thu nhập. `/v1/sources` khai rõ POWER là đầu vào quyết định, IMERG hỗ trợ thống kê, SRTM bối cảnh và SMAP/MODIS/Landsat/ECOSTRESS/GRACE chưa dùng.
