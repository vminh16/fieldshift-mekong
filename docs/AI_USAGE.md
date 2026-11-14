# Khai báo sử dụng AI / AI usage declaration

## Công cụ và phạm vi

Nhóm đã dùng **Claude Code (Anthropic)** với các mô hình **Claude Opus 5.5, Claude Sonnet 5.5 và Claude Fable 5.2** để sinh mã, rà soát mã, audit sản phẩm và nghiên cứu. **OpenAI Codex** được dùng cho các nhiệm vụ triển khai. Đây là khai báo công cụ hỗ trợ, không phải tuyên bố về tác giả con người của từng phần mã hay tài liệu.

## Rà soát đầu ra

Đầu ra AI được rà soát bằng kiểm thử tự động, kiểm tra TypeScript và bản dựng, chạy API/giao diện, backtest và đối chiếu các báo cáo giới hạn. Backtest chỉ đánh giá trong dữ liệu và giả định được ghi trong báo cáo; không thay thế kiểm định tại ruộng hoặc xác nhận của chuyên gia. Con người trong nhóm quyết định phạm vi sản phẩm và chấp nhận hay loại bỏ đề xuất của công cụ.

## Quyết định thuộc về nhóm

Nhóm quyết định người dùng mục tiêu là nông dân và cán bộ khuyến nông ở ĐBSCL. Nhóm để `R_MACHINERY` trống, chưa triển khai; thông tin máy móc chưa được coi là ràng buộc đã kiểm định. Các trọng số heuristic là giả định của nhóm, phải có nhãn “ước lượng nhóm (heuristic)”; chúng không phải mô hình năng suất hoặc lợi nhuận đã kiểm định. AI không tự quyết định các lựa chọn phạm vi này hay quyết định canh tác tại ruộng.

## TODO — Công cụ AI khác nhóm đã dùng (nhóm bổ sung trước khi nộp)

- [ ] Nhóm kiểm tra và bổ sung tên công cụ, nhà cung cấp, mô hình/phiên bản (nếu biết) và phần việc được hỗ trợ.
- [ ] Nhóm xác nhận danh sách và phạm vi sử dụng trước khi nộp.

## Video demo (giọng đọc AI)

Hình ảnh trong video là quay màn hình ứng dụng thật. **Giọng đọc tiếng Anh do AI tạo** bằng Chatterbox TTS (Resemble AI, MIT), nhân bản giọng nam từ đoạn mẫu Kokoro-82M (Apache-2.0); mỗi câu được kiểm tra lại bằng faster-whisper. Nhạc nền được tổng hợp bằng mã. Điều này được ghi trên end card của video và trong metadata MP4. Không dùng hay chỉnh sửa logo/nhận diện NASA. Quy trình dựng nằm ở `scripts/pitch/video/`.

## English

The team used **Claude Code (Anthropic)** with **Claude Opus 5.5, Claude Sonnet 5.5 and Claude Fable 5.2** for code generation, review, product auditing and research. **OpenAI Codex** supported implementation tasks. Outputs were reviewed through automated tests, TypeScript/build checks, live API/UI checks, backtests and documented limitations; these checks do not establish field validation. The team retained decisions on target users and scope, left `R_MACHINERY` unimplemented, and labelled heuristic weights as team estimates rather than validated yield/profit predictions. Other AI tools, if any, remain for the team to declare in the TODO above before submission; no unknown human authorship is claimed here.

### Demo video

Video frames are screen recordings of the real app. The **English voice-over is AI-generated** with Chatterbox TTS (Resemble AI, MIT), using a male voice cloned from a Kokoro-82M (Apache-2.0) reference; every take was checked with faster-whisper speech recognition. Background music is synthesized in code. This is stated on the video's end card and in the MP4 metadata. No NASA logos or branding were generated or modified. The pipeline is in `scripts/pitch/video/`.
