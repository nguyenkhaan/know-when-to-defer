# Phase 5 — Viết hoàn thiện paper (23–28/11)

> Xem `00-README.md` cho Global Constraints. Kết quả đã khóa ngày 22/11: không chạy thí nghiệm mới.

**Goal:** Từ các bản nháp có sẵn, hoàn thành paper 8 trang: Results, Limitations, Conclusion, Introduction bản cuối, Abstract, tiêu đề. Có 2 lượt đọc soát và 1 ngày dự phòng.

**Spec:** `docs/01-research/03-paper-outline.md`, `docs/01-research/02-research-questions-and-claims.md`, `paper/NOTES.md`

## Vấn đề cần giải quyết

Đã có kết quả và các section rời, nhưng chưa thành một câu chuyện liền mạch. Ba lỗi hay gặp:

- quá 8 trang, vì references tính vào giới hạn;
- claim mạnh hơn số liệu;
- ký hiệu không thống nhất giữa các section.

Abstract và Introduction phải viết **sau** Results để khớp với những gì thực sự tìm được. Phase này có 6 ngày (thay vì 4 như bản trước) nhờ khóa kết quả sớm hơn.

## Lịch

| Ngày | Việc |
|---|---|
| 23/11 | Results hoàn chỉnh; Limitations; Conclusion |
| 24/11 | Introduction bản cuối; Abstract; tiêu đề; keywords |
| 25/11 | Ép về 8 trang |
| 26/11 | Đọc soát lượt 1: nội dung và số liệu |
| 27/11 | Đọc soát lượt 2: hình, bảng, ngôn ngữ; bản ổn định gửi người đọc độc lập |
| 28/11 | **Dự phòng**: sửa phần còn tồn đọng |

---

### Step 5.1 [PAPER] — Results (23/11, ~1,75 trang trong mục VI) · **[A]**

Mỗi đoạn mở đầu bằng câu kết luận, sau đó mới đến số liệu (macro từ `paper/macros/results.tex`):

- [ ] **E1 · LLM sai bao nhiêu (RQ1):** `μ` theo mức mơ hồ (T1); tỷ lệ lỗi vô hại (lý do cần nhãn mức kế hoạch); tỷ lệ lỗi không binding (lý do kiểm tra khả thi là không đủ).
- [ ] **E2 + E4 · Tín hiệu nào hiệu quả (RQ2, đóng góp chính):** T2 + F2. Thêm tín hiệu solver làm AURC/coverage cải thiện bao nhiêu so với `LLM`; so với bộ chấm học `LEARNED` và judge xem thay đổi kế hoạch `L6`; mức cải thiện trên nhóm không binding.
- [ ] **E7 · Lỗi thật nào được bắt:** T4 + 1 ví dụ ngắn. Loại lỗi nào tín hiệu solver bắt tốt, loại nào không.
- [ ] **E3 · CRC và giá trị vận hành (RQ3):** T3 + F3. Giữ α trên split ngẫu nhiên; ngưỡng chung vi phạm ở loại nào; hiệu chỉnh theo loại mất bao nhiêu coverage; **tác hại được tránh** trên 1.000 yêu cầu ở `α_main`.
- [ ] **E5 + E6 · Shift và câu người viết:** 3–4 câu cùng các dòng shift/human trong T2, T3. Nói thẳng khi bảo đảm bị vỡ.
- [ ] Mỗi claim phải có trong doc 02 §2 và trỏ đúng bảng hoặc hình. Claim đánh dấu "sửa/bỏ" trong `paper/NOTES.md` thì viết lại cho đúng mức.
- [ ] Commit `paper: results`.

### Step 5.2 [PAPER] — Limitations và Conclusion (23/11, ~0,3 trang) · **[A; B góp Limitations]**

- [ ] Limitations (5 ý, mỗi ý một câu):
  1. benchmark chính là câu tổng hợp; tập người viết nhỏ (~200 câu, 2 người viết);
  2. chỉ một xe;
  3. giả định exchangeable và kết quả shift;
  4. kết quả phụ thuộc mô hình và nhà cung cấp API cụ thể;
  5. tín hiệu S3 dựa trên các quy tắc counter-reading viết tay.
- [ ] Conclusion (3–4 câu): bài toán; đóng góp chính; một hướng tiếp theo (cập nhật ngưỡng online khi người chỉ kiểm tra ngẫu nhiên).
- [ ] Commit `paper: limitations and conclusion`.

### Step 5.3 [PAPER] — Introduction bản cuối (24/11, ~0,8 trang) · **[A]**

Năm đoạn:

