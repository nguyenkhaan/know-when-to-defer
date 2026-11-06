# Phase 4 — Thí nghiệm E1–E7, kiểm tra độ bền, bảng và hình tự động (17–22/11)

> Xem `00-README.md` cho Global Constraints và Review Focus.

**Goal:** Có đủ kết quả cho mọi claim trong doc 02, gồm câu do người viết (E6), phân loại lỗi thật (E7) và kiểm tra độ bền (V2, V3). Một lệnh `kwd report` sinh lại mọi bảng, hình và macro số liệu của paper. **Khóa kết quả ngày 22/11.**

**Spec:** `docs/02-specs/12-risk-control.md`, `docs/03-experiments/13-experiment-protocol.md`, `docs/01-research/02-research-questions-and-claims.md`

## Vấn đề cần giải quyết

Đã có dữ liệu và điểm rủi ro, nhưng chưa có câu trả lời cho RQ1–RQ3. Cần:

- cài CRC đúng (code ngắn nhưng dễ sai hướng đơn điệu);
- chạy đủ tổ hợp trên 100 split;
- chứng minh kết quả không phải do "tự ra đề tự giải" (E6, E7, V3);
- biến tất cả thành đúng T1–T4, F2.

Thí nghiệm nào không phục vụ claim nào thì không chạy. Phase này ngắn hơn trước 2 ngày để dành thời gian cho paper.

---

### Task 4.1: CRC chung và theo loại lệnh (17/11) · **[B]**

**Files:**
- Create: `src/kwd/risk/crc.py`, `tests/risk/test_crc.py`, `configs/risk.yaml`

**Interfaces:**
- Produces:
  - `crc_lambda(s: np.ndarray, h: np.ndarray, executable: np.ndarray, alpha: float) -> float` (trả `-np.inf` nếu phải chuyển duyệt hết)
  - `min_n_for(alpha: float) -> int` = `max(20, ⌈1/α⌉ − 1)` (spec 12 §2.2; tính `ceil` có dung sai để `1/0.02` không thành 51).
  - `alpha_f3(group_counts_median: dict[str, int], alpha_main: float, grid: list[float]) -> float | None` (spec 13 §14.0): α nhỏ nhất trong `grid` với `α ≥ alpha_main` và mọi nhóm có `n ≥ min_n_for(α)`; không có → `None`. Chỉ nhận số mẫu, không nhận nhãn.
  - `per_type_lambda(s, h, executable, group_types: np.ndarray, alpha: float, min_n: int | None = None) -> dict[str, float]` (`min_n=None` → `min_n_for(alpha)`). **`group_types` = `op_type(ê)` (`ĉ`, Task 1.3), không phải loại của gold** (spec 12 §2.2, quyết định 06/11).
  - `evaluate(s, h, executable, group_types, gold_types, lam: float | dict[str, float], alpha: float, harm_cost: pd.DataFrame | None = None) -> dict` (coverage, rủi ro kết hợp, rủi ro có điều kiện (chỉ ghi `runs/`), `per_group_risk` theo `ĉ` (được bảo đảm), `per_type_risk_gold` theo `c = op_type(e*)` (chỉ ghi `runs/`, không lên paper), `deferred_groups`, `violated`; nếu có `harm_cost` thì thêm số lần gây hại, phút trễ, khung giờ bị vi phạm đã tránh trên 1.000 yêu cầu). `group_types` dùng để áp ngưỡng; `gold_types` chỉ dùng để báo cáo (spec 13 §14.3).

- [ ] **Step 1 [CODE]:** `test_crc_validity_synthetic`: dữ liệu giả hoán đổi được, `μ = 0,15`; 1.000 split 50/50, α = 0,05 → rủi ro thực tế trung bình ≤ 0,05 + 0,005. (CRC chỉ bảo đảm rủi ro **trung bình**; tần suất vi phạm chỉ báo cáo, không làm tiêu chí test.)
- [ ] **Step 2 [CODE]:** `test_crc_defer_all_when_impossible`: mọi item có hại → `-inf`.
- [ ] **Step 3 [CODE]:** Review Focus #5: `test_per_type_small_n_defers_all` (loại có 10 mẫu, `min_n=20` → `-inf` cho loại đó; loại khác bình thường; không ném lỗi). `test_min_n_depends_on_alpha`: `min_n_for` trả 99, 49, 20, 20 ở α = 0,01; 0,02; 0,05; 0,10; nhóm 60 mẫu không có hại → `-inf` ở α = 0,01, ngưỡng hữu hạn ở α = 0,02. `test_alpha_f3`: số mẫu `{a: 120, b: 30}`, `alpha_main = 0,02` → 0,05; `{a: 120, b: 60}` → 0,02; `{a: 5}` → `None`. `test_gold_types_never_affect_lambda`: hoán vị `gold_types` → `per_type_lambda` và coverage không đổi, chỉ `per_type_risk_gold` đổi.
- [ ] **Step 4 [CODE]:** `test_non_executable_counts_in_denominator`; `test_harm_prevented`: luôn thực thi → 0 tác hại được tránh; chuyển duyệt hết → bằng tổng tác hại.
- [ ] **Step 5:** FAIL → cài đặt theo spec 12 §2.1–§2.2 → PASS. Commit `feat(risk): global and per-type CRC`.

