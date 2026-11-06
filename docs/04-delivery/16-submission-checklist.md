# 16 · Submission Checklist — IEEE MOST 2027

> Trạng thái: Draft v0.1 · Cập nhật 05/11/2026 · Nguồn: [Call for Papers](https://www.ieeemobility.org/call-for-papers.html), [Submission](https://www.ieeemobility.org/submission.html) (truy cập 05/11/2026). Kiểm tra lại trang chính thức một tuần trước hạn, vì các năm trước hạn nộp từng bị dời.

## 1. Thông tin hội nghị

| Mục | Giá trị |
|---|---|
| Hội nghị | IEEE International Conference on Mobility: Operations, Services, and Technologies (MOST) 2027, lần thứ 5 |
| Thời gian, địa điểm | 04–07/04/2027, Pomona, California |
| Hạn nộp | **01/12/2026** (mục tiêu nội bộ: 30/11) |
| Báo kết quả / camera-ready | 15/01/2027 / 10/02/2027 |
| Cổng nộp | HotCRP: https://most2027.hotcrp.com/ |
| Chủ đề khớp | "Logistics and last-mile delivery"; "Safe, secure, and trustworthy mobility"; "Foundation and world models for mobility" |

## 2. Định dạng

- [ ] IEEE conference template (LaTeX `IEEEtran`, tùy chọn `conference`).
- [ ] **≤ 8 trang, tính cả references, hình, bảng, appendix.** Trang 9–10 được phép nhưng phải trả phí: không dùng.
- [ ] PDF nhúng đủ font, mở và in được.
- [ ] **Đánh số mọi trang** ("Number all pages", trang Submission, tra 06/11/2026). IEEEtran conference mặc định không in số trang; `paper/main.tex` thêm `\pagestyle{plain}`.
- [ ] Hình dạng vector (PDF), đọc được khi in đen trắng.

## 3. Double-blind

- [ ] Không có tên, đơn vị, email, lời cảm ơn trong PDF.
- [ ] Xóa metadata PDF (Author, Creator…), kiểm tra bằng `exiftool` hoặc `pdfinfo`.
- [ ] Tự trích công trình cũ ở ngôi thứ ba.
- [ ] Không có link lộ danh tính (GitHub cá nhân, website, Google Drive có tên). Code và benchmark dùng link ẩn danh (spec 14 §6).
- [ ] Tên file PDF và file phụ không chứa tên tác giả.

## 4. Nội dung và đạo đức nghiên cứu

- [ ] Bài gốc, chưa công bố và không đang nộp nơi khác (tick xác nhận trên HotCRP).
- [ ] Ghi rõ giấy phép LMRC (CC BY-NC 4.0) và nguồn dữ liệu.
- [ ] Mỗi con số trong bài truy được về một run trong `paper/RUNS.md`.
- [ ] Không claim "first" hay "novel" khi chưa có bằng chứng; claim khớp bảng claim → bằng chứng (doc 02).
- [ ] Có mục Limitations: câu tổng hợp, một xe, giả định exchangeable, shift.
- [ ] Trích dẫn đầy đủ CORA (P21), Role-Stratified CRC (P22), ReOpt-LLM bản NeurIPS 2026 (P4).

## 5. Ngày nộp

- [ ] Một tuần trước: kiểm tra lại trang Submission (số trang, policy dùng AI, supplementary material).
- [ ] 29/11: đọc soát toàn bài, rà danh sách này lần cuối.
- [ ] 30/11: nộp PDF lên HotCRP, điền abstract, topic, conflict of interest.
- [ ] Lưu bản nộp vào `paper/submitted/` kèm run IDs.

## 6. Sau khi được nhận (nhắc trước)

- Ít nhất một tác giả đăng ký **full rate** và **trình bày trực tiếp** tại Pomona; bài không trình bày có thể bị loại khỏi proceedings.
- Hạn xin travel grant: 01/03/2027.
- Camera-ready (10/02/2027): thêm lại tên tác giả, link repo thật, lời cảm ơn.
