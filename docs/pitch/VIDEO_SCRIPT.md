# FieldShift-Mekong — 30-second demo video

Giọng đọc: tiếng Anh. Phụ đề: tiếng Việt (burn-in). Định dạng: 1920×1080, 30 fps, ≤ 30 s.

**Ý tưởng chủ đạo:** một thửa ruộng thật (Sóc Trăng), một câu hỏi thật ("mùa khô 2026–27 nên trồng gì?"), một câu trả lời có số liệu kiểm chứng. Không quay "tính năng", quay **một quyết định** đi từ vệ tinh xuống ruộng.

Mạch cảm xúc: *nguy cơ → dữ liệu NASA → thửa của tôi → engine thử mọi phương án → câu trả lời rõ ràng → tin được vì minh bạch*.

## Tất cả số liệu trong video đều lấy từ engine

Nguồn: `contracts/fixtures/plan_soctrang.json`, `as_of = 2026-11-14`.

| Trên video | Giá trị | Trường dữ liệu |
|---|---|---|
| El Niño mạnh | ONI +2,46 (tháng giữa 09/2026) | `year_outlook.enso` |
| Mưa mùa khô của các năm tương tự | 49 mm so với 161 mm, tức 30% | `year_outlook.dry_season_rain` (GPM IMERG + POWER) |
| Số kịch bản | 12 (khí hậu nền, khô, nóng, mưa −30%, mặn sớm, ENSO analog, dự báo mùa, 4 × CMIP6 2041–2050…) | `options[].metrics` |
| Hiện trạng lúa–lúa–lúa | 177 ngày cây đứng trong khung mặn | `baseline.salinity_exposure_days` |
| Phương án "Giảm rủi ro": lúa gieo sớm – nghỉ vụ – lúa | 84 ngày, đạt 12/12 kịch bản, độ tin cậy MEDIUM | `options[0]` |
| Việc cần kiểm tra | Đo ECw nước kênh | `confidence.unknowns = ["canal_ecw"]` |

> ⚠️ Không đưa con số "tiết kiệm 45% nước" (1824 → 1008 mm) vào lời đọc. Phần lớn mức giảm đến từ việc nghỉ một vụ, nên dễ bị giám khảo coi là nói quá. Chỉ số ngày phơi mặn mới là lý do chính của engine.

## Kịch bản phân cảnh

| # | Thời gian | Hình ảnh (quay màn hình app thật) | Lời đọc (EN) | Phụ đề (VI) | Tiêu chí |
|---|---|---|---|---|---|
| 1 | 0:00–0:04 | Globe tự xoay, đêm chuyển sang ngày. Camera lao vào ĐBSCL theo đúng hiệu ứng chuyển globe → bản đồ của app. Chữ nhỏ: *Mekong Delta, Vietnam* | Half of Vietnam's rice grows here. This dry season, the salt comes early. | Một nửa lúa gạo Việt Nam trồng ở đây. Mùa khô này, mặn đến sớm. | Impact |
| 2 | 0:04–0:10 | Banner "Mùa khô tới sẽ giống năm nào". Dùng biểu đồ mưa IMERG: cột 2015–16 và 2023–24 thấp hẳn. Phủ chữ lớn **ONI +2.5** và **30%** | A strong El Niño. In years like this, NASA's GPM saw just thirty percent of normal dry-season rain. | El Niño mạnh. Những năm như vậy, vệ tinh GPM của NASA chỉ ghi nhận 30% lượng mưa mùa khô bình thường. | Relevance (dữ liệu NASA) |
| 3 | 0:10–0:13 | Vẽ thửa: click 4 góc trên ảnh vệ tinh Sóc Trăng, diện tích tự hiện. **Không có lời đọc**, chỉ tiếng "click" và chữ *Draw your field* | *(không lời)* | Vẽ thửa ruộng của bạn | Presentation |
| 4 | 0:13–0:19 | Màn Đề xuất đang tính. Các chuỗi vụ chạy qua timeline, dải mặn đỏ nhạt. Badge nhỏ: *FAO-56 · NASA POWER · 12 scenarios · CMIP6 → 2050* | It tests every rotation, day by day, on NASA POWER weather — across twelve scenarios, out to 2050. | Engine thử mọi chuỗi luân canh theo từng ngày, trên dữ liệu thời tiết NASA POWER, qua 12 kịch bản, tới năm 2050. | Validity, Creativity |
| 5 | 0:19–0:25 | Hai timeline xếp chồng: **lúa–lúa–lúa: 177 ngày** trong dải mặn, rồi **gieo sớm + nghỉ vụ: 84 ngày**. Số đếm lùi 177 → 84. Tag xanh **12/12 scenarios** | For Sóc Trăng: sow early, rest the saltiest season — salt-window days drop from 177 to 84. | Với Sóc Trăng: gieo sớm, nghỉ vụ mặn nhất. Số ngày cây phơi mặn giảm từ 177 xuống 84. | Impact, Validity |
| 6 | 0:25–0:30 | Bấm vào con số, hiện panel nguồn (POWER / IMERG / Công văn 2504) và checklist **"Đo ECw nước kênh trước khi gieo"**. Kết bằng logo, tagline và *NASA Space Apps 2026 · Field Shift* | Every number shows its source — and what to check first. FieldShift: plan before the salt arrives. | Mỗi con số đều có nguồn, kèm việc cần kiểm tra trước. FieldShift: lên kế hoạch trước khi mặn về. | Validity, Presentation |