### Task 4.2: Chạy E1–E6 (17–19/11) · **[B; A đọc kết quả]**

**Files:**
- Create: `src/kwd/eval/experiments.py` (`run_e1` … `run_e6`, mỗi hàm trả `pd.DataFrame` và ghi `runs/<id>/e<k>.parquet`), `configs/exp/e1.yaml … e6.yaml`, `tests/eval/test_experiments_smoke.py`

- [ ] **Step 1 [CODE]:** `test_experiments_smoke`: chạy E1–E6 trên benchmark mini 10 câu + human mini 5 câu với `StubClient` → mỗi file kết quả có đủ cột theo spec 12 §4 và spec 13; không có NaN ngoài cột được phép. Cài đặt → PASS. Commit `feat(eval): experiment runners`.
- [ ] **Step 2 [EXP] E1:** `μ`, lỗi chuỗi, lỗi vô hại, lỗi không binding, luật R1/R2/R3 theo mô hình × mức × op.
- [ ] **Step 3 [EXP] E2:** AUROC từng tín hiệu và từng bộ điểm (AUPRC chỉ ghi `runs/`), CI bootstrap theo tuyến; recall ở mức chuyển duyệt 20% trên nhóm lỗi không binding.
- [ ] **Step 4 [EXP] E3:** {`LLM`, `LEARNED`, `L6`, `SOLVER`, `ALL`} × {chung, theo loại} × α ∈ {0,01; 0,02; 0,05; 0,10} × 100 split; thêm **tác hại được tránh** ở `α_main`.
- [ ] **Step 5 [EXP] E4:** Đường risk–coverage và AURC: `LLM`, `LEARNED`, `L6`, `SOLVER`, `ALL`; các biến thể bỏ-một (paper chỉ một câu). Ba so sánh bắt buộc ở spec 13 §7.
- [ ] **Step 6 [EXP] E5:** shift theo trạm: calibrate trên tuyến của một số trạm, test trên trạm còn lại (spec 13 §8).
- [ ] **Step 7 [EXP] E6:** Điểm học trên fit main, CRC calibrate trên cal main, **test trên tập human**: AUROC từng tín hiệu (thứ hạng có giống main không), rủi ro thực tế so với α, coverage, `μ` trên câu người viết.

### Task 4.3: Phân loại lỗi (E7) và kiểm tra V2, V3 (19–20/11) · **[B; Step 3: A gán 100, B gán 30]**

**Files:**
- Create: `scripts/sample_errors.py`, `data/analysis/error_taxonomy_<annotator>.csv`, `src/kwd/eval/taxonomy.py` (`taxonomy_table(labels: pd.DataFrame, scores: pd.DataFrame, top_frac: float = 0.2) -> pd.DataFrame`), `tests/eval/test_taxonomy.py`

- [ ] **Step 1 [CODE]:** `sample_errors.py --n 100 --seed 0`: lấy 100 lỗi gây hại được thực thi trên tuyến **test**, phân tầng theo mô hình × mức; in câu, lệnh LLM, gold (dạng câu), thay đổi kế hoạch; nhận nhãn loại lỗi (`direction_flip`, `wrong_stop`, `missing_part`, `extra_constraint`, `wrong_value`, `other`).
- [ ] **Step 2 [CODE]:** `test_taxonomy_table`: 6 lỗi giả với điểm cho trước → đúng tỷ lệ mỗi loại và đúng % bị bắt (nằm trong top 20% rủi ro) theo `SOLVER`, `LLM`, `ALL`. Cài đặt → PASS.
- [ ] **Step 3 [HUMAN] [A, B]:** A gán nhãn 100 lỗi (~2 giờ); B gán lại 30 lỗi (không xem nhãn của A); tính κ. Chọn 1–2 ví dụ tiêu biểu cho paper.
- [ ] **Step 4 [EXP] — V2:** gán nhãn lại với ε ∈ {0, 5, 10} phút; chạy lại E3 ở `α_main` cho `ALL` và `LLM`. Ghi kết luận có đổi hay không.
- [ ] **Step 5 [EXP] — V3:** ghi vào `paper/RUNS.md` hash và ngày của commit đóng băng tín hiệu và baseline, so với ngày chạy main và human (đóng băng phải có trước).
- [ ] **Step 6:** Commit `exp: error taxonomy and robustness checks`.