1. **Bối cảnh:** điều phối viên sửa tuyến bằng ngôn ngữ tự nhiên; LLM + solver làm được việc này (P1, P4).
2. **Vấn đề:** ví dụ bệnh viện. Lệnh sai nhưng vẫn khả thi, tuyến không đổi, không bộ kiểm tra nào báo lỗi. Trỏ Hình F1.
3. **Khoảng trống:** validator chỉ kiểm tra khả thi (P4); verifier cần gold (P3); risk control hiện có chấm theo từng hành động (P21), không theo kế hoạch.
4. **Cách làm:** tác hại mức kế hoạch; dùng solver như máy thử nghiệm; CRC chọn ngưỡng.
5. **Đóng góp:** 3 gạch đầu dòng, mỗi dòng có 1 con số thật; 1 câu tóm tắt kết quả, gồm cả kết quả trên câu người viết.

- [ ] Không dùng "first", "novel". Đối chiếu `docs/04-delivery/16-submission-checklist.md` §4.
- [ ] Commit `paper: final introduction`.

### Step 5.4 [PAPER] — Abstract, tiêu đề, keywords (24/11) · **[A]**

- [ ] Abstract 150–200 từ, 6 câu:
  1. bối cảnh;
  2. vấn đề lệnh sai mà vẫn khả thi;
  3. tác hại mức kế hoạch + benchmark LMRC + tập người viết;
  4. tín hiệu solver + CRC;
  5. kết quả chính có số liệu;
  6. ý nghĩa.
- [ ] Tiêu đề: giữ *Know When to Defer: Risk-Controlled Execution of LLM-Translated Dispatcher Edits for Last-Mile Route Re-planning* nếu vừa 2 dòng; nếu không, rút gọn phần sau dấu hai chấm.
- [ ] `\begin{IEEEkeywords}`: large language models, last-mile delivery, route re-optimization, conformal risk control, selective execution, human-in-the-loop.
- [ ] Commit `paper: abstract and title`.

### Step 5.5 [PAPER] — Ép về đúng 8 trang (25/11) · **[A + B]**

- [ ] `make pages`. Nếu quá 8 trang, cắt theo thứ tự sau và dừng ngay khi đủ:
  1. rút câu thừa ở Related Work và Method;
  2. bỏ F3, giữ số theo loại trong T3;
  3. rút T1 chỉ còn các dòng tổng;
  4. đưa T4 thành 2 câu trong Results;
  5. rút danh mục tham khảo còn khoảng 25 mục;
  6. thu nhỏ F1.
- [ ] Không chỉnh margin, cỡ chữ hay khoảng cách dòng của template.
- [ ] Commit `paper: fit to 8 pages`.

### Step 5.6 [PAPER] — Đọc soát lượt 1: nội dung và số liệu (26/11) · **[đọc chéo: A đọc phần B viết, B đọc phần A viết]**

- [ ] **Ký hiệu:** `P, q, e*, ê, P̂, P*, h, s, λ, α, μ` nhất quán, được định nghĩa trước khi dùng.
- [ ] **Số liệu:** mọi con số trong chữ là macro. Tìm số gõ tay bằng `grep -nE '[0-9]+\.[0-9]+\\?%' paper/sections/*.tex`.
- [ ] **Claim:** đối chiếu từng claim với doc 02 §2.
- [ ] **Trích dẫn:** không có `[?]`; có P21 (CORA), P22, P4 bản NeurIPS.
- [ ] Commit `paper: content pass`.

### Step 5.7 [PAPER] — Đọc soát lượt 2: hình, bảng, ngôn ngữ (27/11) · **[B: hình, bảng; A: ngôn ngữ]**

- [ ] Mỗi hình và bảng được nhắc trong chữ trước khi xuất hiện; caption đọc riêng vẫn hiểu.
- [ ] Hình đọc được khi in đen trắng; chữ trong hình ≥ 8 pt.
- [ ] Chính tả và ngữ pháp: dùng extension kiểm tra chính tả trong VS Code (ví dụ Code Spell Checker hoặc LTeX); câu ngắn, dùng thì hiện tại.
- [ ] Xuất bản ổn định `paper/build/main.pdf` gửi **GVHD** và chạy **AI reviewer** ở phiên mới (Phase 6, Step 6.1) **ngay trong ngày 27/11**.
- [ ] Commit `paper: language and figure pass`.

### Step 5.8 — Dự phòng (28/11) · **[A + B]**

- [ ] Sửa các điểm còn tồn đọng. Nếu không còn gì: bắt đầu sớm Phase 6, Step 6.2 (phát hành code ẩn danh).

## Kết thúc Phase 5 khi

- [ ] `make check` pass (≤ 8 trang); không có cảnh báo LaTeX về tham chiếu chưa định nghĩa.
- [ ] Mọi claim trong paper khớp doc 02 và có bảng hoặc hình chống đỡ.
- [ ] Bản PDF ổn định đã gửi người đọc độc lập.