Lời đọc khoảng 76 từ. Đọc với tốc độ 2,6–2,8 từ/giây thì vừa 28–29 s, còn dư khoảng 1 s để nhạc kết.

Chú thích nhỏ ở góc dưới cảnh 4–5, hiện cả video: *Model estimates · not a field measurement · verify salinity on site*. Chú thích này nói rõ giới hạn và giúp tránh bị trừ điểm vì nói quá.

## Vì sao kịch bản này ăn điểm

- **Impact:** mở bằng một nguy cơ có thật (mặn, El Niño 2026–27) và kết bằng một hành động cụ thể cho một thửa cụ thể.
- **Relevance:** gọi tên đích danh GPM, POWER và CMIP6, đúng các nguồn đề bài liệt kê. Đề bài yêu cầu so với chuỗi hiện tại, và cảnh 5 đặt hai chuỗi cạnh nhau.
- **Validity:** có 12 kịch bản, kết quả 12/12, có nguồn và việc cần kiểm tra, có chú thích "model estimate". Ít đội nào dám nói rõ giới hạn như vậy.
- **Creativity:** dùng năm tương tự ENSO để trả lời câu hỏi "mùa khô tới sẽ giống năm nào", cùng hiệu ứng globe → thửa ruộng liền mạch.
- **Presentation:** mỗi cảnh chỉ nói một ý, có một con số lớn trên màn hình, và mọi hình ảnh đều quay từ app thật.

## Hướng dẫn quay

1. Chạy API và `frontend/` (port 5180). Mở thửa demo `fld_soctrang` để có số đúng như bảng trên. Quay bằng OBS ở 1080p60, ẩn thanh trình duyệt (chế độ kiosk hoặc F11).
2. Quay dư mỗi cảnh 2–3 giây để cắt cho khớp với giọng đọc.
3. Nhạc: ambient, tiết tấu chậm, tăng dần. Có thể dùng nhạc CC0 từ Pixabay Music hoặc Free Music Archive (lọc CC-BY), nhớ ghi credit. Giảm âm lượng nhạc khoảng −18 dB dưới giọng đọc.
4. Phụ đề: burn-in `subtitles_vi.srt`. Dùng font Be Vietnam Pro (font của app), cỡ khoảng 46 px, viền đen 2 px, đặt ở 1/6 dưới màn hình.
5. Trước khi xuất video: đối chiếu từng con số với bảng ở đầu tài liệu. Nếu chạy lại engine ra số khác thì sửa kịch bản theo số mới.

## Giọng đọc (TTS) và bản dựng cuối

- Bản cuối: lời đọc rút gọn trong `voiceover_en.txt`, mỗi cảnh bắt đầu theo câu đọc của nó (tổng 29,9 s). Phụ đề cuối: `subtitles_vi.srt`.
- Giọng: **Chatterbox** (Resemble AI, MIT), giọng nam nhân bản từ Kokoro-82M `am_michael` (Apache-2.0), độ truyền cảm 0,62, 2 take mỗi câu, chọn take bằng faster-whisper (loại take lặp câu hoặc đọc sai số).
- Video ghi rõ "Voice-over AI-generated (Chatterbox TTS)" trên end card và trong metadata MP4, theo quy định SI của Space Apps.
- Pipeline dựng lại: `scripts/pitch/video/README.md`.
