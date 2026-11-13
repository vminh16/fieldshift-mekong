# FIELD SHIFT: ADAPTING FARMS WITH NASA DATA

## Problem Statement & Domain Analysis

**NASA International Space Apps Challenge 2026**  
**Phiên bản:** 1.0 — ngày 08/11/2026  
**Mục đích:** Định nghĩa toàn diện bài toán, dữ liệu và giá trị cần tạo ra. **Chưa thu hẹp phạm vi; chưa chọn thuật toán, kiến trúc hoặc giải pháp kỹ thuật.**

> **Lưu ý về nguồn:** Phát biểu ngắn của thử thách đã được đối chiếu trên [trang chính thức NASA Space Apps](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/). Phần *Background, Objectives, Potential considerations* được đối chiếu từ [bản trình bày đầy đủ của đơn vị tổ chức địa phương HackAthlone](https://hackathlone.com/challenges/adapting-farms-with-nasa-data), vốn dẫn về trang chính thức và nói rõ trang chính thức là nguồn quyết định cuối cùng. Các gợi ý được viết bằng **“may”, “may consider”** không phải tiêu chí bắt buộc. Ngày 08/11/2026, danh mục **Resources riêng của đề** được thông báo sẽ xuất hiện vào **thứ Sáu 13/11/2026**; không được nhầm danh sách sản phẩm NASA đang công khai với bộ tài nguyên đã được đính kèm chính thức cho thử thách.

---

## 1. Bức tranh lớn: NASA thực sự đặt ra bài toán gì?

### 1.1. Phát biểu đề gốc, diễn đạt lại bằng tiếng Việt

Nông dân đang phải đưa ra quyết định trồng trọt trong điều kiện ngày càng khó lường: nhiệt độ thay đổi, mưa thất thường, thiếu nước, thời tiết cực đoan và chất lượng đất suy giảm. **Lựa chọn thứ tự cây trồng qua các mùa** không đơn giản là tìm cây có năng suất cao nhất ở mùa sắp tới. Một lựa chọn có thể thuận lợi ngắn hạn nhưng làm tăng nhu cầu tưới, gây rủi ro sâu bệnh, làm mất cân bằng đất hoặc không phù hợp với điều kiện địa phương.

**Thử thách:** Tạo một **công cụ hỗ trợ ra quyết định** kết hợp:

1. Dữ liệu quan sát Trái Đất của NASA;
2. Thông tin đất đai tại địa phương;
3. Đặc tính và nhu cầu của các loại cây trồng;
4. Mục tiêu, ưu tiên và giới hạn thực tế của người nông dân;

để giúp người dùng **khám phá, so sánh và hiểu các chiến lược luân canh cây trồng** có tiềm năng bảo vệ sức khỏe đất và tăng khả năng thích ứng trước biến động thời tiết, nguồn nước.

### 1.2. Một câu mô tả cô đọng

> **Với một thửa ruộng có điều kiện đất, khí hậu và nguồn lực cụ thể, người nông dân nên cân nhắc những chuỗi cây trồng nào trong các mùa tới; mỗi lựa chọn có lợi ích, rủi ro và đánh đổi gì; và bằng chứng nào khiến những đánh giá đó đáng tin?**

### 1.3. Vấn đề cốt lõi KHÔNG phải là gì?

- Không chỉ là **dự báo thời tiết**, vì dự báo mưa chưa cho biết nên thay đổi chuỗi mùa vụ như thế nào.
- Không chỉ là **xác định cây phù hợp với một vùng**, vì cây phù hợp cho một mùa chưa chắc phù hợp sau cây vừa thu hoạch.
- Không chỉ là **tối đa hóa năng suất hoặc lợi nhuận**, vì đất, nước, độ bền vững và rủi ro dài hạn cũng quan trọng.
- Không chỉ là **trực quan hóa ảnh vệ tinh**, vì nông dân cần hiểu hệ quả đối với quyết định canh tác.
- Không phải **một chatbot trả lời kiến thức chung**, vì bài toán đòi hỏi so sánh các lựa chọn gắn với thửa ruộng, thời điểm, điều kiện và bằng chứng.
- Cũng không phải “NASA đã tính sẵn cây nào nên trồng”: dữ liệu viễn thám **không trực tiếp chứa câu trả lời luân canh**.

### 1.4. NASA yêu cầu, NASA gợi ý và nhóm tự quyết định

| Mức độ | Nội dung | Cách diễn giải đúng |
|---|---|---|
| **Cốt lõi của đề** | Công cụ hỗ trợ ra quyết định; kết hợp NASA Earth observations với dữ liệu đất/cây/ưu tiên nông dân; giúp khám phá chiến lược luân canh và thích ứng | Đó là bản chất sản phẩm cần chứng minh |
| **Kết quả mong muốn** | Làm rõ tác động tiềm năng đến sức khỏe đất và khả năng chống chịu trước khí hậu, nguồn nước biến động | Công cụ phải phục vụ **quyết định trong đời thực**, không chỉ hiển thị thông tin |
| **NASA gợi ý, không bắt buộc** | So sánh ít nhất ba chuỗi, gồm chuỗi hiện tại; giải thích bằng chứng, lợi ích, khoảng trống dữ liệu, rủi ro | Một cấu trúc so sánh rất hợp lý, nhưng không được diễn đạt là quy định cứng |
| **NASA gợi ý, không bắt buộc** | Bản đồ tương tác, theo dõi biến đổi theo thời gian, thanh thử kịch bản, phân tích với các nguồn NASA cụ thể | Những cách biểu đạt và khai thác dữ liệu có thể lựa chọn |
| **Nhóm tự quyết định** | Địa bàn, loại cây, số mùa vụ, người dùng trọng tâm, mô hình đánh giá, cách xếp hạng, giao diện | Đây là quyết định sản phẩm/nghiên cứu, không phải nội dung NASA áp đặt |

Nguồn: [NASA Space Apps 2026 — Field Shift](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/); [HackAthlone — mục Objectives và Potential considerations](https://hackathlone.com/challenges/adapting-farms-with-nasa-data).

---

## 2. Luân canh là gì và tại sao nó khó?

### 2.1. Khái niệm

**Luân canh cây trồng (crop rotation)** là việc bố trí **các loại cây hoặc nhóm cây khác nhau nối tiếp nhau trên cùng một diện tích đất qua các mùa vụ hoặc năm** nhằm đạt các mục tiêu nông học và kinh tế. Đối tượng cần xem xét là **cả chuỗi qua thời gian**, không chỉ một cây riêng lẻ.

Ví dụ minh họa, **không phải khuyến nghị nông học**:

| Chuỗi | Mùa 1 | Mùa 2 | Mùa 3 | Câu hỏi cần đánh giá |
|---|---|---|---|---|
| A — duy trì hiện trạng | Lúa | Lúa | Lúa | Có phụ thuộc quá nhiều vào nước? Tác động dài hạn đến đất/sâu bệnh? |
| B — thay đổi một mùa | Lúa | Ngô | Lúa | Ngô có phù hợp lịch mùa, đất, tưới, sâu bệnh, thị trường tại ruộng? |
| C — bổ sung cây họ đậu | Lúa | Đậu xanh | Lúa | Cây họ đậu có trồng được tại đây và đóng góp gì cho hệ thống canh tác? |

Ba chuỗi trên chỉ có ý nghĩa sau khi kiểm tra **mùa vụ, đất, nước, giống, sâu bệnh, độ mặn, điều kiện thị trường** cụ thể. Không thể mặc định phương án C tốt hơn A.

Các thuật ngữ dễ nhầm:

- **Độc canh (monoculture):** trồng một loại cây trên một diện tích; việc liên tục trồng cùng cây qua các mùa là trường hợp chuỗi kém đa dạng.
- **Luân canh (crop rotation):** thay đổi cây **theo thời gian** trên cùng đất.
- **Xen canh (intercropping):** trồng **đồng thời** nhiều cây trên cùng diện tích.
- **Cây che phủ (cover crop):** cây trồng chủ yếu để che phủ, bảo vệ hoặc hỗ trợ đất; không nhất thiết để thu hoạch thương phẩm.
- **Đất nghỉ (fallow):** giai đoạn không trồng cây thương phẩm; có thể để đất trống hoặc được quản lý theo cách khác.
- **Sức khỏe đất (soil health):** năng lực của đất duy trì các chức năng sinh học, hóa học, vật lý cần cho hệ sinh thái và sản xuất; **không thể đồng nhất với một chỉ số NDVI hay độ ẩm duy nhất**.
- **Khả năng chống chịu (resilience):** khả năng hệ thống canh tác chịu đựng, thích ứng và phục hồi trước biến động, không đồng nghĩa với năng suất cao trong một mùa thuận lợi.

FAO nhấn mạnh đa dạng hóa cây trồng có thể đóng góp cho chu trình dinh dưỡng, cấu trúc đất và quản lý dịch hại, nhưng thiết kế luân canh cần theo mục tiêu và bối cảnh. Nguồn: [FAO — Species diversification](https://www.fao.org/conservation-agriculture/in-practice/species-diversification/en/); [FAO — Cover crop species](https://www.fao.org/family-farming/detail/en/c/1619115/).

### 2.2. Vì sao không thể chọn từng mùa một cách độc lập?

Một quyết định ở mùa này **thay đổi điều kiện đầu vào của mùa sau**:

1. **Đất:** cây trồng, tàn dư thực vật, tưới và quản lý dinh dưỡng có thể ảnh hưởng chất hữu cơ, độ che phủ và tình trạng đất về sau.
2. **Nước:** nhu cầu nước hiện tại ảnh hưởng chi phí, mức phụ thuộc tưới và sức chịu đựng khi mùa tiếp theo khô hạn.
3. **Sâu bệnh/cỏ dại:** chuỗi cây liên quan đến vòng đời và áp lực dịch hại; hiệu quả phụ thuộc đối tượng dịch hại cụ thể.
4. **Lịch mùa vụ:** thu hoạch muộn có thể khiến cây kế tiếp không còn đủ cửa sổ thời gian để trồng.
5. **Kinh tế và vận hành:** doanh thu của vụ trước, thiết bị, lao động, đầu ra thị trường và chi phí chuyển đổi ảnh hưởng khả năng thực hiện vụ sau.
6. **Rủi ro khí hậu:** thời tiết tương lai không cố định; phương án tốt ở điều kiện trung bình có thể không còn tốt khi hạn hoặc mưa cực đoan xảy ra.

Do đó, đối tượng đánh giá là **chiến lược canh tác theo chuỗi thời gian**, có điều kiện và có đánh đổi, không chỉ là xếp hạng các cây trồng riêng lẻ.

### 2.3. Hai tầng thời gian luôn cùng tồn tại

| Tầng thời gian | Người dùng cần hiểu | Vai trò |
|---|---|---|
| **Quá khứ** | Nhiều năm qua mưa, nóng, thiếu nước, thảm thực vật thay đổi thế nào? Lịch sử ruộng ra sao? | Nhận diện bối cảnh, xu hướng, mùa vụ bất thường, rủi ro đã xảy ra |
| **Hiện tại** | Đất, nước, lịch canh tác, khả năng đầu tư và ràng buộc cụ thể ra sao? | Xác định điều kiện có thật và những phương án không khả thi |
| **Tương lai** | Nếu những mùa tới nóng/khô/ẩm hơn, các chuỗi sẽ có ưu nhược điểm gì? | Khám phá lựa chọn có điều kiện; **không giả định biết chắc tương lai** |

---

## 3. Ai cần công cụ này và đau ở đâu?

| Người liên quan | Pain point | Quyết định họ cần đưa ra |
|---|---|---|
| **Nông dân / hộ canh tác** | Khó biết khi nào nên đổi cây; rủi ro mất thu nhập nếu thử sai; thiếu khả năng tự đọc dữ liệu vệ tinh | Giữ chuỗi hiện tại, thay một mùa, bổ sung cây họ đậu/che phủ hay thay đổi lịch trồng? |
| **Hợp tác xã / người điều phối sản xuất** | Nhiều thửa có đất, nguồn tưới, điều kiện thị trường khác nhau; khuyến nghị đồng loạt có thể sai | Thửa nào cần xem xét trước; điều kiện nào khiến chiến lược khác nhau? |
| **Cán bộ khuyến nông / chuyên gia địa phương** | Kinh nghiệm thực địa có giá trị nhưng khó kết hợp có hệ thống với xu thế khí hậu dài hạn | Phương án nào đáng xem xét/kiểm tra; thông tin nào cần lấy mẫu hoặc xác minh tại ruộng? |
| **Nhà nghiên cứu / quản lý tài nguyên** | Dữ liệu khí hậu, đất, sinh trưởng và hành vi nông dân phân tán; khác thang đo | Xu thế rủi ro nào nổi lên; còn thiếu bằng chứng nào trước khi mở rộng áp dụng? |

### 3.1. Pain point số một: khoảng cách giữa dữ liệu và quyết định

NASA có thể cho biết một khu vực có xu hướng khô hơn, nóng hơn hoặc có biến động độ ẩm; một cơ sở dữ liệu đất có thể ước tính pH và chất hữu cơ; chuyên gia có thể biết yêu cầu của cây trồng. **Nhưng người nông dân vẫn cần câu trả lời thực dụng:**

> “Tôi đang trồng chuỗi này. Với đất và nguồn tưới của tôi, tôi có thể đổi sang những chuỗi nào? Đổi như vậy được gì, mất gì, rủi ro gì và tôi phải xác minh điều gì trước khi quyết định?”

Khó khăn không chỉ là thiếu dữ liệu, mà là **thiếu cầu nối đáng tin cậy từ dữ liệu đa nguồn sang việc so sánh các phương án có thể thực hiện**.

### 3.2. Những mâu thuẫn người dùng thực sự gặp

- **Tiền ngay** so với **độ bền sức khỏe đất** nhiều mùa sau.
- **Giữ cách canh tác quen thuộc** so với **thử cây mới** có rủi ro thị trường và kỹ thuật.
- **Tối ưu một chỉ tiêu** (nước, thu nhập, độ che phủ) so với **cân bằng nhiều chỉ tiêu**.
- **Dữ liệu khí hậu quy mô vùng** so với **điều kiện một thửa nhỏ**.
- **Khuyến nghị chung** so với **khả năng làm thật** với nguồn tưới, máy móc, lao động, vốn và lịch mùa.
- **Muốn quyết định dứt khoát** so với **thực tế tồn tại bất định và thiếu thông tin**.

### 3.3. Phạm vi toàn cầu của đề — không giới hạn ở ruộng lúa hay Việt Nam

NASA không ràng buộc đề vào một quốc gia, một cây trồng hoặc một kiểu khí hậu. Những tình huống sau đều nằm trong **miền vấn đề** của Field Shift:

| Hệ thống canh tác | Sức ép nổi bật | Câu hỏi luân canh có thể phát sinh |
|---|---|---|
| Vùng nhiệt đới, lúa nước | Thất thường mùa mưa, thiếu nước mùa khô, ngập, thay đổi lịch vụ | Có nên giữ nhiều vụ lúa, thay một vụ bằng cây cạn, bổ sung giai đoạn che phủ hay nghỉ? |
| Vùng khô/bán khô hạn | Thiếu nước, bốc thoát hơi lớn, đất dễ thoái hóa | Đưa cây chịu hạn, cây có rễ sâu hay cây che phủ vào giai đoạn nào? |
| Vùng ôn đới | Băng giá, sương muối, biến động nhiệt, cửa sổ trồng ngắn | Chuỗi ngũ cốc–cây họ đậu–cây che phủ có trọn lịch mùa và đủ an toàn trước sương giá không? |
| Vùng đất dốc | Mưa lớn, xói mòn, đất trống sau thu hoạch | Khi nào nên bổ sung cây che phủ hay lựa chọn giúp bảo vệ bề mặt đất? |
| Nông trại kết hợp chăn nuôi | Nhu cầu thức ăn gia súc, thu nhập và phục hồi đất | Cây làm thức ăn gia súc có thể tham gia chuỗi thế nào mà không làm tăng rủi ro nước/đất? |

Đây là **các ví dụ về nhu cầu**, không phải những chiến lược đã được NASA xác nhận phù hợp với từng khu vực. Phạm vi đầy đủ còn bao gồm các mục tiêu được đề nhắc đến: **chu trình dinh dưỡng, tiềm năng cố định đạm, chất hữu cơ, kết cấu đất, xói mòn, gián đoạn vòng đời sâu bệnh, khả năng thấm nước, giá trị thức ăn gia súc, sự phù hợp thị trường và thu nhập bổ sung**.

---

## 4. Mô hình bài toán ở mức khái niệm

### 4.1. Bốn nhóm thông tin đầu vào

| Nhóm | Câu hỏi | Ví dụ |
|---|---|---|
| **Không gian & khí hậu** | Thửa ruộng ở đâu, điều kiện mưa/nhiệt/nước đã biến đổi thế nào? | Vị trí, diện tích, lịch sử mưa và nóng, độ ẩm đất, biến động thảm thực vật |
| **Đất & lịch sử ruộng** | Đất có đặc tính gì và đã trồng gì ở các mùa trước? | Kết cấu đất, pH, chất hữu cơ, độ mặn nếu có, cây vụ trước, khả năng tưới/thoát nước |
| **Cây trồng & thực hành** | Những loại cây nào thực sự có thể trồng ở đây và nối tiếp nhau? | Lịch gieo, thời gian sinh trưởng, nhu cầu nước, nhóm thực vật, rễ, tàn dư, dịch hại |
| **Người nông dân** | Họ muốn gì và giới hạn nào là không được vi phạm? | Mức sẵn sàng đổi cây, nguồn vốn, máy móc, lao động, đầu ra, ưu tiên đất/nước/thu nhập |

### 4.2. Câu hỏi trung tâm phải giải quyết

**Từ điều kiện của một thửa ruộng và một số bối cảnh khí hậu có thể xảy ra, có những chuỗi mùa vụ nào đáng cân nhắc; mỗi chuỗi có khả thi không; tác động tiềm năng và những đánh đổi của nó so với hiện trạng là gì?**

Điều này chứa **năm bài toán gắn kết**, không thể bỏ qua khi mô tả phạm vi đầy đủ:

1. **Hiểu bối cảnh:** Nhận diện các sức ép khí hậu, nước, đất và tính đặc thù địa phương.
2. **Hiểu lựa chọn:** Biết những cây và chuỗi nào có thể cân nhắc theo lịch mùa và điều kiện canh tác.
3. **So sánh hệ quả:** Xem xét tác động tiềm năng đối với sức khỏe đất, nước, rủi ro sản xuất, khả năng vận hành và kinh tế.
4. **Phù hợp mục tiêu:** Nhận diện những đánh đổi theo ưu tiên của từng nông dân — không có một “tốt nhất” cho mọi người.
5. **Giải thích và xác minh:** Chỉ ra bằng chứng, giả định, khoảng trống và điều cần chuyên gia/đo đạc thực địa kiểm tra.

### 4.3. Đầu ra mong đợi nếu giải quyết trọn vẹn

Một **bức tranh quyết định có thể kiểm tra được**, bao gồm:

- **Hồ sơ bối cảnh thửa ruộng:** điều kiện đã biết, biến động lịch sử, áp lực khí hậu và nguồn nước.
- **Chuỗi hiện tại làm mốc:** nông dân đang làm gì và điểm rủi ro/điểm mạnh cần chú ý.
- **Tập phương án luân canh có điều kiện:** các chuỗi qua nhiều mùa, có lịch mùa vụ rõ ràng; không bắt buộc chỉ có một đề xuất.
- **So sánh đánh đổi:** nước, đất, che phủ, sâu bệnh, tính khả thi, kinh tế và khả năng chống chịu — với đơn vị/ý nghĩa cụ thể khi đủ dữ liệu.
- **Thử thay đổi điều kiện:** ví dụ mưa ít, nắng nóng, thiếu nước, giá bán thay đổi hoặc nguồn lực bị giới hạn.
- **Giải thích theo bằng chứng:** dữ liệu nào ủng hộ, đâu là giả định hoặc kiến thức nông học, đâu là phần chưa chắc chắn.
- **Danh sách kiểm chứng tại ruộng:** điều cần hỏi chuyên gia, thử nghiệm, đo hoặc bổ sung trước khi áp dụng.

**Không nhất thiết là “một con số reward duy nhất”.** Có thể tồn tại nhiều chuỗi hợp lý, tùy mục tiêu; nếu hiển thị điểm tổng hợp thì cần tránh biến một cách đánh trọng số chủ quan thành chân lý khoa học.

---

## 5. Phân tích toàn bộ các chiều cạnh của vấn đề

| Khía cạnh | Vấn đề thực sự cần hiểu | Điểm dễ sai |
|---|---|---|
| **Khí hậu dài hạn** | Nền khí hậu, xu hướng nhiệt/mưa, mùa vụ cực đoan, mức bất thường | Dùng một năm bất thường để kết luận xu hướng dài hạn |
| **Nguồn nước** | Mưa, khả năng giữ nước của đất, tưới, nguồn nước vùng, nhu cầu cây | Đồng nhất lượng mưa với lượng nước cây có thể sử dụng |
| **Nhiệt và stress thực vật** | Nhiệt không khí, nhiệt bề mặt, bốc thoát hơi, tác động thời điểm sinh trưởng | Nhiệt bề mặt không phải luôn là nhiệt không khí/tình trạng cây tại ruộng |
| **Đất và độ phì** | pH, kết cấu, hữu cơ, dinh dưỡng, độ mặn, khả năng thoát nước | Suy trực tiếp N-P-K, sức khỏe đất từ ảnh vệ tinh hoặc NDVI |
| **Luân canh & sinh học** | Tương tác cây trước–cây sau, cây họ đậu, che phủ, rễ, tàn dư, sâu bệnh | Cho rằng cứ trồng cây họ đậu là chắc chắn tăng năng suất vụ kế |
| **Thời vụ** | Độ dài mùa, cửa sổ gieo/thu hoạch, giai đoạn nhạy cảm với hạn/nóng | Chọn cây “hợp khí hậu” nhưng không kịp lịch trồng |
| **Kinh tế & thị trường** | Chi phí giống, tưới, phân, thu hoạch, giá bán, đầu ra, biến động giá | Chuyển “cây phù hợp” thành “lợi nhuận chắc chắn cao” |
| **Ràng buộc thực tế** | Máy móc, giống, kỹ năng, lao động, hạ tầng tưới, vốn | Đề xuất một chuỗi nông dân không thể thực hiện |
| **Không gian** | Khác biệt giữa vùng khí hậu, ô lưới vệ tinh và thửa ruộng | Khẳng định dữ liệu 9–50 km mô tả chính xác một thửa vài nghìn m² |
| **Bất định & niềm tin** | Chênh lệch giữa đo đạc, ước lượng, kịch bản và tri thức chuyên gia | Trình bày dự báo hoặc giả định dưới dạng sự thật đã quan sát |

### Vấn đề khó nhất về bản chất

Chúng ta có thể **quan sát quá khứ và một phần hiện tại**, nhưng muốn so sánh **những chuỗi chưa được trồng trong tương lai**. Vì thế, hệ thống không thể đơn giản truy xuất “kết quả thật” của mỗi chuỗi. Để đưa ra đánh giá có trách nhiệm, phải phân biệt:

1. **Điều đã được ghi nhận:** ví dụ lượng mưa lịch sử, ảnh thực vật, kết quả xét nghiệm đất.
2. **Điều có cơ sở suy diễn nhưng không quan sát trực tiếp:** ví dụ mức dễ tổn thương của một lựa chọn trong bối cảnh hạn.
3. **Điều còn là giả định/kịch bản:** ví dụ đất sẽ cải thiện bao nhiêu, doanh thu tương lai ra sao nếu đổi cây.

Đây là **điểm phân định giữa một giao diện hấp dẫn và một công cụ khoa học đáng tin**.

---

## 6. NASA có những dữ liệu nào liên quan?

### 6.1. Điều quan trọng trước khi liệt kê

NASA **không đưa sẵn một bảng có cột “ruộng X nên luân canh Y”**. Các sản phẩm liên quan chủ yếu mô tả **khí tượng, nước, nhiệt, thảm thực vật và địa hình**. NASA nêu các họ dữ liệu sau trong phần gợi ý của đề: **SMAP, ECOSTRESS, GPM, Landsat, MODIS, NASA POWER, GRACE/GRACE-FO và SRTM/elevation**; phần gợi ý về kết hợp dữ liệu còn nhắc **GEDI biomass**. Đây là **những nguồn có thể khai thác**, không có nghĩa tất cả đều bắt buộc sử dụng. [Nguồn danh sách: HackAthlone — Objectives/Potential considerations](https://hackathlone.com/challenges/adapting-farms-with-nasa-data).

### 6.2. Bản đồ nguồn dữ liệu NASA

| Nguồn | Nó thực sự cho biết gì? | Khai thác cho câu hỏi luân canh | Giới hạn cần nói rõ |
|---|---|---|---|
| **NASA POWER** | Chuỗi khí tượng/khí hậu: nhiệt độ không khí, mưa, bức xạ, ẩm không khí và các biến liên quan, tùy tham số | Tìm điều kiện sinh trưởng, lịch mùa, biến động nhiều năm, áp lực nhiệt/nước | Là dữ liệu tổng hợp vệ tinh và mô hình/tái phân tích; truy vấn điểm không có nghĩa đo trực tiếp tại thửa; độ phân giải khác nhau theo tham số. [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) |
| **GPM / IMERG** | Ước lượng mưa, có các sản phẩm khoảng **0,1° (xấp xỉ 10 km)** và bước thời gian khác nhau | Mùa khô/mưa, mưa cực đoan, tính bất thường, thời gian thiếu/thừa nước | Ô lưới ~10 km không phải đồng hồ mưa đặt trong ruộng; cần phân biệt sản phẩm Early/Late/Final và độ trễ. [NASA GPM](https://gpm.nasa.gov/data/imerg) |
| **SMAP** | Ước lượng độ ẩm đất; ví dụ sản phẩm Level-4 có độ ẩm mặt và vùng rễ ở **lưới khoảng 9 km** | Rủi ro thiếu ẩm, tính mùa vụ, trạng thái ẩm vùng, hỗ trợ quan sát hạn | Không phải phép đo độ ẩm chính xác ở từng luống; sản phẩm vùng rễ có thành phần mô hình hóa. [NASA SMAP L4](https://data.nasa.gov/dataset/smap-l4-global-3-hourly-9-km-ease-grid-surface-and-root-zone-soil-moisture-analysis-update) |
| **ECOSTRESS** | Nhiệt độ bề mặt, các sản phẩm bốc thoát hơi và stress do bốc thoát hơi; có sản phẩm **~70 m** | Nhận diện vùng nóng, nguy cơ stress nhiệt/nước của thực vật, khác biệt trong thửa lớn | Dữ liệu nhiệt không biến thành nhu cầu tưới chính xác khi thiếu thông tin địa phương; không phải chuỗi đo đồng đều mọi thời điểm. [NASA ECOSTRESS](https://science.nasa.gov/mission/ecostress/) |
| **Landsat / HLS** | Ảnh đa phổ bề mặt; Landsat có các băng phản xạ **30 m**; HLS phối hợp Landsat–Sentinel-2 | Quan sát che phủ, mùa sinh trưởng, thay đổi thảm thực vật, thời kỳ đất trống | Chỉ số thực vật không trực tiếp đo dinh dưỡng đất hoặc xác nhận loại cây nếu chưa được kiểm chứng; ảnh có thể bị mây che. [NASA Landsat 9](https://science.nasa.gov/mission/landsat-9/), [NASA HLS](https://science.nasa.gov/mission/landsat/hls-vegetation-indices/) |
| **MODIS** | Chỉ số xanh thực vật như **NDVI/EVI**; ví dụ MOD13Q1 là **250 m / 16 ngày** | Theo dõi tính mùa vụ và biến động sức sống thảm thực vật qua thời gian dài | Pixel 250 m có thể chứa nhiều thửa và các đối tượng khác; “xanh hơn” không đồng nghĩa đất khỏe hơn. [NASA MODIS](https://modis.gsfc.nasa.gov/data/dataprod/mod13.php) |
| **GRACE / GRACE-FO** | Biến thiên trữ lượng nước trên/trong đất ở **quy mô vùng lớn**, thường tổng hợp theo tháng; sản phẩm có lưới công bố 0,5° | Bối cảnh suy giảm/tăng trữ lượng nước dài hạn, áp lực tài nguyên ở lưu vực/vùng | Không phải đồng hồ đo mực nước giếng hoặc nguồn tưới riêng của một nông trại. [JPL GRACE Tellus](https://grace.jpl.nasa.gov/), [JPL ứng dụng nước](https://grace.jpl.nasa.gov/resources/42/grace-and-grace-fo-track-californias-land-water-changes/) |
| **SRTM / NASADEM** | Độ cao, địa hình; nhiều sản phẩm địa hình có bước lưới **~30 m** | Bối cảnh độ dốc, thoát nước, khả năng dễ tổn thương do xói mòn trong kết hợp với đất/mưa | Độ dốc **không đủ** để suy ra lượng xói mòn cụ thể; dữ liệu địa hình không tự biết rãnh thoát nước do người xây. [NASA Earthdata SRTM](https://search.earthdata.nasa.gov/search?q=SRTMGL1) |
| **GEDI** *(nhắc ở phần gợi ý hợp nhất dữ liệu)* | Dữ liệu cấu trúc thực vật/sinh khối trên một số phạm vi và điều kiện | Bối cảnh sinh khối/che phủ, khi phù hợp với địa điểm và sản phẩm | Không phải nguồn mặc định xác định N-P-K hoặc sinh khối cây hằng năm của mọi thửa; tính thích hợp phải xét riêng. [NASA Earthdata](https://www.earthdata.nasa.gov/) |

**Không phải mọi sản phẩm đều có cùng độ phân giải, chu kỳ, thời kỳ lịch sử, mức sẵn có hoặc cùng ý nghĩa đo lường.** Các con số trên là **ví dụ của sản phẩm cụ thể**, không phải thông số chung cho mọi sản phẩm mang tên sứ mệnh đó.

### 6.3. Dữ liệu nào trả lời câu hỏi nào?

| Câu hỏi | Dữ liệu có ích | Điều **không** thể kết luận chỉ từ dữ liệu đó |
|---|---|---|
| “Ở đây hạn hán/mưa thất thường hơn trước không?” | POWER + GPM + SMAP, đối chiếu chuỗi nhiều năm | Năm tới chắc chắn hạn; ruộng chắc chắn mất mùa |
| “Cây có biểu hiện biến động sinh trưởng theo mùa không?” | Landsat/HLS + MODIS + ECOSTRESS | Chắc chắn do thiếu đạm, nhiễm bệnh hay chỉ do thay loại cây |
| “Khu vực đang chịu sức ép nguồn nước lớn?” | GPM + SMAP + GRACE/GRACE-FO | Lượng nước tưới chính xác mà hộ nông dân sẽ được cấp |
| “Khu vực nào có nguy cơ xói mòn?” | SRTM + mưa + che phủ đất + đất địa phương | Mức mất đất hoặc khả năng thoát nước tại ruộng nếu chưa đánh giá thêm |
| “Thửa này nên luân canh cây gì?” | **Tổng hợp** khí hậu + đất + cây + lịch sử + nguồn lực + ưu tiên | Không thể trả lời có trách nhiệm từ **một lớp vệ tinh** |

---

## 7. Những dữ liệu ngoài NASA mang tính quyết định

**Thiếu các nhóm này, đề tài có nguy cơ trở thành bản đồ khí hậu thay vì công cụ hỗ trợ luân canh.**

| Nhóm dữ liệu | Ví dụ | Vì sao thiết yếu | Tình trạng/nguồn có thể tìm |
|---|---|---|---|
| **Đặc tính đất tại ruộng** | pH, thành phần cát–limon–sét, hữu cơ, N/P/K nếu xét nghiệm, độ mặn, thoát nước | Kiểm tra sự phù hợp thực tế của cây và rủi ro với đất | **Tốt nhất: đo/khảo sát địa phương**; có thể tham khảo bản đồ ước lượng [ISRIC SoilGrids](https://isric.org/explore/soilgrids) — **không phải NASA**, có độ bất định, lưới 250 m |
| **Yêu cầu sinh thái của từng cây** | Dải nhiệt, nước, pH, thời gian sinh trưởng, lịch gieo, nhu cầu đất | Biết cây có tồn tại trong lịch mùa và địa điểm không | Tài liệu khuyến nông, nghiên cứu và bộ dữ liệu cây; [FAO ECOCROP](https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/) là nguồn tham khảo lịch sử, **đã ngừng phát triển khoảng 2015**, không được coi là chuẩn cập nhật duy nhất |
| **Quan hệ giữa các cây trong chuỗi** | Cây họ đậu, che phủ đất, tác động tàn dư, họ cây và sâu bệnh | Hiểu hệ quả theo chuỗi, tránh suy diễn từng cây riêng lẻ | FAO, tài liệu chuyên ngành và chuyên gia nông học địa phương |
| **Lịch sử canh tác thực tế** | Các cây/mùa trước, năng suất ghi nhận, loại phân, tưới, sự cố sâu bệnh | Làm mốc đánh giá hiện trạng và biết điều kiện ban đầu của ruộng | Nhật ký nông hộ/hợp tác xã; **NASA không cung cấp sẵn** |
| **Hạ tầng và nguồn lực** | Tưới, tiêu, loại máy, giống, vốn, lao động, khả năng lưu kho | Loại bỏ lựa chọn không thể thực thi | Hỏi trực tiếp nông dân/địa phương |
| **Kinh tế–thị trường** | Giá bán, chi phí giống, phân, nước, vận chuyển, đầu ra và bất định giá | Đánh giá đánh đổi thu nhập và rủi ro chuyển đổi | Dữ liệu thị trường địa phương, cơ quan thống kê và thông tin hộ |
| **Đánh giá thực địa/chuyên gia** | Mẫu đất, khảo sát ruộng, kiểm tra lịch mùa và bệnh hại | Xác thực giả định và phát hiện tác nhân vệ tinh không quan sát được | Cán bộ khuyến nông, cơ sở nghiên cứu, phòng kiểm nghiệm |

**Phân biệt độ chính xác:** SoilGrids cung cấp **ước lượng có độ bất định** của nhiều tính chất đất (pH, carbon hữu cơ, cấu trúc, N tổng, v.v.), không thay thế xét nghiệm đất ở từng ruộng. [ISRIC SoilGrids](https://isric.org/explore/soilgrids); [tài liệu bất định](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html).

### 7.1. “Có dữ liệu” không đồng nghĩa “biết câu trả lời”

Trong một hệ thống hoàn chỉnh, nên luôn nhận diện ba loại:

- **Quan sát/đo đạc:** ảnh vệ tinh, sản phẩm mưa, xét nghiệm pH, lịch sử gieo trồng do nông dân cung cấp.
- **Ước lượng suy ra:** chỉ số stress, bản đồ độ ẩm đất mô hình hóa, bản đồ thuộc tính đất dạng lưới.
- **Tri thức/giả định/kịch bản:** cây họ đậu có thể hỗ trợ chu trình đạm trong điều kiện phù hợp; giá bán kỳ vọng; diễn biến mùa tương lai.

Một vấn đề khoa học lớn của dự án là **tránh tráo đổi ba tầng bằng chứng này**.

---

## 8. Khoảng trống dữ liệu và những rủi ro khoa học của bài toán

### 8.1. Sai khác về quy mô không gian

Thửa ruộng có thể nhỏ hơn nhiều so với ô dữ liệu GPM, SMAP hoặc GRACE. Một giá trị độ ẩm/khí hậu ở lưới rộng không thể tự động trở thành phép đo chính xác của thửa ruộng. Ngược lại, dữ liệu ảnh 30 m hoặc 70 m dù chi tiết hơn vẫn bị ảnh hưởng bởi mây, góc quan sát, lớp phủ và giới hạn của phép đo.

**Câu hỏi cần giải quyết:** Khi nào dữ liệu chỉ đủ để mô tả **vùng**, và khi nào có cơ sở để mô tả **thửa**?

### 8.2. Sai khác về thời gian

Mưa có thể tính theo nửa giờ/ngày; NDVI có thể là tổng hợp 16 ngày; trữ lượng nước khu vực theo tháng; xét nghiệm đất làm vài lần mỗi năm; quyết định trồng cây lại phụ thuộc đúng **cửa sổ gieo–thu hoạch**.

**Câu hỏi cần giải quyết:** Điều kiện ở thời điểm quyết định có còn tương thích với dữ liệu được quan sát không?

### 8.3. Thiếu dữ liệu trạng thái đất và quản lý

Vệ tinh không trực tiếp cho biết toàn bộ N-P-K tại ruộng, quần thể dịch hại trong đất, số lần bón phân, độ mặn tại tầng rễ, hay tính sẵn có của giống và đầu ra thị trường.

**Câu hỏi cần giải quyết:** Phần kết luận nào có thể dựa vào dữ liệu hiện có, phần nào **phải chờ thông tin từ nông dân hoặc chuyên gia**?

### 8.4. Khó biết nguyên nhân và hệ quả

Một ruộng có NDVI thấp có thể do thiếu nước, thu hoạch, giống khác, bệnh, đất trống theo lịch canh tác hoặc mây/nhiễu ảnh. Một mùa có doanh thu tốt chưa chứng minh chuỗi luân canh đang tối ưu dài hạn.

**Câu hỏi cần giải quyết:** Làm thế nào để không nhầm **tương quan quan sát được** với **tác động do thay đổi luân canh**?

### 8.5. Không biết chắc tương lai

Mục tiêu của đề tài hướng tới các mùa chưa xảy ra. Những kết luận tương lai luôn chịu ảnh hưởng của khí hậu, giá cả, dịch hại và hành vi quản lý mà dữ liệu lịch sử không thể đảm bảo biết trước.

**Câu hỏi cần giải quyết:** Sản phẩm phải diễn đạt **lựa chọn theo điều kiện và mức bất định**, tránh hứa năng suất, lợi nhuận hoặc sức khỏe đất chắc chắn đạt được.

---

## 9. Use case đầy đủ để hình dung vấn đề

### Tình huống giả định: một hộ sản xuất lúa ở đồng bằng sông Cửu Long

> Đây là **tình huống hư cấu để minh họa yêu cầu bài toán**. Không có dữ liệu ruộng, phân tích NASA hay bằng chứng nông học tại địa điểm cụ thể ở đây; mọi phương án đều cần kiểm tra địa phương.

**Bối cảnh:** Hộ nông dân có một thửa đang canh tác lúa nhiều mùa liên tiếp. Họ muốn giữ thu nhập nhưng lo mùa khô tới thiếu nước, chất lượng đất đi xuống và chi phí tưới tăng. Họ chưa biết thay đổi một mùa sang cây khác có đáng thử không.

**Bước 1 — Nông dân mang gì tới?** Vị trí thửa, diện tích, chuỗi vụ trước đây, khả năng tưới, thông tin đất nếu có, các cây họ có thể tiếp cận, và thứ tự ưu tiên (nước/đất/thu nhập).

**Bước 2 — Công cụ cần làm rõ bối cảnh nào?** Mưa, nhiệt và xu hướng thiếu nước trong nhiều năm; mùa nào có nguy cơ bất lợi; ruộng có những hạn chế nào mà ảnh vệ tinh không thể nhìn thấy; độ mặn và lịch mùa có được xác minh chưa.

**Bước 3 — Có thể cân nhắc những lựa chọn nào?**

| Chuỗi mang tính minh họa | Điểm đáng khám phá | Rủi ro và điều **chưa biết** |
|---|---|---|
| **A. Lúa → Lúa → Lúa** | Dễ so với cách làm hiện tại; ít rào cản chuyển đổi | Phụ thuộc vào nguồn nước thế nào? Sức khỏe đất, chi phí và sâu bệnh thay đổi không? |
| **B. Lúa → Ngô → Lúa** | Có thể đa dạng hóa sản phẩm và lịch sử sử dụng đất | Đất, độ mặn, lịch vụ, máy móc, tưới và đầu ra có phù hợp không? |
| **C. Lúa → Đậu xanh → Lúa** | Xem xét cây họ đậu và tính đa dạng chuỗi | Không được mặc định cải tạo đất thành công; cần xem điều kiện ngập/thoát nước, giống, bệnh, đầu ra, quản lý tàn dư |

**Bước 4 — Nông dân thay đổi một giả định:** “Nếu mùa tới khô hơn bình thường?” hoặc “Tôi không thể mua thiết bị mới” hoặc “Tôi ưu tiên không mất thu nhập tối thiểu”. Một số lựa chọn có thể trở nên kém phù hợp hoặc không còn khả thi.

**Bước 5 — Thông tin có trách nhiệm ở đầu ra:** Không chỉ nêu “chọn C”, mà đưa ra **điều kiện để C đáng cân nhắc**, yếu tố làm C rủi ro, bằng chứng đang có, vấn đề chưa đo và **câu hỏi cần đem tới cán bộ khuyến nông**.

**Kết luận use case:** Giá trị của sản phẩm là **giúp quyết định tốt hơn trước khi xuống giống**, kể cả khi kết luận hợp lý nhất là *chưa nên thay đổi cho tới khi kiểm tra được độ mặn, nguồn tưới hoặc đầu ra thị trường*.

---

## 10. Sản phẩm đầu ra đầy đủ có “hình thù” như thế nào? (chỉ ở mức nghiệp vụ)

Không cần xác định stack hay mô hình AI để hình dung một trải nghiệm lý tưởng:

| Không gian người dùng nhìn thấy | Nó phải trả lời câu gì? | Thông tin không được thiếu |
|---|---|---|
| **Hồ sơ thửa ruộng** | “Ta đang nói về ruộng nào và những điều kiện nào?” | Vị trí, lịch sử, đất, nước, phần người dùng tự khai, chỗ còn thiếu |
| **Bức tranh khí hậu & stress** | “Thách thức chính của thửa/vùng này là gì?” | Xu hướng theo thời gian, lớp dữ liệu NASA, độ phân giải, độ tin cậy |
| **Lịch mùa vụ** | “Các chuỗi cây sẽ nằm ở mùa nào và có xung đột thời gian không?” | Cửa sổ thời vụ, giai đoạn chuyển tiếp, khoảng trống đất |
| **Bàn so sánh luân canh** | “Nếu đổi từ A sang B/C, điều gì có thể tốt hơn hoặc tệ hơn?” | Cùng hệ tiêu chí, phương án hiện tại làm mốc, các điều kiện khả thi |
| **Bộ thử tình huống** | “Kết quả thay đổi thế nào nếu hạn/nóng/nước/ưu tiên khác đi?” | Phân biệt kịch bản giả định với dự báo thực tế |
| **Hồ sơ bằng chứng & bất định** | “Kết luận này dựa trên gì; chỗ nào chưa chắc?” | Nguồn, thời gian, mức chi tiết, yếu tố suy diễn, cảnh báo |
| **Bản tóm tắt quyết định** | “Tôi nên tìm hiểu hoặc kiểm chứng điều gì trước khi quyết?” | Danh sách lựa chọn, đánh đổi, câu hỏi dành cho chuyên gia |

**Chatbox có thể hỗ trợ giải thích**, nhưng không thay được việc xem bảng so sánh, lịch mùa, thay đổi tình huống và kiểm tra bằng chứng.

---

## 11. Thế nào là “đề tài được giải quyết tốt” nếu chưa có tương lai để chấm đúng/sai?

Không nên định nghĩa thành công chỉ là “đề xuất cây X có lợi nhuận cao nhất”. Đây là bài toán quyết định có **nhiều mục tiêu**, dữ liệu không đầy đủ và tương lai bất định. Nên đánh giá trên nhiều tầng khác nhau:

| Tầng đánh giá | Câu hỏi để kiểm tra chất lượng bài toán/sản phẩm | Bằng chứng phù hợp về nguyên tắc |
|---|---|---|
| **Đúng dữ liệu** | Mưa/nhiệt/ẩm/thảm thực vật thể hiện đúng nguồn và phạm vi không? | Đối chiếu tài liệu NASA, đo đạc mặt đất khi có, kiểm tra lỗi thời gian/đơn vị |
| **Đúng nông học** | Chuỗi được đề xuất có khả thi theo đất, thời vụ, cây, sâu bệnh không? | Tài liệu nông học, lịch trồng vùng, phản biện chuyên gia địa phương |
| **Đúng ràng buộc** | Có loại các lựa chọn mà nông dân không thể thực hiện không? | Tình huống nông hộ thật và kiểm tra các giới hạn đã khai báo |
| **Đúng so sánh** | Các phương án có được so trên cùng nền giả định và công khai đánh đổi không? | So sánh với chuỗi hiện trạng, minh bạch từng tiêu chí và trường hợp thay đổi ưu tiên |
| **Trung thực với bất định** | Những kết quả thiếu cơ sở có bị trình bày như chắc chắn không? | Phân biệt quan sát/suy diễn/kịch bản, thông báo thiếu dữ liệu |
| **Hữu ích cho người dùng** | Nông dân/chuyên gia có hiểu vì sao và biết bước kiểm chứng tiếp theo? | Phỏng vấn, xem người dùng giải thích lại quyết định, thử tình huống |
| **Có giá trị theo thời gian** | Khi thêm dữ liệu hoặc thay đổi khí hậu, công cụ có giúp so lại lựa chọn không? | Theo dõi nhiều mùa; thử trên dữ liệu quá khứ với các thời điểm quyết định giả định; đánh giá thực địa dài hạn khi có điều kiện |

### 11.1. Giới hạn của đánh giá quá khứ

Có thể kiểm tra “nếu đứng ở năm trước, chỉ biết dữ liệu khi đó, hệ thống nhìn ra rủi ro gì?” Nhưng **không thể từ đó chứng minh lợi ích thực tế của một chuỗi chưa từng được trồng**. Chứng minh tác động của việc đổi luân canh cần bằng chứng nông học, đối chứng thích hợp hoặc theo dõi ngoài ruộng; chỉ nhìn lịch sử ảnh vệ tinh không đủ để suy ra quan hệ nhân quả.

### 11.2. Thành công ở cấp đề tài

Một kết quả có giá trị khoa học phải trả lời được cả ba câu:

1. **Ta biết gì?** Dữ liệu quan sát và kiến thức đáng tin cậy nào đã được sử dụng?
2. **Ta đang cân nhắc gì?** Những chiến lược nào khả thi và đánh đổi giữa chúng là gì?
3. **Ta chưa biết gì?** Điều gì có thể đảo ngược đánh giá và phải được kiểm chứng ở địa phương?

---

## 12. Kết luận: Problem statement hoàn chỉnh để dùng làm chuẩn chung

> **Field Shift — Adapting Farms with NASA Data** nghiên cứu vấn đề hỗ trợ nông dân lựa chọn **chiến lược luân canh cây trồng qua nhiều mùa** trong bối cảnh khí hậu, nguồn nước và sức khỏe đất biến đổi. Bài toán xuất phát từ sự thiếu kết nối giữa dữ liệu quan sát Trái Đất quy mô lớn, đặc tính đất và cây trồng ở địa phương, cùng điều kiện và ưu tiên thực tế của từng nông hộ. Sản phẩm được kỳ vọng giúp người dùng hiểu bối cảnh ruộng, nhận diện các rủi ro, khám phá nhiều chuỗi luân canh có điều kiện, so sánh lợi ích–chi phí–rủi ro–tác động tiềm năng đến đất và nước, thử các tình huống thay đổi, đồng thời thấy rõ bằng chứng, giới hạn và những điều cần xác minh trước khi triển khai. Mục tiêu là **hỗ trợ quyết định có hiểu biết và thích ứng lâu dài**, không thay thế chuyên gia địa phương và không hứa hẹn một chuỗi trồng trọt tối ưu tuyệt đối.

### Những câu hỏi còn mở — cố ý để mở, chưa quyết định giải pháp

1. Người nông dân thực sự đặt “sức khỏe đất” ở vị trí nào so với dòng tiền và rủi ro mất mùa?
2. Khái niệm “khả thi” cần những thông tin tối thiểu nào trước khi một chuỗi được phép đưa ra xem xét?
3. Những tác động nào có thể đánh giá bằng dữ liệu quan sát hiện có, và tác động nào chỉ nên ghi là *tiềm năng*?
4. Khi dữ liệu vệ tinh quá thô so với ruộng, nên trình bày rủi ro và độ tin cậy ra sao?
5. Nếu các mục tiêu xung đột, đâu là cách biểu đạt để nông dân chủ động quyết định mà không bị một điểm số đánh lừa?
6. Trong điều kiện tương lai chưa chắc chắn, đánh giá và kiểm chứng kết quả ở mức nào là trung thực về mặt khoa học?
7. Các dữ liệu NASA riêng của thử thách công bố ngày 13/11/2026 có bổ sung hoặc thay đổi những khả năng khai thác đã nêu không?

---

## Nguồn gốc và tài liệu tham khảo chủ đạo

**Đề bài và tính chất yêu cầu**

1. [NASA Space Apps Challenge 2026 — Field Shift: Adapting Farms with NASA Data](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/) — nguồn chính thức cho phát biểu cốt lõi.
2. [HackAthlone — bản nội dung đề đầy đủ](https://hackathlone.com/challenges/adapting-farms-with-nasa-data) — bản trình bày của sự kiện địa phương, gồm Background, Objectives, Potential considerations và lịch công bố Resources; đối chiếu với trang chính thức nếu nội dung cập nhật.
3. [NASA Science — Agriculture](https://science.nasa.gov/earth/explore/agriculture/) — bối cảnh NASA hỗ trợ nông nghiệp bằng quan sát Trái Đất.

**NASA Earth observations**

4. [NASA POWER — Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
5. [NASA GPM — IMERG](https://gpm.nasa.gov/data/imerg)
6. [NASA SMAP Level 4 — Soil moisture product](https://data.nasa.gov/dataset/smap-l4-global-3-hourly-9-km-ease-grid-surface-and-root-zone-soil-moisture-analysis-update)
7. [NASA Science — ECOSTRESS](https://science.nasa.gov/mission/ecostress/)
8. [NASA Science — Landsat 9](https://science.nasa.gov/mission/landsat-9/) và [HLS vegetation indices](https://science.nasa.gov/mission/landsat/hls-vegetation-indices/)
9. [NASA MODIS — Vegetation Indices](https://modis.gsfc.nasa.gov/data/dataprod/mod13.php)
10. [NASA/JPL — GRACE Tellus](https://grace.jpl.nasa.gov/)
11. [NASA Earthdata — SRTM](https://search.earthdata.nasa.gov/search?q=SRTMGL1)

**Đất và nông học ngoài NASA**

12. [ISRIC — SoilGrids](https://isric.org/explore/soilgrids)
13. [FAO — Species diversification in conservation agriculture](https://www.fao.org/conservation-agriculture/in-practice/species-diversification/en/)
14. [FAO — ECOCROP](https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/)

**Phân loại độ tin cậy:** Nội dung thử thách, ví dụ dữ liệu và thông số sản phẩm được dựa trên các nguồn trên; các bảng phân tích pain point, hệ quả nghiệp vụ, khung kết quả và use case là **diễn giải/phân tích của nhóm** để xác định vấn đề — không phải điều NASA đã kiểm chứng hay bắt buộc triển khai.
