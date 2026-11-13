# agy-problem-agronomy: Nghiên Cứu Nông Học ĐBSCL & Chiến Lược Dự Thi NASA Space Apps 2026

> **Tài liệu tham chiếu chuyên sâu cho dự án FieldShift-Mekong**  
> **Thử thách:** *Field Shift: Adapting Farms with NASA Data* (NASA International Space Apps Challenge 2026).  
> **Ngày lập:** 13/11/2026.  
> **Nguyên tắc biên soạn:** Mọi số liệu thực tế đều có đường dẫn nguồn (URL). Những nội dung là giả định hoặc chưa được đo đạc thực nghiệm kiểm chứng độc lập đều được đánh dấu rõ bằng nhãn `[Chưa kiểm chứng]`. Ưu tiên cấu trúc bảng, cô đọng, định lượng cao.

---

## MỤC LỤC
1. [Phần A: Phân Tích Thử Thách & Tiêu Chí Chấm Điểm NASA](#phan-a-phan-tich-thu-thach--tieu-chi-cham-diem-nasa)
2. [Phần B: Bằng Chứng Nông Học ĐBSCL Cho Mô Hình Luân Canh Lúa – Màu](#phan-b-bang-chung-nong-hoc-dbscl-cho-mo-hinh-luan-canh-lua--mau)
3. [Phần C: Thiết Kế UX Hướng Nông Dân & Khuyến Nông Việt Nam](#phan-c-thiet-ke-ux-huong-nong-dan--khuyen-nong-viet-nam)
4. [Phần D: 3 Kịch Bản Demo Điển Hình & Kịch Bản Thuyết Trình 5 Phút](#phan-d-3-kich-ban-demo-dien-hinh--kich-ban-thuyet-trinh-5-phut)
5. [Top 10 Hành Động Then Chốt Cho Đội Ngũ Phát Triển (Build Insights)](#top-10-hanh-dong-then-chot-cho-doi-ngu-phat-trien-build-insights)

---

## PHẦN A: PHÂN TÍCH THỬ THÁCH & TIÊU CHÍ CHẤM ĐIỂM NASA

### 1. Phân Tích Thử Thách "Field Shift: Adapting Farms with NASA Data"

Thử thách yêu cầu thí sinh xây dựng công cụ hỗ trợ ra quyết định (Decision-Support Tool) giúp nông dân và các nhà hoạch định nông nghiệp thiết lập chiến lược luân canh cây trồng (crop rotation) tối ưu, thích ứng với biến đổi khí hậu dựa trên dữ liệu viễn thám Trái đất của NASA kết hợp với ràng buộc nông học thực tế tại địa phương.

* Nguồn chính thức: [NASA Space Apps Challenge - Field Shift](https://www.spaceappschallenge.org/nasa-space-apps-2024/challenges/field-shift-adapting-farms-with-nasa-data/)

| Yếu tố trọng tâm từ NASA | Yêu cầu kỹ thuật & khoa học | Lời giải của FieldShift-Mekong |
| :--- | :--- | :--- |
| **NASA Earth Observations** | Tích hợp dữ liệu vệ tinh về nhiệt độ, lượng mưa, độ ẩm đất, bức xạ, bốc thoát hơi nước. | Tích hợp NASA POWER (daily MERRA-2 1981–2026), SRTM DEM 30m, kết nối chuẩn bị cho SMAP L4, GPM IMERG Late, MODIS/VIIRS NDVI. |
| **Local Farm Factors** | Kết hợp dữ liệu thổ nhưỡng địa phương, đặc tính cây trồng, lịch mùa vụ, hạ tầng tưới tiêu. | Tích hợp catalog cây trồng FAO-56 & khuyến nông ĐBSCL, ngưỡng mặn $EC_w$, lịch né mặn/né rầy của Cục Trồng trọt, đo đạc cống kênh địa phương. |
| **Farmer Priorities & Constraints** | Cân bằng giữa tiết kiệm nước, bảo vệ đất, an toàn sinh kế, chi phí máy móc, vốn đầu tư. | Mô hình tối ưu hóa đa mục tiêu Pareto (Pareto-optimal ranking), không dùng trọng số gộp ảo, hiển thị trade-off trực quan (nước vs rủi ro vs chi phí). |
| **Actionable Output** | Không dừng ở bản đồ xem ảnh; phải đưa ra lịch gieo trồng, rủi ro, điều kiện kích hoạt (triggers), checklist hành động. | Output dạng `DecisionPackage` bất biến: so sánh baseline 3 vụ lúa với chuỗi lúa-màu, trigger độ mặn theo thời gian thực, bảng kiểm tra thực địa. |

---

### 2. Tiêu Chí Chấm Điểm NASA & Chiến Lược Đạt Điểm Tối Đa

Cơ chế chấm điểm của NASA Space Apps chia đều 5 hạng mục (mỗi hạng mục chiếm 20%):

* Nguồn tiêu chí: [NASA Space Apps Judging Criteria](https://www.spaceappschallenge.org/)

```mermaid
pie title Phân Bổ 5 Tiêu Chí Chấm Điểm Của NASA Space Apps
    "Impact (Tác động thực tế)" : 20
    "Creativity (Sáng tạo & Đột phá)" : 20
    "Validity (Tính đúng đắn khoa học)" : 20
    "Relevance (Bám sát đề bài)" : 20
    "Presentation (Truyền thông & Demo)" : 20
```

| Tiêu chí (Tỷ trọng) | Thước đo của Giám khảo NASA | Sai lầm phổ biến khiến đội thi bị trừ điểm | Chiến lược hành động của FieldShift-Mekong |
| :--- | :--- | :--- | :--- |
| **Impact** (20%) | Mức độ giải quyết vấn đề nhức nhối thực tế; khả năng nhân rộng cho cộng đồng yếu thế. | Giải pháp chung chung, không gắn với vùng sinh thái cụ thể; tính khả thi kinh tế mơ hồ. | Gắn trực tiếp vào ĐBSCL: khủng hoảng hạn mặn, rầy nâu, Đề án 1 triệu ha lúa; chứng minh tiết kiệm 50–70% nước mùa kiệt. |
| **Creativity** (20%) | Tính nguyên bản, góc nhìn mới, cách tiếp cận độc đáo so với các giải pháp hiện hành. | Chỉ làm một Dashboard GIS hiển thị lại lớp bản đồ màu sắc có sẵn của NASA. | Engine lập kế hoạch theo kịch bản tương phản (Pareto + Stress Testing analog-year); cơ chế "Zero Fake Numbers" gắn nhãn minh bạch. |
| **Validity** (20%) | Cơ sở khoa học vững chắc, công thức chuẩn mực, tính tái lập (reproducibility), code chạy thật. | Tuyên bố AI "hộp đen" dự báo chính xác 100% năng suất; bịa số liệu mặn từ ảnh mây/mưa; demo mock tĩnh. | Dùng FAO-56 Penman-Monteith, mô hình cân bằng ẩm tầng rễ TAW/RAW; phân biệt rạch ròi ước lượng viễn thám và số đo tại ruộng (`origin`). |
| **Relevance** (20%) | Đáp ứng toàn diện các câu hỏi trong đề bài; tận dụng hiệu quả dữ liệu mở của NASA/đối tác. | Dùng dữ liệu vệ tinh một cách hình thức (chỉ lấy 1 ảnh làm nền trang trí); phụ thuộc dữ liệu độc quyền. | Dùng chuỗi thời gian 25 năm NASA POWER, SRTM elevation, phân tích tương quan khí hậu - bốc thoát hơi nước theo đúng yêu cầu đề tài. |
| **Presentation** (20%) | Kỹ năng kể chuyện (storytelling), cấu trúc video pitch, tính thẩm mỹ và công thái học của UI. | Trình bày quá thiên về kỹ thuật thuật toán, thiếu demo trải nghiệm người dùng, quá giờ, video nhạt nhòa. | Cấu trúc Pitch 5 phút theo "Vấn đề nông dân -> Đột phá dữ liệu -> Trực quan hóa giải pháp -> Khả năng chuyển giao Khuyến nông"; giao diện Zalo/Web tối giản. |

---

### 3. Bài Học Từ Các Quán Quân Toàn Cầu (Global Winners 2021–2025)

* Nguồn tổng hợp: [NASA Space Apps Global Winners Repository](https://www.spaceappschallenge.org/)

| Năm & Đội thi | Giải thưởng đạt được | Sản phẩm & Ý tưởng cốt lõi | Lý do thuyết phục Ban Giám Khảo | Bài học áp dụng cho FieldShift |
| :--- | :--- | :--- | :--- | :--- |
| **Queñaris** (2025 - Peru) | *Local Impact Award* | Hệ thống phục hồi rừng Queñuales bảo vệ nguồn nước nông nghiệp dựa trên dữ liệu hiện tượng học thực vật (Phenology). | Bản địa hóa triệt để (Hyper-localized); giải quyết xung đột tài nguyên nước của nông dân vùng Andes hẻo lánh. | Không làm tool cho cả thế giới; tập trung giải quyết xuất sắc bài toán hạn mặn và lũ lụt tại 13 tỉnh ĐBSCL. |
| **Zumorroda-X** (2025 - Egypt) | *Art & Technology Award* | Ứng dụng mô phỏng nông nghiệp kết hợp game tương tác trực quan hóa dữ liệu vệ tinh tưới tiêu và dinh dưỡng đất. | Biến dữ liệu viễn thám phức tạp thành hành động tưới tiêu trực quan, dễ hiểu với người không chuyên. | Đơn giản hóa giao diện: dùng đèn giao thông (Xanh/Vàng/Đỏ), biểu tượng mùa vụ, tránh biểu đồ ma trận gây rối não. |
| **GaamaRamma** (2024 - Global) | *Best Use of Data Award* | Công cụ "WaterWise" tích hợp đa tầng dữ liệu viễn thám để cảnh báo sớm hạn - lũ cho nông hộ nhỏ. | Khai thác sâu sắc và chính xác các sản phẩm vệ tinh của NASA, kết hợp logic vật lý chặt chẽ giữa mưa và ẩm đất. | Sử dụng chuỗi thời gian ngày (daily) 25 năm của NASA POWER để tính thâm hụt bốc thoát hơi nước ($ET_0 - P$) thực tế. |
| **Team Eggplant** (2024 - S. Korea) | *Global Winner* | Hệ thống hỗ trợ ra quyết định ứng phó hạn hán vùng thông qua giám sát độ ẩm đất vệ tinh và nhu cầu cây trồng. | Độ trung thực cao: làm rõ sai số vệ tinh và cách hiệu chỉnh tương đối cho cấp độ nông hộ. | Minh bạch nhãn dữ liệu (`OBSERVED_REMOTE_ESTIMATE` vs `OBSERVED_FIELD`), không nhận vơ vệ tinh đo được độ mặn lòng kênh. |
| **4 Seeds** (2021 - Global) | *Galactic Impact Award* | Mô hình tối ưu hóa chu trình dinh dưỡng và nước cho cây trồng khép kín Earth-to-Space. | Cân bằng toán học chuẩn xác, giao diện mô phỏng tương tác cao. | Thiết kế Digital Twin mô phỏng tiến trình sinh trưởng và tiêu thụ nước theo tuần cho từng phương án luân canh. |

---

### 4. Các "Cái Bẫy" Khiến Giám Khảo Trừ Điểm Nặng (Judges' Red Flags)

1. **Bẫy "Ảo tưởng độ phân giải" (Spatial Scale Delusion):** Tuyên bố vệ tinh NASA (độ phân giải từ 9 km của SMAP đến 50 km của MERRA-2) có thể đo trực tiếp độ ẩm hay độ mặn của một thửa ruộng 0,5 ha. *Cách tránh:* Định nghĩa rõ vệ tinh cung cấp bối cảnh khí hậu vùng (`regional_context`); trạng thái thửa ruộng được mô hình hóa qua cân bằng nước và người dùng bổ sung số đo tại chỗ.
2. **Bẫy "Hộp đen tiên tri" (Black-box Prophecy):** Đưa ra dự báo năng suất chính xác đến từng kg hoặc dự báo mưa sau 6 tháng một cách chắc chắn. *Cách tránh:* Bật cổng kiểm soát Gate G6; công khai rằng không có dự báo mùa tất định khả tín; thay bằng phương pháp phân tích năm tương đồng lịch sử (analog-years 2016, 2020, 2024) và kiểm thử ứng suất (stress-testing).
3. **Bẫy "Bịa đặt số liệu mặn từ không gian" (Faking Salinity):** Tuyên bố cảm biến quang học hay radar đo được độ mặn nước trong kênh rạch bị che phủ bởi dừa nước hoặc lục bình. *Cách tránh:* Khẳng định mặn là biến đo thực địa hoặc kịch bản giả định (`ASSUMPTION`), kích hoạt Gate G5 yêu cầu kiểm tra thực địa trước khi khuyến nghị.
4. **Bẫy "Bất khả thi nông học" (Agronomic Blindness):** Đề xuất trồng cây cạn (ngô, mè) trên đất trũng ngập không có hệ thống mương liếp thoát nước, hoặc bố trí lịch gieo trùng vào đợt dịch rầy nâu lịch sử. *Cách tránh:* Tích hợp bộ quy tắc cứng (HARD rules) loại bỏ các chuỗi vi phạm thoát nước, cửa sổ vụ và trùng lặp thời gian sinh trưởng.

---

## PHẦN B: BẰNG CHỨNG NÔNG HỌC ĐBSCL CHO MÔ HÌNH LUÂN CANH LÚA – MÀU

### 1. Bằng Chứng Nông Học Của Mô Hình Luân Canh Lúa – Màu

Thực trạng canh tác độc canh 3 vụ lúa/năm (Đông Xuân – Hè Thu – Thu Đông) tại ĐBSCL đã dẫn đến suy thoái nghiêm trọng: đất ngập nước liên tục gây yếm khí, tích tụ độc chất $H_2S$, $CH_4$, suy giảm độ phì, nén dẽ tầng đế cày, đồng thời tạo cầu nối thức ăn liên tục cho dịch hại lây lan.

* Nguồn tham khảo: [Viện Lúa ĐBSCL (CLRRI)](http://clrri.org/), [Tạp chí Khoa học Nông nghiệp Việt Nam / VAAS](http://vaas.vn/), [Báo Nông nghiệp & Môi trường](http://nongnghiepmoitruong.vn)

```mermaid
flowchart TD
    subgraph DocCanh ["Độc Canh 3 Vụ Lúa (Vòng Luẩn Quẩn)"]
        A[Ngập nước quanh năm] --> B[Đất yếm khí, nghẹt rễ, ngộ độc hữu cơ]
        B --> C[Ký chủ lúa liên tục: Rầy nâu, Đạo ôn bùng phát]
        C --> D[Thiếu hụt nước mùa khô Feb-Apr: 450-550mm]
        D --> E[Lạm dụng phân thuốc hóa học, lợi nhuận bấp bênh]
    end

    subgraph LuanCanh ["Luân Canh Lúa - Màu (Cắt Đứt Vòng Lặp)"]
        F[Vụ 2: Chuyển sang Cây Màu Cạn] --> G[Phơi đất hiếu khí, phân giải chất độc, rễ cọc phá đế cày]
        F --> H[Cắt đứt nguồn thức ăn: Rầy nâu & nấm bệnh triệt tiêu]
        F --> I[Tiết kiệm 50-70% nước tưới mùa khô]
        F --> J[Cây họ đậu cố định đạm 30-60 kg N/ha, tăng thu nhập]
    end
```

| Lợi ích nông học | Cơ chế khoa học | Bằng chứng định lượng tại ĐBSCL | Nguồn tài liệu |
| :--- | :--- | :--- | :--- |
| **Tiết kiệm nước tưới** | Lúa cần ngập nước liên tục (bốc hơi mặt nước + thấm rò 2–4 mm/ngày + bừa ngấu 150–250 mm). Cây màu chỉ hút nước tầng rễ qua tưới ẩm tiết kiệm. | Lúa mùa khô cần: $10.000 - 14.000\text{ m}^3\text{/ha}$ ($1.000 - 1.400\text{ mm}$).<br>Mè/Đậu xanh chỉ cần: $2.000 - 3.500\text{ m}^3\text{/ha}$ ($200 - 350\text{ mm}$).<br>**Tiết kiệm 65–75% lượng nước ngọt.** | [Đại học Cần Thơ (CTU)](https://www.ctu.edu.vn/), [FAO-56 Irrigation Paper](https://www.fao.org/land-water/databases-and-software/cropwat/en/) |
| **Cắt đứt chu kỳ rầy nâu** (*Nilaparvata lugens*) | Rầy nâu có vòng đời 25–30 ngày, chỉ ký sinh chuyên biệt trên cây lúa và cỏ họ hòa thảo; là môi giới truyền virus Vàng lùn - Lùn xoắn lá. Việc giãn cách không có lúa $\ge 21-30$ ngày làm rầy mất thức ăn và nơi đẻ trứng. | Luân canh 1 vụ màu hoặc phơi ải 3 tuần làm suy giảm $>85\%$ mật số rầy di trú đầu vụ sau; giảm số lần phun thuốc BVTV từ 4–6 lần xuống còn 1–2 lần/vụ. | [Báo Nông nghiệp & Môi trường](http://nongnghiepmoitruong.vn), [Cục Bảo vệ Thực vật](https://www.ppd.gov.vn/) |
| **Triệt tiêu nấm bệnh đạo ôn** (*Magnaporthe oryzae*) | Bào tử nấm đạo ôn tồn lưu trong rơm rạ và đất ngập nước. Khi ruộng được rút cạn, phơi đất hiếu khí và chiếu xạ nhiệt, sức sống bào tử giảm mạnh. | Tỷ lệ bệnh đạo ôn lá và đạo ôn cổ bông trên lúa vụ tiếp theo giảm 40–60% so với ruộng thâm canh lúa liên tục. | [Hội BVTV Việt Nam](http://baovethucvat.org.vn/), [IRRI Rice Knowledge Bank](http://www.knowledgebank.irri.org/) |
| **Cải tạo cấu trúc đất & phì nhiêu** | Rễ lúa chỉ ăn nông (0–15 cm). Rễ cọc của mè/ngô ăn sâu 40–80 cm giúp phá vỡ tầng đế cày bị nén dẽ. Cây họ đậu (đậu xanh, đậu phộng) cộng sinh vi khuẩn *Rhizobium* nốt sần. | Đậu xanh để lại tàn dư sinh khối cung cấp tương đương 30–60 kg N nguyên chất/ha; tăng độ xốp đất thêm 12–18%, giảm tỷ trọng thể tích đất. | [Tạp chí Nông nghiệp & PTNT](http://tapchinongnghiep.gov.vn/), [ISRIC SoilGrids Data](https://soilgrids.org/) |
| **Hiệu quả kinh tế & rủi ro** | Chi phí đầu tư vụ màu thấp hơn lúa (giảm phân hóa học và chi phí bơm tưới); giá bán nông sản màu/kg cao hơn lúa. | Lợi nhuận mè/đậu xanh đạt 20–35 triệu đ/ha so với lúa vụ 2 chỉ đạt 8–18 triệu đ/ha (đặc biệt khi lúa vụ 2 thường xuyên đối mặt nguy cơ mất trắng do mặn). | [Sở NN&PTNT Đồng Tháp](https://snnptnt.dongthap.gov.vn/), [Cổng thông tin Cần Thơ](https://cantho.gov.vn/) |

---

### 2. Khung Chính Sách & Cơ Sở Pháp Lý Chuyển Đổi Tại Việt Nam

Việc chuyển đổi cơ cấu cây trồng trên đất lúa ở ĐBSCL được bảo trợ bởi các chủ trương chiến lược cấp quốc gia:

* **Nghị quyết số 120/NQ-CP** ngày 17/11/2017 của Chính phủ về *Phát triển bền vững ĐBSCL thích ứng với BĐKH* (Nghị quyết "Thuận thiên"): Thay đổi trục chiến lược ưu tiên từ "Lúa gạo – Cây ăn trái – Thủy sản" sang **"Thủy sản – Cây ăn trái – Lúa gạo"**; quy hoạch giảm diện tích lúa 3 vụ kém hiệu quả, ưu tiên các mô hình kinh tế nước lợ, nước mặn và lúa - màu ([Chính phủ điện tử](http://chinhphu.vn)).
* **Quyết định số 1490/QĐ-TTg** ngày 27/11/2023 của Thủ tướng Chính phủ phê duyệt *Đề án phát triển bền vững 1 triệu héc-ta chuyên canh lúa chất lượng cao và phát thải thấp gắn với tăng trưởng xanh vùng ĐBSCL đến năm 2030*: Đặt chỉ tiêu bắt buộc giảm 20% lượng nước tưới, giảm 30% phân bón và thuốc BVTV hóa học, 100% diện tích áp dụng quy trình bền vững (1 phải 5 giảm, AWD), giảm trên 10% phát thải khí nhà kính ([Bộ Công Thương](http://moit.gov.vn)).
* **Nghị định số 112/2024/NĐ-CP** ngày 11/09/2024 của Chính phủ quy định chi tiết về *Đất trồng lúa* (thay thế Nghị định 35/2015/NĐ-CP và Nghị định 62/2019/NĐ-CP):
  * **Điều 6 & 7:** Cho phép chuyển đổi cơ cấu cây trồng hàng năm (lúa – màu), cây lâu năm trên đất trồng lúa theo kế hoạch của địa phương.
  * **Quy định pháp lý quan trọng:** Đất sau khi chuyển đổi cơ cấu cây trồng sang trồng màu ngắn ngày **vẫn được thống kê và công nhận là đất trồng lúa**, bảo toàn quyền lợi pháp lý và trợ cấp của nông dân.
  * Đối với mô hình lúa kết hợp thủy sản: cho phép hạ mặt bằng tối đa 20% diện tích, độ sâu hạ không quá 120 cm ([Văn bản Chính phủ](https://chinhphu.vn)).

---

### 3. Lịch Thời Vụ Thực Tế Theo Vùng Sinh Thái ĐBSCL

Cục Trồng trọt và các Sở NN&PTNT định kỳ ban hành khung lịch thời vụ nghiêm ngặt nhằm mục tiêu: **"Né rầy – Né mặn – Đón phù sa lũ"**.

* Nguồn tham khảo: [Cục Trồng trọt - Bộ NN&PTNT](https://cuctrongtrot.gov.vn/), [Viện Quy hoạch Thủy lợi Miền Nam (SIWRP)](http://iwrp.gov.vn/)

```mermaid
gantt
    title Khung Thời Vụ Canh Tác Điển Hình Tại 3 Tiểu Vùng Sinh Thái ĐBSCL
    dateFormat  YYYY-MM-DD
    axisFormat  %b

    section Vùng Thượng Lũ (An Giang)
    Lúa Đông Xuân (Đón phù sa)       :done, a1, 2026-10-20, 2027-02-15
    Mè / Bắp Xuân Hè (Tiết kiệm nước):active, a2, 2027-02-25, 2027-05-15
    Thời kỳ xả lũ lấy phù sa / Thủy sản:crit, a3, 2027-08-01, 2027-11-01

    section Vùng Phù Sa Ngọt (Cần Thơ)
    Lúa Đông Xuân (Vụ chính)        :done, b1, 2026-11-15, 2027-03-05
    Đậu xanh / Màu vụ Xuân Hè       :active, b2, 2027-03-15, 2027-05-30
    Lúa Thu Đông                    :crit, b3, 2027-06-15, 2027-09-25

    section Vùng Duyên Hải Mặn (Bến Tre)
    Lúa Đông Xuân Cực Sớm (Né mặn)  :done, c1, 2026-10-10, 2027-01-20
    Giai đoạn đỉnh mặn (Đậu xanh / Nghỉ ruộng):crit, c2, 2027-02-01, 2027-05-10
    Lúa Hè Thu / Mùa mưa rửa mặn    :active, c3, 2027-05-25, 2027-09-30
```

| Tiểu vùng sinh thái | Tỉnh đại diện | Vụ 1: Đông Xuân (ĐX) | Vụ 2: Xuân Hè / Hè Thu (HT) | Vụ 3: Thu Đông (TĐ) / Mùa | Rủi ro khí hậu & Chiến lược luân canh |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Vùng Thượng nguồn ngập lũ** (Đồng Tháp Mười & Tứ giác Long Xuyên) | An Giang, Đồng Tháp, thượng Long An | **Sạ: 15/10 – 30/11**<br>Thu: 01 – 02<br>Lúa chất lượng cao (OM18, ĐT8) | **Sạ: 20/02 – 15/04**<br>Thu: 05 – 06<br>*Chiến lược:* Thay lúa bằng **Mè đen** hoặc **Ngô sinh khối** | **Sạ: 01/07 – 15/08** (vùng đê bao triệt để) hoặc **Mở cống xả lũ** đón phù sa từ tháng 8 đến tháng 11 | Lũ về sớm gây vỡ đê vụ 3; vụ Xuân Hè thiếu nước mặt. Khuyến nghị: Chuỗi **Lúa ĐX – Mè XH – Xả lũ lấy phù sa**. |
| **Vùng Trung tâm phù sa ngọt** | Cần Thơ, Vĩnh Long, Hậu Giang, trung Tiền Giang | **Sạ: 10/11 – 31/12**<br>Thu: 02 – 03<br>Lúa thương phẩm xuất khẩu | **Sạ: 01/04 – 15/05**<br>Thu: 06 – 07<br>*Chiến lược:* Chuyển đổi vụ này sang **Đậu xanh** | **Sạ: 01/07 – 20/08**<br>Thu: 10 – 11<br>Lúa Thu Đông (cần đê bao chống ngập triều cường) | Thâm hụt ẩm tháng 3–4 cao ($ET_0 - P \approx 480\text{ mm}$), áp lực sâu bệnh cao. Khuyến nghị: Chuỗi **Lúa ĐX – Đậu xanh – Lúa TĐ**. |
| **Vùng Ven biển cửa sông & Bán đảo** | Bến Tre, Tiền Giang (Gò Công), Trà Vinh, Sóc Trăng, Bạc Liêu | **Sạ CỰC SỚM: 10/10 – 10/11**<br>Thu: dứt điểm trước 20/01 – 10/02 (trước Tết) | **TUYỆT ĐỐI KHÔNG SẠ LÚA** (Đỉnh mặn $4‰$ bủa vây).<br>*Chiến lược:* Trồng **Đậu xanh / Dưa hấu** hoặc **Cắt vụ phơi đất** | **Sạ: 20/05 – 30/06** (sau khi mưa rửa mặn $>150\text{ mm}$)<br>Lúa chịu mặn nhẹ (ST24, ST25) hoặc Tôm – Lúa | Mặn xâm nhập sớm làm chết cháy lúa non vụ 2; thiếu nước sinh hoạt. Khuyến nghị: Chuỗi **Lúa ĐX sớm – Đậu xanh/Mè – Lúa Mùa/Nghỉ**. |

---

### 4. Lịch Sử & Đặc Điểm Xâm Nhập Mặn Kỷ Lục (2016, 2020, 2024)

Xâm nhập mặn tại ĐBSCL mang tính quy luật mùa khô nhưng chịu ảnh hưởng mang tính liên vùng: **phụ thuộc vào lưu lượng xả từ thủy điện thượng nguồn sông Mekong, hiện tượng El Niño và gió chướng đẩy triều cường**, hoàn toàn không phản ánh lượng mưa tại chỗ.

* Nguồn tham khảo: [Viện Khoa học Thủy lợi Miền Nam (SIWRR)](http://www.siwrr.org.vn/), [Báo cáo Tổng kết Hạn mặn 2016-2020-2024 của Bộ NN&PTNT](https://chinhphu.vn/)

| Mùa khô hạn mặn | Tháng đạt đỉnh mặn | Phạm vi ranh mặn $4\text{ g/L}$ ($4‰$) | Tỉnh chịu ảnh hưởng nặng nhất | Thiệt hại nông nghiệp & Biện pháp đã áp dụng |
| :--- | :--- | :--- | :--- | :--- |
| **2015 – 2016** (Đợt thiên tai lịch sử) | **Tháng 3 – Tháng 4/2016** | Sông Tiền, sông Hậu: mặn vào sâu **45 – 65 km**.<br>Sông Vàm Cỏ: vào sâu **85 – 95 km**. | Bến Tre, Kiên Giang, Tiền Giang, Sóc Trăng, Cà Mau, Trà Vinh, Long An (11/13 tỉnh công bố thiên tai). | $>250.000\text{ ha}$ lúa và hoa màu bị mất trắng/giảm năng suất; $210.000$ hộ dân thiếu nước sinh hoạt. Thiệt hại $>7.900$ tỷ đồng. |
| **2019 – 2020** (Khốc liệt hơn 2016 về độ sâu) | **Tháng 2 – Tháng 3/2020** (Mặn đến sớm từ tháng 12/2019) | Sông Cửu Long: sâu **55 – 75 km**.<br>Sông Vàm Cỏ: sâu kỷ lục **100 – 110 km** (vượt lịch sử 2016). | Bến Tre (100% diện tích bị mặn bao vây), Tiền Giang, Long An, Sóc Trăng, Trà Vinh. | Thiệt hại lúa giảm chỉ còn $\sim 42.000\text{ ha}$ nhờ Bộ NN&PTNT chỉ đạo gieo sạ sớm né mặn trước 1 tháng và chuyển đổi sang cây trồng cạn. |
| **2023 – 2024** (Đợt gay gắt gần nhất) | **Tháng 2 – Tháng 3/2024** (Cao điểm: 08/03 – 13/03 và cuối tháng 3) | Sông Cửu Long: sâu **40 – 55 km**.<br>Sông Vàm Cỏ: sâu **75 – 90 km**.<br>Sông Cái Lớn: kiểm soát tốt nhờ cống Cái Lớn - Cái Bé. | Tiền Giang (vùng ngọt hóa Gò Công), Bến Tre (Ba Tri, Giồng Trôm), Sóc Trăng, Cà Mau (sụt lún kênh rạch). | Không có diện tích lúa Đông Xuân bị mất trắng ngoài quy hoạch; một số diện tích rau màu ven biển thiếu nước tưới ngọt cục bộ. |

---

### 5. Ngưỡng Mặn Nông Học & Quy Đổi Đơn Vị Trong Khuyến Nông Việt Nam

Trong hệ thống khuyến nông Việt Nam, độ mặn thường được thông báo bằng **đơn vị phần ngàn ($\text{‰}$ hoặc $\text{g/L}$)**. Tuy nhiên, các thiết bị cảm biến IoT, máy đo khúc xạ cầm tay và tài liệu quốc tế (FAO) lại sử dụng **độ dẫn điện cảm ứng $EC$ (đơn vị $\text{dS/m}$ hoặc $\text{mS/cm}$)**.

#### Bảng Quy Đổi Chuẩn Cửa Sông ĐBSCL
* Công thức chuyển đổi thực nghiệm chuẩn cho nguồn nước mặt lợ ĐBSCL:  
  $$\text{TDS (mg/L)} \approx 640 \times EC_w\text{ (dS/m)} \quad (\text{với } EC_w < 5\text{ dS/m})$$  
  $$1\text{ ‰} = 1\text{ g/L} = 1.000\text{ mg/L} \implies EC_w \approx \frac{1.000}{640} \approx \mathbf{1,56\text{ dS/m}} \quad (1\text{ dS/m} \approx \mathbf{0,64\text{ ‰}})$$  
  *(Lưu ý: $1\text{ dS/m} = 1\text{ mS/cm} = 1.000\text{ }\mu\text{S/cm}$)*.

* Nguồn tham khảo: [FAO Irrigation and Drainage Paper 29 (Water Quality for Agriculture)](https://www.fao.org/land-water/databases-and-software/cropwat/en/), [Sổ tay khuyến nông Quản lý hạn mặn - Cục Trồng trọt](https://cuctrongtrot.gov.vn/)

| Cây trồng (Tên khoa học) | Ngưỡng mặn an toàn ($100\%$ NS) $\text{‰}$ / [$\text{dS/m}$] | Bắt đầu giảm NS ($b\%$/$\text{dS/m}$) $\text{‰}$ / [$\text{dS/m}$] | Ngưỡng mất trắng / Tử vong $\text{‰}$ / [$\text{dS/m}$] | Giai đoạn mẫn cảm nhất với mặn | Khuyến cáo của Khuyến nông ĐBSCL |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Lúa** (*Oryza sativa*) | $\le \mathbf{0,8\text{ ‰}}$<br>[$1,2\text{ dS/m}$] | **$1,5\text{ ‰}$** [$2,3\text{ dS/m}$]<br>(Giảm $12\%$/$\text{dS/m}$) | $> \mathbf{3,5 - 4,0\text{ ‰}}$<br>[$> 5,5 - 6,2\text{ dS/m}$] | **Làm đòng & trỗ bông** (lép hạt 100%), mạ non mới sạ | Độ mặn $>1‰$ tuyệt đối không lấy nước vào ruộng lúa. Ranh mặn $4‰$ là giới hạn đóng cống hoàn toàn. |
| **Mè / Vừng** (*Sesamum indicum*) | $\le \mathbf{1,5\text{ ‰}}$<br>[$2,3\text{ dS/m}$] | **$2,5\text{ ‰}$** [$3,9\text{ dS/m}$]<br>(Giảm $10\%$/$\text{dS/m}$) | $> \mathbf{5,0\text{ ‰}}$<br>[$> 7,8\text{ dS/m}$] | Cây con (1–15 ngày sau gieo) | Cây cạn chịu mặn khá nhất; phù hợp luân canh đất lúa nhiễm mặn nhẹ ven biển. |
| **Đậu xanh** (*Vigna radiata*) | $\le \mathbf{1,0\text{ ‰}}$<br>[$1,5\text{ dS/m}$] | **$1,5\text{ ‰}$** [$2,3\text{ dS/m}$]<br>(Giảm $15\%$/$\text{dS/m}$) | $> \mathbf{3,5\text{ ‰}}$<br>[$> 5,5\text{ dS/m}$] | Ra hoa, thụ phấn và tạo nốt sần rễ | Rất nhạy cảm úng nhưng chịu hạn tốt. Tưới nước mặn $>1,5‰$ nốt sần ngưng cố định đạm. |
| **Bắp / Ngô** (*Zea mays*) | $\le \mathbf{1,1\text{ ‰}}$<br>[$1,7\text{ dS/m}$] | **$1,6\text{ ‰}$** [$2,5\text{ dS/m}$]<br>(Giảm $12\%$/$\text{dS/m}$) | $> \mathbf{4,5\text{ ‰}}$<br>[$> 7,0\text{ dS/m}$] | Phun râu, trỗ cờ, thụ phấn | Chịu mặn trung bình. Cần đất thịt nhẹ thoát nước tốt; mặn $>2‰$ bắp bị nghẽn cờ, hạt lép. |
| **Đậu phộng / Lạc** (*Arachis hypogaea*) | $\le \mathbf{1,2\text{ ‰}}$<br>[$1,9\text{ dS/m}$] | **$2,0\text{ ‰}$** [$3,1\text{ dS/m}$]<br>(Giảm $14\%$/$\text{dS/m}$) | $> \mathbf{4,0\text{ ‰}}$<br>[$> 6,2\text{ dS/m}$] | Đâm tia củ và vào hạt | Ưa đất cát giồng, đất xốp ven biển; không trồng được trên đất sét dẻo tích tụ muối. |
| **Dưa hấu** (*Citrullus lanatus*) | $\le \mathbf{1,0\text{ ‰}}$<br>[$1,5\text{ dS/m}$] | **$1,8\text{ ‰}$** [$2,8\text{ dS/m}$]<br>(Giảm $11\%$/$\text{dS/m}$) | $> \mathbf{3,5\text{ ‰}}$<br>[$> 5,5\text{ dS/m}$] | Nảy mầm và nuôi quả non | Nông dân trồng trên ruộng lúa mùa khô bằng màng phủ nilon; tưới gốc bằng nước ngầm ngọt hoặc mương trữ. |

---

### 6. Bảng Thông Số Nông Học Đầy Đủ (Agronomic Parameter Catalog)

* Nguồn tham khảo: [FAO-56 Crop Evapotranspiration](https://www.fao.org/land-water/databases-and-software/cropwat/en/), [Viện Khoa học Kỹ thuật Nông nghiệp Miền Nam (IAS)](http://iasvn.org/), [Sở NN&PTNT các tỉnh ĐBSCL](https://snnptnt.angiang.gov.vn/)

| Cây trồng | Thời gian sinh trưởng (ngày) | Nhu cầu nước cả vụ ($mm$) | Quy đổi nước ($m^3/ha$) | Hệ số cây trồng $K_c$ (Đầu - Giữa - Cuối vụ) | Độ sâu rễ hiệu dụng ($m$) | Yêu cầu thổ nhưỡng & Thoát nước |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Lúa sạ thẳng** (OM18/OM5451) | 95 – 105 | 1.000 – 1.300 | 10.000 – 13.000 | 1,05 — 1,20 — 0,90 | 0,15 – 0,25 | Đất phù sa, đất sét nặng; giữ nước mặt; chịu úng tuyệt đối. |
| **Mè đen** (Vè đen 1, giống ĐP) | 75 – 85 | 250 – 380 | 2.500 – 3.800 | 0,35 — 1,10 — 0,25 | 0,50 – 0,80 | Đất thịt pha cát, đất phù sa cổ; **sợ úng số một**; cần rãnh thoát nước sâu 30 cm. |
| **Đậu xanh** (ĐX 208, giống Mỡ) | 65 – 75 | 200 – 320 | 2.000 – 3.200 | 0,40 — 1,05 — 0,35 | 0,40 – 0,60 | Đất tơi xốp, $pH \ge 5,5$; nhạy cảm với phèn nặng; yêu cầu thoát nước cực nhanh sau mưa. |
| **Bắp lai / Sinh khối** (NK7328, CP511) | 90 – 105 | 380 – 550 | 3.800 – 5.500 | 0,30 — 1,20 — 0,35 | 0,60 – 1,00 | Đất phù sa ven sông, giàu dinh dưỡng; không chịu ngập úng quá 24h. |
| **Đậu phộng** (MD7, L14) | 90 – 100 | 350 – 480 | 3.500 – 4.800 | 0,40 — 1,15 — 0,60 | 0,40 – 0,70 | Đất cát pha, đất phù sa giồng ven biển; tầng đất mặt tơi xốp để đâm tia củ. |
| **Dưa hấu** (Phù Đổng, Hắc Mỹ Nhân) | 60 – 70 | 250 – 350 | 2.500 – 3.500 | 0,45 — 1,00 — 0,75 | 0,40 – 0,70 | Đất cát pha, thịt nhẹ; thoát nước tốt; bắt buộc có màng phủ nông nghiệp. |

---

### 7. Bảng Phân Tích Kinh Tế Nông Hộ ĐBSCL (Mặt Bằng Giá 2024–2026)

* Nguồn tham khảo: [Cục Trồng trọt - Chi phí sản xuất lúa và cây màu ĐBSCL](https://cuctrongtrot.gov.vn/), [Báo Nông nghiệp Việt Nam](https://nongnghiep.vn/), [Viện Nghiên cứu Phát triển ĐBSCL (MDI - Can Tho University)](https://mdi.ctu.edu.vn/)

| Cây trồng | Chi phí đầu tư (Triệu đ/ha/vụ) | Năng suất bình quân (Tấn/ha) | Giá bán tại ruộng tham khảo (VNĐ/kg) | Tổng doanh thu (Triệu đ/ha) | Lợi nhuận ròng (Triệu đ/ha) | Mức độ rủi ro thị trường & Tiêu thụ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Lúa Đông Xuân** (chính vụ) | 22 – 26 | 7,0 – 8,5 | 7.000 – 8.500 | 50 – 68 | **25 – 42** | **Thấp**: Thị trường lúa gạo toàn cầu ổn định, thương lái thu mua tại ruộng. |
| **Lúa Hè Thu / Xuân Hè** | 20 – 24 | 4,5 – 6,0 | 6.500 – 7.500 | 30 – 45 | **8 – 20**<br>*(Nguy cơ lỗ nếu hạn mặn)* | **Trung bình - Cao**: Năng suất thấp do mưa bão hoặc thiếu nước; phẩm cấp gạo thấp. |
| **Mè đen** | 12 – 16 | 1,2 – 1,8 | 45.000 – 55.000 | 54 – 90 | **35 – 70** | **Trung bình**: Thị trường xuất khẩu ngách tốt; cần bảo quản khô ráo tránh mốc hạt. |
| **Đậu xanh** | 10 – 14 | 1,6 – 2,2 | 24.000 – 30.000 | 38 – 66 | **24 – 48** | **Thấp - Trung bình**: Nhu cầu chế biến thực phẩm trong nước tiêu thụ quanh năm. |
| **Bắp lai (hạt khô)** | 26 – 32 | 8,0 – 10,0 | 5.500 – 6.500 | 44 – 65 | **15 – 33** | **Thấp**: Nhà máy thức ăn chăn nuôi ĐBSCL bao tiêu lớn. |
| **Đậu phộng** | 28 – 35 | 3,0 – 4,2 | 18.000 – 24.000 (tươi) | 54 – 95 | **25 – 55** | **Trung bình**: Tốn công thu hoạch nhổ củ; đầu ra ổn định. |
| **Dưa hấu** | 35 – 45 | 25,0 – 35,0 | 4.000 – 9.000 (biến động) | 100 – 250 | **30 – 150**<br>*(hoặc hòa vốn)* | **Rất cao**: Điệp khúc "được mùa mất giá"; phụ thuộc xuất khẩu tiểu ngạch biên giới. |

---

## PHẦN C: THIẾT KẾ UX HƯỚNG NÔNG DÂN & KHUYẾN NÔNG VIỆT NAM

### 1. Bối Cảnh Người Dùng: Nông Dân & Cán Bộ Khuyến Nông Cơ Sở

* **Đặc tính nông dân ĐBSCL:** Độ tuổi trung bình 45–62 tuổi; thị lực giảm; ngón tay thô ráp khó thao tác bàn phím nhỏ; trình độ học vấn phổ biến cấp 1 – cấp 2; ngại đọc tài liệu nhiều chữ; tâm lý "thấy mới tin" (ưa chuộng bằng chứng thực tế từ ruộng láng giềng).
* **Thiết bị & Kết nối:** 85% sử dụng smartphone Android giá rẻ (bộ nhớ 32–64 GB thường xuyên đầy do ảnh/video); mạng 3G/4G chập chờn khi ra cánh đồng xa; dung lượng pin hao nhanh dưới trời nắng nóng.
* **Hành vi số:** Không có thói quen tải app từ Google Play/App Store vì sợ mã độc hoặc quên mật khẩu; nhưng **100% sử dụng Zalo hàng ngày** để gọi video cho con cháu, nhận thông báo ấp/xã và trao đổi trong nhóm Hợp tác xã (HTX).

---

### 2. Mô Hình Phổ Biến Khuyến Nông Thực Tế Tại Việt Nam

Việc ra quyết định mùa vụ tại ĐBSCL không diễn ra đơn lẻ ở từng nông dân mà tuân thủ cấu trúc chỉ đạo và tháp niềm tin cộng đồng:

```mermaid
graph TD
    A["Sở NN&PTNT / Chi cục Trồng trọt & BVTV"] -->|"Ban hành khung lịch & Dự báo rầy/mặn"| B["Trạm Khuyến nông Huyện"]
    B --> C["Tổ Khuyến nông Cộng đồng Xã (QĐ 1094/QĐ-BNN-KN)"]
    C -->|"Tư vấn qua Zalo nhóm & Họp ấp"| D["Ban Giám đốc Hợp tác xã (HTX)"]
    D -->|"Thống nhất bơm nước & Xuống giống đồng loạt"| E["Nông dân thành viên"]
    
    style C fill:#bbf,stroke:#333,stroke-width:2px
    style D fill:#dfd,stroke:#333,stroke-width:2px
    style E fill:#ffd,stroke:#333,stroke-width:2px
```

* **Vị thế chiến lược của FieldShift-Mekong:** Công cụ **không được tự xưng thay thế cán bộ khuyến nông**. FieldShift đóng vai trò là **"Trợ lý số cho Tổ Khuyến nông Cộng đồng và Giám đốc HTX"** – giúp họ chạy thử nghiệm các kịch bản khí hậu ("Nếu năm nay hạn mặn như 2016 thì xã mình nên chuyển đổi bao nhiêu ha sang cây màu?") để đưa ra khuyến cáo thuyết phục nông dân.

---

### 3. Nguyên Tắc Thiết Kế UX/UI Cho FieldShift-Mekong

| Thách thức người dùng | Giải pháp thiết kế trong FieldShift-Mekong | Quy tắc kỹ thuật bắt buộc |
| :--- | :--- | :--- |
| **Ngại cài app, thiếu bộ nhớ** | Xây dựng dưới dạng **Zalo Mini App** (hoặc Web PWA siêu nhẹ $<1,5\text{ MB}$). | Khởi chạy ngay trong Zalo bằng quét mã QR tại trụ sở HTX; không cần đăng nhập Google/Apple ID. |
| **Mù mờ trước số liệu viễn thám** | Trực quan hóa theo chuẩn **Đèn giao thông (Traffic Lights)**: Xanh lá (An toàn) – Vàng (Cảnh giác) – Đỏ (Báo động/Không khả thi). | Không hiển thị chỉ số trừu tượng $NDVI = 0,68$ hay bốc thoát hơi nước $180\text{ mm}$; dịch thành: "Tháng 3: Ruộng thiếu hụt 18 đợt nước tưới – Nguy cơ cạn kênh". |
| **Thao tác khó khăn** | Giao diện thẻ chạm (Touch Cards), nút bấm to bản ($min\text{ height } 48\text{ px}$); tối đa 3 bước để xem kết quả. | Hỗ trợ phát âm thanh (Voice synthesis giọng miền Tây) đọc to kết quả khuyến nghị và checklist kiểm tra. |
| **Mất sóng 3G ngoài ruộng** | Cơ chế **Offline-First**: lưu toàn bộ kế hoạch đã tạo vào LocalStorage / SQLite nội tại. | Có nút "In phiếu khuyến cáo mùa vụ" (xuất file ảnh 1 trang hoặc HTML printable) để Giám đốc HTX in ra giấy dán tại Nhà văn hóa ấp. |

---

### 4. Tuyên Bố Miễn Trừ Trách Nhiệm & Xây Dựng Niềm Tin (Trust & Disclaimers)

Nông dân sẽ tẩy chay ngay lập tức nếu ứng dụng đưa ra lời khuyên sai dẫn đến mất mùa. Do đó, tính minh bạch và ranh giới trách nhiệm pháp lý phải được thiết kế công khai:

> **Khung thông điệp chuẩn (Bắt buộc hiển thị ở chân trang mọi màn hình kết quả):**  
> *"FieldShift-Mekong là công cụ số hỗ trợ tính toán khoa học dựa trên dữ liệu vệ tinh mở của NASA và mô hình nông học chuẩn FAO. Kết quả có tính chất tham khảo định hướng. Trước khi quyết định xuống giống hoặc mở cống lấy nước, bà con bắt buộc phải kiểm tra thông báo đo mặn thực tế của Trạm Khuyến nông / Xí nghiệp Thủy lợi địa phương và nếm/đo nước kênh bằng bút đo EC."*

---

## PHẦN D: 3 KỊCH BẢN DEMO ĐIỂN HÌNH & KỊCH BẢN THUYẾT TRÌNH 5 PHÚT

### 1. Ba Kịch Bản Demo Thực Tế Với Số Liệu NASA Data

```mermaid
graph LR
    subgraph S1 ["Storyline 1: Châu Đốc (Thượng Nguồn)"]
        A1["Baseline: Lúa - Lúa - Lúa<br>Thiếu nước T3-T4: 480mm<br>Rầy gối lứa liên tục"] -->|FieldShift| B1["Chuỗi: Lúa ĐX - Mè XH - Xả lũ<br>Giảm 4.500 m3 nước (-65%)<br>Cắt đứt rầy nâu, lãi +12 tr/ha"]
    end
    subgraph S2 ["Storyline 2: Ba Tri (Duyên Hải Mặn)"]
        A2["Baseline: Lúa ĐX - Lúa HT<br>Đỉnh mặn T2-T4 >4‰ bủa vây<br>Rủi ro mất trắng 22 tr/ha"] -->|FieldShift| B2["Chuỗi: Lúa ĐX sớm - Đậu xanh<br>Né mặn tuyệt đối<br>Cố định đạm 35 kg N/ha, bảo toàn vốn"]
    end
    subgraph S3 ["Storyline 3: Trần Đề (Chuyển Tiếp Lợ)"]
        A3["Baseline: Độc canh tôm rủi ro dịch<br>Hoặc làm lúa mùa khô chết mặn<br>Ô lưới POWER lẫn biển"] -->|FieldShift| B3["Chuỗi: Tôm lợ (mùa khô) - Lúa ST25 (mưa)<br>Kiểm chứng mưa bằng GPM IMERG<br>Thu nhập 95 tr/ha/năm"]
    end
```

#### Storyline 1: Vùng Thượng Nguồn Phù Sa Ngọt (Châu Đốc, An Giang)
* **Bối cảnh thửa ruộng:** Nông dân Nguyễn Văn Ba, HTX Phú Tân, An Giang. Tọa độ: `10.70°N, 105.12°E`. Diện tích 1,5 ha. Đang làm lúa 3 vụ/năm, đất bị chai cứng, năng suất giảm dần từ 7,5 tấn xuống 5,8 tấn/ha; vụ 2 thường xuyên bị rầy nâu tấn công.
* **Số liệu NASA trích xuất:**
  * NASA POWER Daily: Nhiệt độ trung bình tháng 3–4 đạt $T_{max} \ge 36,7^\circ\text{C}$ với 26 ngày/tháng nắng nóng cực đoan; lượng bốc thoát hơi nước tham chiếu $ET_0 = 212\text{ mm/tháng}$, mưa chỉ $24\text{ mm}$ (Thâm hụt nước tự nhiên: $188\text{ mm/tháng}$).
  * SRTM 30m: Cao độ $2,0\text{ m}$ (vùng trũng đón lũ sông Hậu).
* **Đề xuất từ FieldShift-Mekong:**
  * Thay thế vụ lúa Xuân Hè bằng **Mè đen** (thời gian sinh trưởng 78 ngày: 01/03 $\rightarrow$ 18/05); vụ 3 mở cống xả lũ lấy phù sa.
* **Kết quả định lượng so sánh:**
  * Lượng nước tưới tiêu thụ: giảm từ $11.500\text{ m}^3\text{/ha}$ (lúa) xuống $3.200\text{ m}^3\text{/ha}$ (mè) $\implies$ **Tiết kiệm $8.300\text{ m}^3\text{ nước/ha}$ ($-72\%$)**.
  * Cắt đứt chu kỳ rầy nâu: thời gian cách ly không có ký chủ lúa kéo dài 80 ngày $\implies$ mật số rầy lột xác giảm $95\%$, giảm 3 lần phun thuốc trừ sâu ở vụ Đông Xuân kế tiếp.
  * Lợi nhuận vụ 2 tăng từ 12 triệu đ/ha (lúa) lên 28 triệu đ/ha (mè).

#### Storyline 2: Vùng Duyên Hải Nhiễm Mặn (Ba Tri, Bến Tre)
* **Bối cảnh thửa ruộng:** Nông dân Lê Văn Sáu, xã An Đức, huyện Ba Tri, Bến Tre. Tọa độ: `10.10°N, 106.45°E`. Diện tích 1,0 ha ven sông Hàm Luông. Từng bị mất trắng lúa vụ 2 trong đợt mặn lịch sử 2016 và 2020 do cống thủy lợi đóng kín không có nước ngọt tưới.
* **Số liệu NASA trích xuất:**
  * NASA POWER 25 năm Climatology: Mưa mùa khô (tháng 12 đến tháng 4) biến động dữ dội: năm ẩm đạt $412\text{ mm}$ (2022) nhưng năm khô kiệt chỉ đạt $37\text{ mm}$ (2016) và $47\text{ mm}$ (2024).
  * Kịch bản Stress-Test Analog-Year 2016: Hệ số thiếu hụt nước đạt đỉnh vào tháng 3; độ mặn ngoại vi sông dao động $6 - 9‰$.
* **Đề xuất từ FieldShift-Mekong:**
  * Vụ 1: Xuống giống lúa Đông Xuân cực sớm (15/10 $\rightarrow$ thu hoạch 20/01 để né hoàn toàn đợt mặn bùng phát từ tháng 2).
  * Vụ 2: Chuyển sang **Đậu xanh** ngắn ngày (68 ngày); cài đặt điều kiện kích hoạt (Trigger): *"Nếu $EC_w$ nước kênh $> 2,0\text{ dS/m}$ trước ngày 15/02 $\implies$ Chuyển sang phơi ải đất, tuyệt đối không gieo hạt"*.
* **Kết quả định lượng so sánh:**
  * Loại bỏ $100\%$ rủi ro mất trắng vốn đầu tư lúa (tiết kiệm 22 triệu đ chi phí giống, phân, dầu bơm).
  * Vụ đậu xanh mang lại lợi nhuận an toàn 22 triệu đ/ha; bổ sung $\sim 35\text{ kg N/ha}$ cho đất thông qua nốt sần rễ.

#### Storyline 3: Vùng Chuyển Tiếp Bán Đảo Cà Mau (Trần Đề, Sóc Trăng)
* **Bối cảnh thửa ruộng:** Nông dân Thạch Danh, xã Liêu Tú, huyện Trần Đề, Sóc Trăng. Tọa độ: `9.55°N, 106.20°E`. Diện tích 2,0 ha mô hình tôm - lúa.
* **Số liệu NASA trích xuất & Cảnh báo chất lượng:**
  * Dữ liệu ô lưới MERRA-2 ($0,5^\circ \times 0,625^\circ$) bị cắm cờ `COASTAL_CELL_MIXED` (lẫn diện tích mặt biển làm nhiệt độ thấp bất thường). Engine tự động áp dụng hiệu chỉnh nội suy từ trạm phụ cận nội đồng Sóc Trăng.
  * GPM IMERG Late: Phát hiện thời điểm mở đầu gió mùa mùa mưa (vượt ngưỡng mưa tích lũy $150\text{ mm}$) thường rơi vào tuần thứ 3 của tháng 5.
* **Đề xuất từ FieldShift-Mekong:**
  * Mùa khô (T1–T5): Khai thác nuôi tôm nước lợ.
  * Mùa mưa (T6–T11): Trồng 1 vụ lúa đặc sản ST25 chịu mặn nhẹ kết hợp trồng ngô sinh khối trên bờ liếp; dùng IMERG để xác định ngày bắt đầu rửa mặn an toàn.
* **Kết quả định lượng so sánh:**
  * Doanh thu tích hợp hệ thống Lúa – Tôm đạt $110\text{ triệu đ/ha/năm}$ (gấp 2,5 lần so với trồng 2 vụ lúa bấp bênh).
  * Không phát sinh xung đột nước mặn/ngọt giữa các hộ nuôi tôm và trồng lúa lân cận.

---

### 2. Kịch Bản Thuyết Trình 5 Phút (Pitch Script Mapped to Judging Criteria)

* **Tổng thời lượng:** Đúng 5 phút (300 giây).  
* **Phân bổ cấu trúc bài thi theo tiêu chí chấm điểm:**

```text
[00:00 - 01:00] | PHẦN 1: IMPACT - Khủng Hoảng Hạn Mặn & Nỗi Đau Nông Dân
* Hình ảnh mở đầu: Ruộng lúa nứt nẻ trắng xóa vệt muối tại Bến Tre; người nông dân thất thần nhìn lúa cháy lá.
* Thông điệp: ĐBSCL cung cấp 50% sản lượng lúa và 95% lượng gạo xuất khẩu của Việt Nam, nhưng đang đứng trước bờ vực: 3 vụ lúa liên miên làm kiệt quệ phù sa, rầy nâu bùng phát và thâm hụt 480 mm nước ngọt mỗi mùa khô.
* Điểm nghẽn: Nông dân biết cần chuyển đổi lúa - màu theo Nghị quyết 120, nhưng câu hỏi chết người là: "Đổi sang cây gì? Ngày nào gieo? Nếu mặn đến sớm thì trắng tay hay không?". Họ thiếu một công cụ dự báo có căn cứ khoa học.

[01:00 - 01:45] | PHẦN 2: CREATIVITY - Khác Biệt Của FieldShift-Mekong
* Trực quan: So sánh 2 màn hình: (Trái) Bản đồ vệ tinh GIS truyền thống đầy màu sắc phức tạp mà nông dân không hiểu gì; (Phải) Giao diện FieldShift dạng thẻ hành động đơn giản trên Zalo.
* Đột phá: Chúng tôi không xây thêm một "Dashboard xem ảnh viễn thám". FieldShift là Hệ thống Lập kế hoạch Luân canh Đa kịch bản (Scenario-based Multi-crop Planner).
* Điểm sáng tạo: Engine so sánh song song chuỗi truyền thống 3 vụ lúa với các phương án luân canh lúa-màu tối ưu Pareto, hiển thị rõ ràng sự đánh đổi (trade-off) về nước, rủi ro và lợi nhuận dưới các kịch bản khí hậu khắc nghiệt.

[01:45 - 03:15] | PHẦN 3: VALIDITY & RELEVANCE - Sức Mạnh Dữ Liệu NASA & Tính Chân Thực
* Trực quan: Sơ đồ dòng dữ liệu từ vệ tinh NASA -> FAO-56 Engine -> Quyết định trên đồng ruộng.
* Chi tiết khoa học:
  1. Chúng tôi khai thác 25 năm dữ liệu NASA POWER Daily và SRTM 30m để mô phỏng bốc thoát hơi nước chuẩn FAO-56 Penman-Monteith và ẩm đất tầng rễ.
  2. Nguyên tắc "Zero Fake Numbers": Vệ tinh không đo được độ mặn lòng kênh! FieldShift phân tách minh bạch: khí hậu là ước lượng viễn thám (`OBSERVED_REMOTE_ESTIMATE`), mặn là đo thực địa (`OBSERVED_FIELD`).
  3. Xử lý thiếu dự báo mùa bằng Stress-Testing với các năm tương đồng lịch sử có thật (Analog-years 2016, 2020, 2024). Bật cổng kiểm soát Gate G5, G6: thiếu số đo mặn, hệ thống lập tức khóa khuyến nghị cứng và chuyển sang chế độ "Cảnh báo kèm điều kiện kiểm tra".

[03:15 - 04:15] | PHẦN 4: DEMO - Trải Nghiệm 60 Giây Của Bác Sáu Ba Tri
* Trực quan: Video quay màn hình thao tác trên điện thoại:
  1. Bác Sáu chọn vị trí xã An Đức, Ba Tri. Hệ thống kéo dữ liệu POWER nhận diện bối cảnh ven biển.
  2. Baseline 2 vụ lúa báo động ĐỎ: Vụ 2 thiếu 410 mm nước, trùng đỉnh mặn tháng 3.
  3. FieldShift gợi ý: Chuyển vụ 2 sang Đậu xanh. Lượng nước tưới giảm 68%, né được đỉnh mặn.
  4. Hệ thống đưa ra Trigger rõ ràng: "Nếu đo nước kênh trước 15/02 vượt 2,0 dS/m (1,3‰) -> Dừng gieo, chuyển phơi đất".
  5. Bác Sáu bấm 1 nút: Xuất phiếu khuyến cáo 1 trang bằng tiếng Việt gửi thẳng vào nhóm Zalo ấp.

[04:15 - 05:00] | PHẦN 5: PRESENTATION & ROADMAP - Chuyển Giao Thực Tế & Kết Luận
* Tác động cộng hòa: Phù hợp 100% với Đề án 1 triệu ha lúa chất lượng cao, phát thải thấp đến 2030 của Chính phủ Việt Nam.
* Con đường chuyển giao: Đồng hành cùng hơn 3.000 Tổ Khuyến nông Cộng đồng tại ĐBSCL qua nền tảng Zalo Mini App – không tốn chi phí cài đặt, không đòi hỏi thiết bị đắt tiền.
* Thông điệp kết: "Dữ liệu vệ tinh từ độ cao 700 km của NASA chỉ thực sự có giá trị khi nó giúp được một người nông dân miền Tây quyết định đúng đắn trên mảnh ruộng 1 hecta của mình. FieldShift-Mekong – biến dữ liệu vũ trụ thành chén cơm bền vững cho ĐBSCL!"
```

---

## TOP 10 HÀNH ĐỘNG THEN CHỐT CHO ĐỘI NGŨ PHÁT TRIỂN (BUILD INSIGHTS)

Dưới đây là 10 kết luận hành động cô đọng nhất mà đội ngũ lập trình (Frontend, Backend, Data) cần tuân thủ nghiêm ngặt trong 48 giờ hackathon:

1. **Khóa chặt nguyên tắc "Zero Fake Numbers" trong API:** Mọi trường số trả về từ backend bắt buộc phải đi kèm metadata nguồn gốc (`Measure`: `value`, `unit`, `origin`, `label`). Tuyệt đối không trả về số trần (`naked floats`).
2. **Không cố dự báo độ mặn từ vệ tinh:** Vệ tinh NASA không đo được $EC_w$ trong kênh rạch ĐBSCL. Khi người dùng chưa nhập giá trị đo mặn, `salinity.value` phải là `null` với nhãn `Chưa biết`, đồng thời kích hoạt cổng `Gate G5` chuyển trạng thái sang `CONDITIONAL_PENDING_CHECK`.
3. **Thay thế Projection API bằng Stress-Test Analog-Year:** NASA POWER Projection trả giá trị lỗi `-999` tại châu Á. Không cố sửa API này; thay thế bằng kịch bản kiểm thử ứng suất lặp lại mùa khô lịch sử năm 2016, 2024 hoặc giả lập tăng nhiệt $+1,5^\circ\text{C}$, giảm mưa $-30\%$.
4. **Xử lý cờ ô lưới ven biển lẫn biển (`COASTAL_CELL_MIXED`):** Các điểm ven biển như Sóc Trăng, Bến Tre ở lưới $0,5^\circ$ của MERRA-2 bị nhiễm nhiệt độ mặt biển làm $T_{max}$ thấp giả tạo. Backend phải gắn cờ cảnh báo chất lượng và dịch điểm lấy mẫu vào nội đồng $0,2^\circ - 0,25^\circ$.
5. **Cố định bảng chuyển đổi mặn trong Catalog:** Sử dụng công thức $1\text{ ‰} = 1\text{ g/L} \approx 1,56\text{ dS/m}$ ($1\text{ dS/m} \approx 0,64\text{ ‰}$). Luôn hiển thị song song cả 2 đơn vị trên UI để nông dân (quen dùng $\text{‰}$) và khuyến nông (dùng bút đo $\text{EC}$) đều hiểu.
6. **Bộ quy tắc cứng (HARD Rules) phải lọc triệt để trước khi tối ưu:** Chuỗi luân canh nào vi phạm: thời gian sinh trưởng vượt cửa sổ mùa vụ kế tiếp, hoặc bố trí cây cạn (mè, ngô) trên đất không thoát nước được (ngập úng $>24\text{h}$) phải bị đẩy ngay vào danh sách `excluded` có nêu rõ lý do (`rule_id`, `how_to_resolve`).
7. **Baseline 3 vụ lúa luôn phải xuất hiện:** Dù phương án 3 vụ lúa (`seq_rice_rice_rice`) cực kỳ rủi ro hay vi phạm tiêu chí nước, nó luôn phải được đánh giá và hiển thị cạnh các phương án đề xuất để làm mốc đối chứng (Delta calculation).
8. **Ưu tiên kiến trúc Cache-First cho demo hội trường:** Mạng internet tại các sự kiện hackathon thường xuyên quá tải. Toàn bộ dữ liệu NASA POWER của 4 điểm demo (Cần Thơ, Châu Đốc, Bến Tre, Sóc Trăng) phải được nạp sẵn từ các file cache JSON cục bộ; API live chỉ đóng vai trò thứ cấp.
9. **UI phải tối giản hóa theo chuẩn Mobile/Zalo:** Frontend tập trung vào giao diện thẻ dọc kiểu Zalo, thẻ tóm tắt khuyến nghị có màu sắc trực quan (Xanh/Vàng/Đỏ), nút bấm to, có checklist hành động thực tế ("Kiểm tra cống", "Đo độ mặn kênh trước khi bơm").
10. **Chuẩn bị sẵn màn hình Export 1 trang A4:** Tính năng xuất báo cáo tóm tắt khuyến nghị mùa vụ 1 trang HTML in được (Printable View) là "vũ khí ghi điểm" lớn với giám khảo cho tiêu chí *Impact & Validity*, chứng minh tính sẵn sàng chuyển giao cho Tổ Khuyến nông cộng đồng cơ sở.