### Task 4.4: Sinh bảng, hình và đọc kết quả (20–22/11) · **[B; Step 5 do A]**

**Files:**
- Create: `src/kwd/eval/report.py`, `src/kwd/eval/plots.py`, `tests/eval/test_report.py`, `paper/RUNS.md`
- Modify: `src/kwd/cli.py` (`kwd report --run <id>`)

**Interfaces:**
- Produces: `paper/tables/t1_benchmark.tex`, `t2_signals.tex`, `t3_crc.tex`, `t4_taxonomy.tex`; `paper/figures/f2_risk_coverage.pdf`; `paper/macros/results.tex` (vd. `\newcommand{\muMOneLevelThree}{12.4\%}`, `\newcommand{\lateAvoided}{…}`).

- [ ] **Step 1 [CODE]:** `test_report_outputs`: trên kết quả smoke → sinh đủ 5 file + `results.tex`; mỗi bảng biên dịch được trong một file LaTeX nhỏ (`booktabs`).
- [ ] **Step 2 [CODE]:** Cài đặt. F2 có đường "always execute" và oracle. Hình 1 cột (3,5 in), font ≥ 8 pt, đọc được khi in đen trắng (nét liền/đứt + marker). Bảng `booktabs`, tối đa 6 cột; T2 và T3 có dòng "human".
- [ ] **Step 3:** PASS. Commit `feat(eval): paper tables, figures and macros`.
- [ ] **Step 4 [EXP]:** `kwd report --run <final_id>`; ghi run ID của từng bảng và hình vào `paper/RUNS.md`.
- [ ] **Step 5 [READ]:** Đối chiếu kết quả với bảng claim ở doc 02: claim nào giữ, sửa câu chữ, hay bỏ. **Không** chạy thêm thí nghiệm để "cứu" claim. Ghi vào `paper/NOTES.md`.
- [ ] **Step 5b [GVHD] (22/11, ~30 phút):** GVHD đọc danh sách claim (giữ/sửa/bỏ) cùng T1–T3, F2 và trả lời: claim nào thuyết phục, claim nào nên hạ giọng. A cập nhật `paper/NOTES.md`.
- [ ] **Step 6 [DECIDE] — Khóa kết quả (22/11):** từ đây chỉ sửa lỗi. Nếu phát hiện lỗi làm đổi số liệu: sửa, chạy lại `kwd report`, ghi run ID mới.

---

## Song song [PAPER] (17–22/11)

- [ ] **[PAPER] [B]** `06-experiments.tex` phần **Setup** (~0,5 trang): 5 mô hình và vai trò; `k`; tham số solver; ε; chia dữ liệu (fit 30% tuyến, 100 split 50/50); `α_main`; α; baseline (spec 13 §12); chỉ số; V1–V3 (mỗi mục một mệnh đề; ε gộp vào V2). Viết được trước khi có kết quả.
- [ ] **[PAPER] [B]** Gắn `\input{tables/...}`, `\includegraphics{figures/...}` vào đúng chỗ; dùng macro trong `results.tex` thay vì gõ số.
- [ ] **[PAPER] [A]** Viết nháp Results với số tạm (macro) ngay khi E1–E3 có kết quả (19–20/11), để ngày 23/11 chỉ còn chỉnh.
- [ ] **[PAPER] [A]** Introduction v1: điền con số chính bằng macro (μ, mức cải thiện, tác hại được tránh).
- [ ] `make check` → ghi số trang vào `CONTENT.md` §6. Commit `paper: setup, wiring, results draft`.

## Kết thúc Phase 4 khi (M3 · 22/11)

- [ ] Có kết quả E1–E7, V1–V3 trong `runs/`; `paper/RUNS.md` đầy đủ.
- [ ] `kwd report` sinh T1–T4, F2 và `results.tex` không cần thao tác tay.
- [ ] `paper/NOTES.md` có danh sách claim: giữ / sửa / bỏ.
- [ ] Paper có nháp Results.
