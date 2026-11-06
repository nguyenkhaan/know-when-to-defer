# Nợ rà soát cuối (paper)

> Mỗi khi viết xong một phần paper, ghi lại ở đây những gì phải kiểm tra hoặc sửa sau. **Nợ đã trả thì xóa khỏi file** (quyết định đã chốt ghi ở `docs/CONTENT.md`, không giữ ở đây).
> Mức: **P1** = phải xong trước mốc GVHD gần nhất · **P2** = trước khóa kết quả 22/11 · **P3** = trước khi nộp (29/11).

## Mục III · Problem Formulation (`paper/sections/03-problem.tex`, nháp xong 06/11, commit `9a87b93`; sửa điều kiện `x = 1` và `t_now` ở `e511e92`; tinh gọn 07/11: bỏ ký hiệu `c` và câu Prop. 1, thêm chỗ trỏ tới bộ lọc fixed point)

### 1. Trích dẫn

| | Mức | Trích dẫn | Dùng cho câu | Tình trạng | Việc cần làm |
|---|---|---|---|---|---|
| [ ] | P1 | `angelopoulos2024crc` [Thm. 1] | Điều kiện áp CRC | Nội dung **đã đối chiếu** với PDF arXiv v4 trong `reference-documents/` (06/11) | Kiểm tra số Thm. 1 có giữ nguyên ở bản ICLR 2024 không (ta trích ICLR nhưng đọc bản arXiv); bib còn thiếu trang/URL |
| [ ] | P1 | `feng2026cora` (CORA) | "As in CORA, we require the joint risk" | **Chưa đọc toàn văn**, chỉ dựa vào ghi chú `MoTaDeTai.md` §9 (Eq. (3)); không có PDF trong repo | Tải PDF, xác nhận loss "thực thi ∧ gây hại" đúng là rủi ro kết hợp như câu viết; kiểm tra đã có venue chính thức chưa |
| [ ] | P1 | `rahman2026rolestratified` (P22) | "A single threshold can still hide violations concentrated in rare operation types" | **Chưa đọc toàn văn**, mới xem bản HTML qua ghi chú; không có PDF trong repo | Tải PDF, xác nhận đúng kết quả "ngân sách co lại còn `α · p_c`"; kiểm tra venue |
| [ ] | P1 | Toàn bộ `refs.bib` (24 mục) | — | Chưa mục nào kiểm tra bằng API | Chạy `/citation-verification` rồi `/bibtex-hygiene` trước 10/11. Riêng P23 (`kotte2026whencancrc`): bib đã ghi tác giả Varun Kotte nhưng chưa đối chiếu với arXiv |

### 2. Độ dài

- [ ] **P3** · Mục III: 516 từ văn xuôi + 3 công thức riêng dòng (đếm 07/11 bằng `slop_check.py` của skill `unslop-academic-writing`; slop index 0.0), vẫn vượt ngân sách 0,75 trang vài dòng. Chờ PDF đủ trang rồi mới cắt. Hai chỗ cắt dự kiến, theo thứ tự:
  1. ví dụ "such as how early a stop is served before its new window opens" (đoạn Harm, ~12 từ);
  2. câu cuối "We use (3) as the reference…" (đoạn Coverage, ~10 từ).

### 3. Phụ thuộc vào mục khác (mục III đã hứa, mục sau phải có)

