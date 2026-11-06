# Phase 6 — Rà soát, ẩn danh, phát hành và nộp bài (29–30/11)

> Xem `00-README.md` cho Global Constraints. Checklist chi tiết: `docs/04-delivery/16-submission-checklist.md`.

**Goal:** Nộp lên HotCRP trước 23:59 ngày **30/11/2026** một PDF hợp lệ, ẩn danh, ≤ 8 trang, kèm link code và benchmark ẩn danh.

## Vấn đề cần giải quyết

Lỗi hình thức có thể làm bài bị loại không qua review: lộ danh tính, quá trang, PDF thiếu font. Lỗi nội dung có thể khiến reviewer phản bác ngay: claim quá mạnh, thiếu so sánh với CORA. Cần một lượt đọc độc lập, một lượt kiểm tra kỹ thuật, và nộp sớm một ngày để chừa chỗ cho sự cố.

> **Làm sớm (trước 20/11):** tạo tài khoản HotCRP tại https://most2027.hotcrp.com/ và kiểm tra form nộp bài (các trường bắt buộc, topic, conflict). Đây không phải việc của ngày cuối.

---

### Step 6.1 [PAPER] — Đọc độc lập như reviewer · **[GVHD; AI reviewer do A chạy]** (nhận PDF 27/11, GVHD trả nhận xét tối 28/11)

- [ ] **GVHD** (~1,5 giờ) đọc PDF với vai reviewer IEEE MOST. Song song, A mở một phiên AI mới, chỉ đưa PDF và CFP, yêu cầu đóng vai reviewer. Cả hai trả lời:
  1. Đóng góp chính là gì, trong một câu?
  2. Khác CORA và ReOpt-LLM ở đâu?
  3. Claim nào chưa được chứng minh đủ?
  4. Hình hoặc bảng nào khó hiểu?
  5. Kết quả trên câu do người viết và phần phân loại lỗi có thuyết phục không?
  6. Có chỗ nào lộ danh tính không?
- [ ] 27–28/11: A sửa theo AI reviewer. 29/11: A sửa theo nhận xét GVHD. Chỉ sửa chữ, không thêm thí nghiệm.
- [ ] Commit `paper: fixes from internal review`.

### Step 6.2 [CODE] — Phát hành code và benchmark ẩn danh (29/11) · **[B]**

- [ ] Tạo bản sạch theo **danh sách cho phép**: chỉ chép `src/`, `tests/`, `configs/`, `scripts/` (bỏ `scripts/smoke_translate.py`), `pyproject.toml`, `uv.lock`, `.python-version`, README ẩn danh và gói benchmark. Không chép `docs/`, `paper/`, `reference-documents/`, `IEEE-conference-template-062824/`, `CLAUDE.md`, `.claude/`, `debit-last-submit.md`, `mynote.md`, `PROMPT_TEMPLATE.md`, ảnh, `.env`, `.git`.
- [ ] Trong bản sạch: xóa khối `authors` của `pyproject.toml`; tìm tên, email bằng `grep -rniE "nguyen|kha an|khaan|@gmail|cloudian" .` → kết quả phải rỗng (fixture bệnh viện dùng tên điểm trung tính từ 07/11).
- [ ] README ẩn danh: cài đặt (`uv sync`), tải LMRC, tái tạo benchmark (`kwd snapshot`, `kwd bench`), tái tạo bảng (`kwd report`), giấy phép (code MIT; benchmark dẫn xuất từ LMRC theo CC BY-NC 4.0).
- [ ] Đóng gói benchmark: `main/items.jsonl`, `human/items.jsonl` (không kèm tên người viết, chỉ `writer_id`) + snapshot + config sinh dữ liệu (không kèm cache LLM có API key hay metadata cá nhân).
- [ ] Đẩy lên một repo GitHub riêng rồi tạo link ẩn danh qua https://anonymous.4open.science; mở link ở cửa sổ ẩn danh để kiểm tra không lộ tên.
- [ ] Thêm link ẩn danh vào paper (chân trang của Abstract hoặc đầu Experiments).

### Step 6.3 [PAPER] — Kiểm tra kỹ thuật PDF (29/11 chiều) · **[B]**

- [ ] Đọc `debit-last-submit.md`: mọi nợ P3 đã trả hoặc được ghi lý do bỏ qua.

- [ ] `make check` → ≤ 8 trang.
- [ ] `pdffonts build/main.pdf`: mọi font có cột `emb` = `yes`.
- [ ] `pdfinfo build/main.pdf` và `exiftool build/main.pdf`: không có Author/Creator lộ tên. Nếu có: thêm `\hypersetup{pdfauthor={}}` hoặc xóa bằng `exiftool -all:all= build/main.pdf`.
- [ ] Mở PDF ở hai trình xem khác nhau; in thử 1 trang hình để xem đọc được khi in đen trắng.
- [ ] Đi hết danh sách `docs/04-delivery/16-submission-checklist.md` §2–§4, tick từng ô.
- [ ] Đặt tên file không chứa tên tác giả, ví dụ `most2027_know_when_to_defer.pdf`.

### Step 6.4 — Nộp bài (30/11) · **[A + B cùng kiểm tra]**

- [ ] Kiểm tra lại trang Submission của hội nghị (hạn có bị dời, quy định mới về số trang hay việc dùng AI).
- [ ] HotCRP: điền tiêu đề, abstract (copy từ PDF), topic ("Logistics and last-mile delivery"; "Safe, secure, and trustworthy mobility"), conflict of interest, tick xác nhận bài gốc. Tải PDF lên.
- [ ] Tải lại PDF từ HotCRP, mở kiểm tra.
- [ ] Lưu bản nộp vào `paper/submitted/` cùng `RUNS.md`; tag git `submitted-most2027`.
- [ ] Ghi dòng "Đã nộp" vào `docs/CONTENT.md` §6.

### Step 6.5 — Sau khi nộp (ghi nhớ, không làm ngay)

- [ ] Giữ nguyên `runs/` và cache cho đến khi có kết quả (15/01/2027) để trả lời reviewer hoặc chỉnh camera-ready.
- [ ] Nếu được nhận: camera-ready trước 10/02/2027 (thêm tên tác giả, link repo thật); đăng ký full rate; chuẩn bị trình bày trực tiếp ở Pomona (04–07/04/2027); hạn xin travel grant 01/03/2027.

## Kết thúc Phase 6 khi

- [ ] HotCRP hiển thị bài ở trạng thái đã nộp, PDF tải về mở được.
- [ ] Link code ẩn danh hoạt động và không lộ danh tính.
