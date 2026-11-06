# Ghi chú paper — IEEE MOST 2027

> Nguồn: [Submission](https://www.ieeemobility.org/submission.html), [Call for Papers](https://www.ieeemobility.org/call-for-papers.html), tra ngày 06/11/2026. Template: `IEEE-conference-template-062824/` (IEEEtran.cls V1.8b, bản 27/06/2024). Kiểm tra lại trang Submission một tuần trước hạn (spec 16 §5).

## 1. Yêu cầu bắt buộc

| Mục | Yêu cầu | Trong repo |
|---|---|---|
| Template | "Strictly follow the official IEEE conference paper format" | `IEEEtran.cls` copy nguyên từ template; preamble của `main.tex` giữ nguyên template, chỉ thêm `booktabs` và `\graphicspath` |
| Số trang | ≤ 8 trang miễn phí, **tính cả references, hình, bảng, acknowledgments, appendix**. Trang 9–10 phải trả phí: **không dùng** | `make check` |
| Đánh số trang | "Number all pages" | `\pagestyle{plain}` sau `\maketitle` (IEEEtran conference mặc định không in số trang) |
| PDF | Adobe PDF mở và in được, **nhúng đủ font** | `make fonts` (cột `emb` phải toàn `yes`) |
| Hình/bảng | Đọc được khi in đen trắng, không cần phóng to | Hình vector PDF trong `figures/` |
| Double-blind | Bỏ tên, đơn vị, email, lời cảm ơn; tự trích công trình cũ ở ngôi thứ ba; không link lộ danh tính (repo, web, video, dataset, supplementary); xóa metadata PDF. Vi phạm có thể bị loại không cần review | Khối tác giả `Anonymous Authors`; không `\thanks`; không Acknowledgment; không dùng `hyperref` (tránh ghi metadata) |
| Nộp bài | HotCRP: https://most2027.hotcrp.com/. Bài gốc, không nộp nơi khác; tác giả, đơn vị, conflict phải điền đúng và khớp camera-ready | spec 16 |
| Supplementary | Trang Submission không nói có cho nộp kèm; chỉ cấm link lộ danh tính | Code và benchmark dùng link ẩn danh (spec 14 §6) |
| Chính sách AI | Trang Submission không đề cập | Kiểm tra lại một tuần trước hạn |

## 2. Ngày quan trọng

| Mốc | Ngày |
|---|---|
| Hạn nộp | **01/12/2026** (nội bộ: 30/11) |
| Báo kết quả | 15/01/2027 |
| Camera-ready | 10/02/2027 |
| Xin travel grant | 01/03/2027 |
| Hội nghị | 04–07/04/2027, Pomona, California |

## 3. Quy tắc từ template IEEE (giữ khi viết)

- Không đổi lề, font, độ rộng cột, giãn dòng.
- Tiêu đề và abstract: không ký hiệu, ký tự đặc biệt, footnote hay công thức. Không dùng sub-title.
- Hình và bảng đặt ở đầu hoặc cuối cột, sau chỗ được nhắc tới. Caption của hình ở **dưới** hình, tiêu đề bảng ở **trên** bảng. `\label` đặt **sau** `\caption`.
- Viết "Fig.~\ref{...}", kể cả ở đầu câu. Công thức dùng `\eqref{...}`, không viết "Eq. (1)".
- Không dùng `eqnarray`; dùng `align` hoặc `IEEEeqnarray`.
- Chỉ mở subsection khi có ít nhất 2 subsection.
- Trích dẫn dạng số trong ngoặc vuông; không viết "Ref. [3]" trừ đầu câu. Bài đã được nhận nhưng chưa in thì ghi "in press"; chưa công bố thì ghi "unpublished".
- Xóa toàn bộ chữ hướng dẫn của template trước khi nộp (`main.tex` hiện không chứa đoạn nào).

## 4. Cấu trúc folder

```
paper/
├── main.tex            # khung IEEEtran conference, \input 8 section
├── IEEEtran.cls        # copy nguyên từ template (V1.8b)
├── refs.bib            # P1–P24 (docs/MoTaDeTai.md §9.2); mục ghi VERIFY cần kiểm trước khi nộp
├── sections/           # 00-abstract … 07-conclusion; đầu mỗi file ghi ngân sách trang + thông điệp
├── figures/            # hình vector PDF (F1–F3)
├── tables/             # bảng sinh bởi `kwd report` (T1–T4)
├── Makefile            # make | make pages | make check | make fonts | make clean
└── build/              # đầu ra (gitignored)
```

`IEEEtran.bst` (style BibTeX) lấy từ TeX distribution: `tlmgr install ieeetran`.

## 5. Việc còn mở

- [ ] Tắt `\nocite{*}` trong `main.tex` khi các section đã có ít nhất một `\cite` thật (bài chưa có `\cite` nào thì BibTeX báo lỗi "missing \item").
- [ ] Kiểm tra các mục `VERIFY` trong `refs.bib` (P2 bản v2, P3 số trang, P4 bản NeurIPS camera-ready, P7 volume/pages).
- [ ] Trước khi nộp: `make check`, `make fonts`, `pdfinfo build/main.pdf` (Author/Creator trống).

## 6. Claim cần sửa hoặc bỏ (điền ở Phase 4–5)

| Claim | Trạng thái | Ghi chú |
|---|---|---|
