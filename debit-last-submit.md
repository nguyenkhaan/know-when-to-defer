# Nợ rà soát cuối (paper)

> Mỗi khi viết xong một phần paper, ghi lại ở đây những gì phải kiểm tra hoặc sửa sau. Đánh `[x]` khi đã trả nợ.
> Mức: **P1** = phải xong trước mốc GVHD gần nhất · **P2** = trước khóa kết quả 22/11 · **P3** = trước khi nộp (29/11).

## Mục III · Problem Formulation (`paper/sections/03-problem.tex`, nháp xong 06/11, commit `9a87b93`)

### 1. Trích dẫn

| | Mức | Trích dẫn | Dùng cho câu | Tình trạng | Việc cần làm |
|---|---|---|---|---|---|
| [ ] | P1 | `angelopoulos2024crc` [Thm. 1], [Prop. 1] | Điều kiện áp CRC; rủi ro có điều kiện không dùng CRC được | Nội dung **đã đối chiếu** với PDF arXiv v4 trong `reference-documents/` (06/11) | Kiểm tra số Thm. 1 / Prop. 1 có giữ nguyên ở bản ICLR 2024 không (ta trích ICLR nhưng đọc bản arXiv); bib còn thiếu trang/URL |
| [ ] | P1 | `feng2026cora` (CORA) | "As in CORA, we require the joint risk" | **Chưa đọc toàn văn**, chỉ dựa vào ghi chú `MoTaDeTai.md` §9 (Eq. (3)); không có PDF trong repo | Tải PDF, xác nhận loss "thực thi ∧ gây hại" đúng là rủi ro kết hợp như câu viết; kiểm tra đã có venue chính thức chưa |
| [ ] | P1 | `rahman2026rolestratified` (P22) | "A single threshold can still hide violations concentrated in rare operation types" | **Chưa đọc toàn văn**, mới xem bản HTML qua ghi chú; không có PDF trong repo | Tải PDF, xác nhận đúng kết quả "ngân sách co lại còn `α · p_c`"; kiểm tra venue |
| [ ] | P1 | Toàn bộ `refs.bib` (24 mục) | — | Chưa mục nào kiểm tra bằng API | Chạy `/citation-verification` rồi `/bibtex-hygiene` trước 10/11. Riêng P23 (`kotte2026whencancrc`) chưa rõ tác giả |

### 2. Độ dài

- [ ] **P3** · Mục III ~520 từ văn xuôi + 3 công thức riêng dòng, vượt ngân sách 0,75 trang khoảng 5–7 dòng. Chờ PDF đủ trang rồi mới cắt. Ba chỗ cắt dự kiến, theo thứ tự:
  1. ví dụ "such as how early a stop is served before its new window opens" (đoạn Harm, ~12 từ);
  2. câu rủi ro có điều kiện + [Prop. 1] (cuối đoạn Decision rule, ~22 từ) — chỉ cắt nếu LTT chắc chắn bị bỏ và không ai hỏi;
  3. câu cuối "We use (3) as the reference…" (đoạn Coverage, ~10 từ).

### 3. Phụ thuộc vào mục khác (mục III đã hứa, mục sau phải có)

- [ ] **P2** · Mục IV (Method) phải có: công thức chọn `λ̂` và lưới ngưỡng **có `−∞`**; lập luận lưới điểm calibration (vấn đề liên tục phải sau khi đổi biến `θ = −λ`, spec 12 §2.1); danh sách loại thao tác DSL; nhóm `compound`; nguồn của điểm rủi ro `s` (LLM outputs + solver feedback). Mục III trỏ tới Section IV hai lần.
- [ ] **P2** · Mục VI (Experiments) phải báo: tần suất vi phạm qua 100 split (vì CRC chỉ bảo đảm trung bình); rủi ro theo nhóm `ĉ` (được bảo đảm) **và** theo loại gold `c` (phân tích); `cov_max` (3) làm đường tham chiếu trong F2/T3; độ nhạy `ε ∈ {0, 5, 10}` (spec 09, check V2).
- [ ] **P2** · Mục IV phải nói `cost` trong (1) **không** có số hạng độ lệch `dev_weight·deviation` mà solver dùng khi tối ưu (spec 07 §3, spec 09 §2), để reviewer không tưởng nhầm `Solve` tối ưu đúng `cost`. Thêm 06/11.
- [ ] **P3** · Intro: viết "large language model (LLM)" ở lần dùng đầu; Abstract không dùng viết tắt.
- [ ] **P2** · Mục IV hoặc VI phải có một câu về nhóm nhỏ: CRC theo nhóm `ĉ` cần tối thiểu `n ≥ 1/α − 1` mẫu calibration (99 ở α = 0,01; 49 ở 0,02), nhóm dưới ngưỡng bị chuyển duyệt hết (bảo đảm vẫn giữ, coverage của nhóm = 0). Báo số nhóm bị chuyển duyệt hết trong T3. Caption F3 và câu về C5 phải ghi rõ `α_F3` và quy tắc chọn (chỉ dựa vào số mẫu, spec 13 §14.0); nếu `α_F3 ≠ α_main` thì giải thích một câu (spec 12 §2.2, spec 13 §14.5; thêm 06/11).

