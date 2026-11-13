# FieldShift-Mekong — R&D: Climate-Adaptive Rotation Planner (CARP)

**Ngày nghiên cứu:** 12/11/2026. **Trạng thái:** đề xuất kiến trúc, chưa có kết quả hiệu chỉnh/kiểm định.  
**Tài liệu gốc:** `Field_Shift_Problem_Statement(2).md`, `FieldShift-Mekong — Bản thiết kế giải pháp.docx`.

## 1. Bài toán thực tế

NASA Space Apps 2026 yêu cầu một công cụ hỗ trợ nông dân **khám phá và so sánh các chiến lược luân canh**, kết hợp NASA Earth observations, dữ liệu đất địa phương, yêu cầu cây và ưu tiên nông dân. Dự báo khí tượng và mô hình tối ưu cụ thể **không phải yêu cầu bắt buộc**. Đề khuyến khích chỉ ra lợi ích tiềm năng đối với đất, khả năng thích ứng với nhiệt độ/mưa/nước, rủi ro và điều còn phải kiểm tra tại ruộng. Tham khảo [NASA challenge](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/) và [HackAthlone full description](https://hackathlone.com/challenges/adapting-farms-with-nasa-data).

**Lỗ hổng Solution cũ:** NASA POWER/IMERG 1991–2025 được phát lại trên chuỗi trồng trọt và lọc Pareto. Đó là historical stress-test, không tự dự báo điều kiện 2027; cũng chưa có bộ ước lượng trạng thái ban đầu đủ rõ hay mô hình hiệu ứng liên vụ được kiểm định. B4 sinh/lọc, B5 mô phỏng, B6 Pareto chưa tạo thành một lõi đề xuất mang thông tin tương lai.

## 2. Đối chiếu ứng dụng gần bài toán

| Hệ thống | Cơ chế được xác minh | Bài học/giới hạn |
|---|---|---|
| [DSSAT](https://dssat.net/about/) | Mô hình tăng trưởng dựa trên đất, khí tượng, giống, quản lý; có seasonal/sequence/rotation analysis. | Mô hình hệ quả giữa các lựa chọn, nhưng cần nhiều tham số và hiệu chỉnh. |
| [APSIM crop rotation tutorial 2025](https://apsim-rotationtraining.readthedocs.io/en/latest/) | `RotationManager`, lưu và chuyển nước, dinh dưỡng, hữu cơ qua các vụ; quản lý trạng thái liên tục. | Hướng phù hợp cho nghiên cứu đất dài hạn; phức tạp để tích hợp nguyên khối trong MVP. |
| [FAO AquaCrop 7.3](https://www.fao.org/aquacrop) | Mô phỏng sinh trưởng và năng suất dưới stress nước bằng thời tiết, cây, đất, quản lý; Python implementation công bố 30/07/2026. | Lõi crop response thực dụng nhưng không là một optimizer luân canh/dinh dưỡng hoàn chỉnh. |
| [ICRISAT iSAT](https://issca.icrisat.org/scalable-solutions/intelligent-agricultural-systems-advisory-tool-isat) | AI + rules + dự báo khí tượng + tình trạng cây/đất + hiểu biết địa phương -> tư vấn đúng thời điểm. | Minh họa cầu nối forecast -> khuyến nghị, không chứng minh đã tối ưu chuỗi luân canh. |
| [IRRI Rice Crop Manager](https://webapps.irri.org/bd/rcm/) | Dữ liệu phỏng vấn nông hộ -> khuyến nghị quản lý dinh dưỡng/cây theo địa điểm. | Minh họa thiết kế người dùng thật và dữ liệu thực địa; không trực tiếp chọn chuỗi đa cây. |

## 3. Nguồn dữ liệu: phân tầng theo công dụng

| Phân tầng | Nguồn | Chức năng | Giới hạn |
|---|---|---|---|
| Lịch sử khí tượng | [NASA POWER Daily](https://power.larc.nasa.gov/docs/services/api/temporal/daily/), [IMERG](https://gpm.nasa.gov/data/imerg) | Phân bố mưa/nhiệt/ET0, số ngày khô, dị thường, học tương quan | Không tự dự báo tương lai; khác lưới và mốc dữ liệu. |
| Trạng thái gần hiện tại | [SMAP L4](https://data.nasa.gov/dataset/smap-l4-global-3-hourly-9-km-ease-grid-surface-and-root-zone-soil-moisture-analysis-update), Landsat/HLS | Bối cảnh thiếu ẩm, lớp phủ, thời vụ | Ô vệ tinh không phải đo đạc thửa; NDVI không là SOC/NPK. |
| Địa hình | NASADEM/SRTM | Địa hình tương đối và cảnh báo ngập có điều kiện | Không biết hạ tầng đê bao/thoát nước. |
| Dự báo mùa | [NASA GEOS-S2S-3](https://gmao.gsfc.nasa.gov/gmao-products/geos-s2s-3/) / [ECMWF](https://www.ecmwf.int/en/forecasts/documentation-and-support/seasonal) | Phân bố bất định nhiệt/mưa 1–nhiều tháng | GEOS-S2S subsets được NASA cung cấp theo yêu cầu; cần kiểm tra khả dụng; độ phân giải vùng. |
| Kịch bản khí hậu tương lai | [NASA POWER Projection API](https://power.larc.nasa.gov/docs/services/api/projection/) dựa trên [NEX-GDDP-CMIP6](https://www.nasa.gov/ames/earth-science/nasa-earth-exchange-nex/gddp/downscaled-climate-projections-nex-gddp-cmip6/) | Dữ liệu theo ngày/tháng 2015–2100, 0.25°; 3 kịch bản SSP và nhiều GCM | **Climate projection** không phải dự báo 2027 chính xác; không gán xác suất xảy ra cho SSP. |
| Mặn/thủy văn vùng | [MRC forecasting](https://www.mrcmekong.org/flood-and-drought-forecasting/), [MRC modeling](https://www.mrcmekong.org/modelling-and-assessments/), [SIWRR](https://www.siwrr.org.vn/) | Lưu lượng, mức nước, thông tin/xu hướng mặn theo khu vực; kịch bản thiếu nước | Cần kiểm tra vị trí trạm, phạm vi, API, độ trễ. GEOS sea-surface salinity **không phải** EC nước kênh. |
| Thửa ruộng & nông học | SoilGrids/FAO/đo ECw-ECe/pH/thoát nước/tưới, giống, nhật ký canh tác, giá | Xây dựng trạng thái, ràng buộc, hiệu chỉnh/năng suất và thu nhập | Thiếu các phép đo quan trọng phải báo thiếu, không nội suy thành sự thật. |

## 4. Đề xuất lõi CARP (5 module)

1. **Field State Estimator**: ghép vị trí, đất, lịch sử, viễn thám và đo tại ruộng thành trạng thái khởi đầu \(s_0\) (dải khả dĩ nếu thiếu dữ liệu), tối thiểu nước đất, độ mặn/nguồn tưới, pH/kết cấu, khả năng thoát nước, cây vụ trước và nguồn lực.
2. **Climate & Water Risk Outlook**: sử dụng dự báo mùa khi tiếp cận và đã kiểm định, tạo *ensemble* tương lai tương ứng; dùng NASA historical để chuẩn hóa bias và lấy các chuỗi hợp lý, bảo toàn chuỗi ngày khô và tương quan mưa–nhiệt. Với 1–3 năm, dùng kịch bản NASA POWER Projection API/CMIP6, **không giả vờ dự báo chính xác năm cụ thể**. Mặn dùng nguồn địa phương/bản tin, cùng stress-test mặn sớm/lâu hơn và tình huống “không có nước ngọt”, được gắn nhãn kịch bản.
3. **Feasible Rotation Generator**: sinh hành động \(a_t=(\text{crop, planting date, irrigation, residue management})\) và tùy chọn nghỉ đất; lọc ràng buộc nghiêm ngặt (lịch mùa, thửa ngập/thoát nước, giống, ngân sách, mức nước có sẵn). ECw khác ECe; không loại cây chỉ vì vượt *ngưỡng bắt đầu giảm năng suất* nếu thiếu điều kiện.
4. **Crop–Soil Response Model**: với mỗi \((s_0,a_{1:T},w^{(j)})\), mô phỏng năng suất/nước/stress bằng FAO-56 hoặc AquaCrop đã hiệu chỉnh, cộng các trạng thái liên vụ *chỉ khi có cơ sở định lượng*. Chỉ báo đất thiếu kiểm định phải được ghi “lợi ích tiềm năng”, không gọi là SOC/NPK dự báo.
5. **Risk-aware Rotation Planner**: đánh giá cùng ensemble cho baseline và mỗi chuỗi; lọc không khả thi; so sánh sản lượng, nhu cầu tưới, ngưỡng thua lỗ, tổn thất đuôi, bảo vệ đất, chi phí chuyển đổi; lấy 3–5 phương án Pareto và chọn theo ưu tiên đã xác nhận. Khi có điều kiện mới, lặp lại từ đầu vụ tiếp theo (receding-horizon).

Biểu diễn trừu tượng:

\[
 s_{t+1}^{(j)}=f(s_t^{(j)}, a_t, w_t^{(j)}; \theta),\quad
 y^{(j)}=g(s_{1:T}^{(j)},a_{1:T},w_{1:T}^{(j)})
\]

Với mỗi chuỗi \(a\), dùng phân bố lợi nhuận/nước/rủi ro trên \(j\) kịch bản. Ví dụ ràng buộc \(\Pr(\mathrm{profit}(a)<L)\le\epsilon\) hoặc CVaR mất mát; đưa sức khỏe đất vào đánh giá theo mức độ có thể đo/kiểm chứng; không ép thành một điểm tổng duy nhất.

## 5. Quy trình lựa chọn phương án có thể triển khai

1. Chọn điểm ruộng -> đọc profile, nguồn tưới và baseline.
2. Đọc khí hậu lịch sử NASA; nhận biết thiếu ẩm, nóng, thiếu mưa theo giai đoạn; kiểm tra xu thế vùng.
3. Lấy forecast mùa sắp tới (nếu có và có skill), nếu không dùng climatology làm prior và các kịch bản stress; sử dụng projection NASA cho tầm nhìn dài hạn.
4. Sinh ensemble thời tiết và **ensemble mặn/nước riêng** (không ngầm hiểu lượng mưa = độ mặn kênh).
5. Sinh chuỗi 3 vụ gồm cả giữ nguyên, đổi 1 vụ, đổi lịch xuống giống, và tùy chọn nghỉ đất; loại chuỗi bất khả thi. Vốn/lịch máy móc/giống không đủ -> báo không khả thi.
6. Mô phỏng theo đúng cùng bộ kịch bản. Đầu ra có chênh lệch với baseline, ngưỡng an toàn, phần lợi ích được chứng minh và phần còn giả định.
7. Trình bày 3–5 lựa chọn có giải thích, không chỉ thứ hạng. Nếu thiếu dữ liệu mặn cốt yếu: yêu cầu đo trước khi chọn.
8. Cập nhật sau mỗi vụ khi có SMAP/Landsat/đo EC mới, lập kế hoạch lại thay vì cố định chuỗi 3 năm.

## 6. MVP và Roadmap

**MVP cho cuộc thi:** Dùng POWER Daily + IMERG + SMAP + SoilGrids + diện tích ruộng, baseline, 5–7 cây với lịch vụ, và bản tin mặn vùng; xây profile, phân tích điểm yếu baseline, tạo 3–5 chuỗi thỏa ràng buộc; tính nước và ngày stress bằng FAO-56 theo ensemble kịch bản, không tuyên bố yield chính xác khi chưa hiệu chỉnh. Tích hợp NASA POWER Projection API cho *climate scenarios* (có nhãn), thử GEOS-S2S nếu dữ liệu thực truy cập được. Chỉ báo đất gồm thời gian đất trống, kiểu luân canh, quản lý tàn dư; không gán SOC tăng x% nếu chưa mô hình hóa/kiểm định.

**Sau cuộc thi:** hiệu chỉnh AquaCrop 7.3 cho giống/đất địa phương, thêm nước ruộng lúa, ECe và cân bằng muối; tích hợp bản tin/dữ liệu mặn cập nhật; kiểm định lợi ích đất bằng mô hình liên vụ (APSIM/DSSAT có dữ liệu đầu vào); rolling optimization nhiều vụ và hệ thống giám sát chất lượng dự báo.

## 7. Thực nghiệm bắt buộc để chứng minh lõi dự đoán hữu ích

- **B0:** chuỗi hiện tại, không đổi.
- **B1:** rule-based suitability (đất + lịch + điều kiện tưới), không có NASA temporal features.
- **B2:** B1 + historical climatology/stress test từ NASA.
- **B3:** B2 + seasonal forecast/projection có phân loại rõ + scenario optimization (CARP).
- **Ablation:** B3 bỏ mô hình trạng thái liên vụ; B3 bỏ ràng buộc thực địa; B3 bỏ nhánh mặn.
- **Hindcast thời gian:** chọn ngày ra quyết định quá khứ, chỉ sử dụng dữ liệu đã có ở ngày đó, kiểm tra xác suất mùa khô/ẩm và stress với quan sát tương lai; báo skill so với climatology. Đánh giá yield cần quan trắc từ ruộng, không thể chứng minh yield counterfactual chỉ từ vệ tinh.
- **Decision utility:** so B1/B2/B3 trên tỷ lệ phương án bị chuyên gia loại, số lần vi phạm ngưỡng nước/thiệt hại, khả năng giải thích rủi ro và hiệu quả so baseline trong *cùng* môi trường giả định. Những con số thu được từ cùng model là chứng cứ hành vi mô hình, không phải xác nhận tác động thực.

## 8. Phản biện cần được ghi vào Solution

1. Quy hoạch 2027 không thể dự báo chính xác từng ngày từ projection CMIP6; dùng chuỗi và mức bất định, không giao tín nhiệm giả.
2. Một mô hình Time Series cho thời tiết không tự học được độ mặn nước kênh hoặc sức khỏe đất; nguồn bổ sung là bắt buộc.
3. NASADEM 30m không thay khảo sát hạ tầng ngập/thoát nước; SMAP 9km không phải ẩm đất thửa; SoilGrids không thay mẫu đất.
4. Chỉ tiêu cải thiện đất phải tách bằng chứng định tính và dự báo định lượng; lợi ích họ đậu không tự động xảy ra.
5. Forecast không có skill so với climatology thì không nên chi phối quyết định.
6. Không tuyên bố “tối ưu” khi có thiếu dữ liệu lớn hoặc khi heuristics/beam search chưa chứng minh tối ưu toàn cục.
7. Kịch bản mặn, nước khan, giá đầu ra phải được đánh dấu nguồn và giả định.
8. Thông tin riêng của thử thách được thông báo sẽ công bố ngày 13/11/2026; cần rà lại khi có nguồn chính thức.

**Đề xuất:** Đổi trọng tâm kiến trúc từ `Historical Replay Digital Twin` sang `Field State + Forecast/Scenario Engine + Crop/Soil Transition + Risk-Aware Rotation Planner`. Giữ Digital Twin để diễn giải khác biệt giữa baseline và các phương án — không xem nó là bộ khuyến nghị duy nhất.