- [ ] **P2** · Mục IV (Method) phải có: công thức chọn `λ̂` và lưới ngưỡng = điểm calibration ∪ {`−∞`} (lập luận liên tục sau khi đổi biến `θ = −λ` để ở spec 12 §2.1, **không** đưa vào paper); danh sách loại thao tác DSL (6 op) kèm **một mệnh đề phạm vi**: DSL chỉ gồm ràng buộc lên kế hoạch, lệnh đổi dữ liệu bài toán (thời gian di chuyển, thời gian phục vụ) nằm ngoài phạm vi; nhóm `compound`; nguồn của điểm rủi ro `s` (LLM outputs + solver feedback). Mục III trỏ tới Section IV hai lần.
- [ ] **P2** · Mục VI (Experiments) phải báo: tần suất vi phạm qua 100 split (vì CRC chỉ bảo đảm trung bình); rủi ro theo nhóm `ĉ` (được bảo đảm; rủi ro theo loại gold `c` chỉ ở `runs/`); `cov_max` (3) làm đường tham chiếu trong F2/T3; độ nhạy `ε ∈ {0, 5, 10}` **một mệnh đề trong Setup** (spec 09 §2, check V2).
- [ ] **P2** · Mục IV phải nói solver tối ưu với **trọng số riêng** (`late_penalty`, `shift_penalty`, `dev_weight`, spec 07 §3), còn `cost` trong (1) tính bằng phút, trọng số 1, không có số hạng độ lệch (spec 09 §2; §III đã viết "all in minutes" từ 07/11). Một mệnh đề, để reviewer không tưởng `Solve` tối ưu đúng `cost`. Thêm 06/11, sửa 07/11.
- [ ] **P2** · Mục IV, đoạn DSL: **một mệnh đề** liệt kê những gì parser chặn (JSON sai, điểm không tồn tại hoặc đã giao, khoảng giờ rỗng hoặc đã qua), để reviewer thấy lỗi dễ bắt không được tính là gây hại. Nháp: *"The parser rejects malformed JSON, unknown or already-served stops, and empty or past time intervals; rejected edits are deferred."* Không tách `bad_interval` thành dòng/cột riêng trong T1 (spec 06 §4). Thêm 07/11.
- [ ] **P3** · Intro: viết "large language model (LLM)" ở lần dùng đầu; Abstract không dùng viết tắt.
- [ ] **P2** · Mục IV hoặc VI phải có một câu về nhóm nhỏ: CRC theo nhóm `ĉ` cần tối thiểu `n ≥ 1/α − 1` mẫu calibration (99 ở α = 0,01; 49 ở 0,02), nhóm dưới ngưỡng bị chuyển duyệt hết (bảo đảm vẫn giữ, coverage của nhóm = 0). Báo số nhóm bị chuyển duyệt hết trong T3. Câu về C5 (dòng theo nhóm trong T3; không có F3) phải ghi rõ `α_F3` và quy tắc chọn (chỉ dựa vào số mẫu, spec 13 §14.0); nếu `α_F3 ≠ α_main` thì thêm một dòng T3 và giải thích một câu (spec 12 §2.2; thêm 06/11, sửa 07/11).