### 4. Tham số phải khớp với code của B

- [ ] **P2** · `τ = 1 min`, `ε = max{5 min, 0,02·cost(P*)}` phải khớp `configs/harm.yaml` (`tol_min`, `eps_abs`, `eps_rel`) bản cuối.
- [ ] **P2** · Paper chưa ghi **hệ số phạt trễ** trong `cost` (spec 07 §3 `late_penalty` chưa chốt). Khi B chốt, cân nhắc thêm "(penalty $w$ per minute)".
- [ ] **P2** · Nếu pilot đổi danh sách loại lệnh hoặc quy tắc lệnh ghép, xem lại đoạn Setting.

### 5. Câu hỏi mở về phương pháp

- [x] **P2** · Lỗi non-binding: Mục III viết `P̂ = P`, spec cũ chỉ băm thứ tự. **Đã chốt (a) ngày 06/11:** digest băm thứ tự + `service_start` làm tròn phút + `end_time`; mọi giờ trong `Plan` lấy từ hàm chung `schedule()` (spec 07 v0.2 §5); câu paper giữ nguyên. Đã sửa spec 07, 08, 09, 11, 14 và Task 1.4.
- [ ] **P1** · **Báo B trước khi làm Task 1.4:** `Plan` có thêm `service_start`, hàm `schedule()`, digest mới, `check_constraints` dùng `service_start`, mô hình OR-Tools thêm cận dưới `tw_start` của khung giờ gốc (spec 07 §2, §5).
- [ ] **P1** · **`P̂ = P` có thể gần như không bao giờ xảy ra trên tuyến thật** (có từ trước, không do quyết định (a)). `P` là thứ tự tài xế LMRC đã chạy, thường chưa tối ưu; `solve(P, ê)` tối ưu lại nên có thể đổi thứ tự dù `ê` đã thỏa sẵn (spec 07 §7 chỉ yêu cầu `solve(P, ∅)` có cost ≤). Khi đó lỗi non-binding, `gold_binding` và tín hiệu S3 đều sai trên dữ liệu thật, dù fixture bệnh viện vẫn qua. Cần chọn trước pilot 10/11: so `P̂` với `P₀ = solve(P, ∅)` thay vì `P` (paper đổi định nghĩa `P`), hoặc buộc solver giữ thứ tự khi thứ tự hiện tại đã thỏa `ê`. Đo nhanh trên 20 tuyến thật: tỷ lệ `solve(P, ∅).digest != P.digest`.
- [ ] **P1** · Hỏi GVHD 10/11: dữ liệu chia **theo tuyến** nhưng CRC tính rủi ro **theo yêu cầu**. Các yêu cầu cùng tuyến phụ thuộc nhau, nên giả định "exchangeable" mà mục III nêu có thể không đúng hẳn. Tùy câu trả lời: thêm 1 câu giới hạn ở Mục VII, hoặc đổi đơn vị calibration.

### 6. Nhất quán thuật ngữ và ký hiệu (rà khi các mục khác đã viết)

- [ ] **P3** · Ký hiệu: ~~`t_0` vs `t_now`~~ đã thống nhất `$t_{\mathrm{now}}$` (06/11); `ĉ` (loại lệnh LLM) và `c` (loại gold) không được lẫn ở Results; `Solve(·)` thống nhất.
- [ ] **P3** · Thuật ngữ: *non-executable*, *harmless error*, *non-binding error*, *joint risk*, *coverage* dùng đúng một nghĩa trong toàn bài.

### 7. Văn phong và chính sách

- [x] Slop check mục III: index 0,0 (06/11).
- [ ] **P3** · Đối chiếu giọng văn với 1–3 trang A tự viết trước đây (bước 4 của `unslop-academic-writing`), làm trước khi viết Intro.
- [ ] **P3** · Kiểm tra chính sách khai báo dùng AI của IEEE MOST 2027 (một tuần trước hạn, `paper/NOTES.md`).