- [ ] **P2** · Mục V (Benchmark) phải có một câu: chỉ giữ snapshot mà kế hoạch hiện tại là fixed point của solver (`solve(P, ∅)` trả lại đúng `P`), kèm số tuyến bị loại và bao nhiêu tuyến trong đó đang trễ khung giờ gốc, tức tuyến đang trễ bị loại bớt (spec 08 §2.1; thay cho ý giới hạn riêng ở Mục VII). Không có câu này thì định nghĩa non-binding `P̂ = P` ở Mục III không đứng vững; §III đã trỏ tới §V (`\ref{sec:benchmark}`, 07/11). Kèm nửa câu về phạm vi: bảo đảm CRC áp cho snapshot đã lọc, và hệ thống triển khai kiểm tra được điều kiện này lúc nhận yêu cầu vì không cần gold.
- [ ] **P2** · Mục V: **một mệnh đề** nêu tỷ lệ gold non-binding ~30% (trên các op có thể non-binding; `remove_stop` luôn binding) là tham số thiết kế (spec 08 §3), vì tỷ lệ lỗi non-binding (C1') phụ thuộc vào nó. Thêm 07/11.
- [ ] **P3** · Mục VII (Limitations, câu 1 trong 4 câu của Phase 5 Step 5.2, gộp với kết quả shift theo trạm): các yêu cầu cùng tuyến phụ thuộc nhau (dùng chung snapshot), nên bảo đảm CRC chỉ gần đúng. Nháp: *"Requests on the same route share a snapshot and may be correlated; CRC assumes exchangeable requests, so the guarantee is approximate. Across 100 route-level splits the realized risk stays within α (Table III)."* Nửa câu sau chỉ viết nếu C4 đạt; nếu không đạt thì báo trung thực (spec 13 §14.6). Phụ thuộc nợ P1 "Hỏi GVHD 10/11" ở §5. Thêm 07/11.

### 4. Tham số phải khớp với code của B

- [ ] **P2** · `τ = 1 min`, `ε = max{5 min, 0,02·cost(P*)}` phải khớp `configs/harm.yaml` (`tol_min`, `eps_abs`, `eps_rel`) bản cuối.
- [ ] **P2** · Nếu pilot đổi danh sách loại lệnh hoặc quy tắc lệnh ghép, xem lại đoạn Setting.

### 5. Câu hỏi mở về phương pháp

- [ ] **P1** · **Báo B trước khi làm Task 1.4–1.5:** (06/11) `Plan` có `service_start`, hàm `schedule()`, digest thứ tự + giờ phục vụ, OR-Tools thêm cận dưới `tw_start`, `is_fixed_point`; `build_items` bỏ snapshot không phải fixed point (spec 08 §2.1). (07/11) solver dừng theo `solution_limit`, có `warm_start`; `Infeasible` có lý do `precheck`/`no_solution`; số hạng quá ca; `check_constraints` theo bảng spec 07 §5; `cost` cho harm tính bằng phút, trọng số 1; `HarmLabel` có `rule` R1 > R2 > R3, `late_min`, `tw_violations` (spec 09 v0.5).
- [ ] **P1** · Hỏi GVHD 10/11: dữ liệu chia **theo tuyến** nhưng CRC tính rủi ro **theo yêu cầu**. Các yêu cầu cùng tuyến phụ thuộc nhau, nên giả định "exchangeable" mà mục III nêu có thể không đúng hẳn. Tùy câu trả lời: thêm 1 câu giới hạn ở Mục VII, hoặc đổi đơn vị calibration.
  - **Đề xuất mang tới GVHD (A tạm chốt 07/11): phương án (a)** — giữ CRC theo câu, chia theo tuyến như hiện tại; nêu giả định ở Mục VII; dùng C4 (rủi ro trung bình qua 100 split theo tuyến ≤ α + 0,005) làm kiểm tra thực nghiệm. Không đổi code, spec 12, `CONTRACT.md` §3. Câu hỏi: *"Bọn em giữ CRC theo câu, chia theo tuyến, nêu giả định ở §VII và dùng C4 làm kiểm tra thực nghiệm. Thầy/cô thấy có chấp nhận được không?"*
  - Phương án dự phòng (b), chỉ khi GVHD không chấp nhận: CRC theo tuyến (loss tuyến = tỷ lệ câu gây hại được thực thi), chỉ áp cho CRC chung. Cái giá: ở α = 0,02 chỉ còn ~11 thay vì ~20 câu gây hại được phép trong calibration; CRC theo nhóm `ĉ` gần như không cho lọt câu nào, C5 gần như mất. Đổi sang (b) chạm mục khóa ở `CONTRACT.md` §3, phải theo quy tắc 2.
  - Trả nợ: sau khi GVHD trả lời, ghi quyết định vào nhật ký `docs/CONTENT.md`, rồi xóa nợ này.

### 6. Nhất quán thuật ngữ và ký hiệu (rà khi các mục khác đã viết)

- [ ] **P3** · Ký hiệu: paper chỉ dùng `ĉ` (loại lệnh LLM), không có `c` (bỏ 07/11) — không để `c` lọt lại vào Results; `Solve(·)` thống nhất; thời điểm hiện tại luôn là `$t_{\mathrm{now}}$`.
- [ ] **P3** · Thuật ngữ: *non-executable*, *harmless error*, *non-binding error*, *joint risk*, *coverage* dùng đúng một nghĩa trong toàn bài.

### 7. Văn phong và chính sách

- [ ] **P3** · Đối chiếu giọng văn với 1–3 trang A tự viết trước đây (bước 4 của `unslop-academic-writing`), làm trước khi viết Intro.
- [ ] **P3** · Kiểm tra chính sách khai báo dùng AI của IEEE MOST 2027 (một tuần trước hạn, `paper/NOTES.md`).
