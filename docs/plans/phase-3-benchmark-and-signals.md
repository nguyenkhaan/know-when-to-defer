# Phase 3 — Benchmark chính, tập câu người viết, baseline mạnh (11–16/11)

> Xem `00-README.md` cho Global Constraints và Review Focus. Chỉ bắt đầu khi Phase 2 ra quyết định **Go**.

**Goal:** Có benchmark chính ~3.000 câu đã kiểm duyệt, tập ~200 câu do 2 người viết, bản dịch của M1 và M2, đủ tín hiệu kèm hai baseline mạnh (G1, L6), mô hình điểm rủi ro, và kiểm tra độ ổn định nhãn V1. Paper có nháp Related Work, Method, Benchmark, Hình F1, Intro v0.

**Spec:** `docs/02-specs/08-benchmark-generation.md` (§9 tập người viết), `10-llm-translation.md`, `11-verification-signals.md`, `docs/03-experiments/13-experiment-protocol.md` §9, §11

## Vấn đề cần giải quyết

Pilot chỉ đủ để quyết định có làm tiếp hay không. Để reviewer tin kết quả, cần:

1. **Dữ liệu đủ lớn** để chia 100 lần calibration/test theo tuyến.
2. **Ngôn ngữ thật**: một tập nhỏ câu do người viết, để trả lời câu hỏi "câu máy sinh có dễ hơn thực tế không?".
3. **Baseline mạnh**: một bộ chấm học có giám sát (G1, kiểu CORA) và một LLM judge được xem thay đổi kế hoạch (L6), để so sánh công bằng với tín hiệu solver.
4. **Nhãn đáng tin**: kiểm tra nhãn không đổi khi cho solver chạy lâu hơn (V1).

Việc của người (kiểm duyệt, viết câu) chạy song song với việc code. Cần nhờ người từ ngày 11/11.

---

### Task 3.1: Sinh benchmark chính · **[A — B không xem tới 13/11]**

**Files:**
- Modify: `configs/bench.yaml` (thêm `set: main`, ~300 tuyến, ~10 câu/tuyến, mỗi ô op × mức ≥ 100 câu)
- Create: `src/kwd/bench/stats.py`, `tests/bench/test_build_reproducible.py`

**Interfaces:**
- Produces: `data/benchmark/main/items.jsonl`, `data/benchmark/main/README.md`; `bench_stats(items: list[BenchmarkItem]) -> pd.DataFrame`.

- [ ] **Step 1 [CODE]:** `test_build_reproducible`: chạy `build_items` 2 lần trên 3 snapshot (paraphrase qua `StubClient`) → hai file giống hệt từng byte.
- [ ] **Step 2 [CODE]:** Cài `bench_stats` (số câu theo op × mức, % binding, độ dài câu trung bình). PASS. Commit `feat(bench): stats and reproducibility test`.
- [ ] **Step 3 [EXP]:** `kwd snapshot` cho ~300 tuyến (không trùng tuyến pilot và tuyến của tập người viết) → `kwd bench --set main`. Kiểm tra `README.md`: mỗi ô ≥ 100 câu, binding ≈ 70%, tổng ~3.000; số tuyến bị loại vì không phải fixed point (spec 08 §2.1) và bao nhiêu trong đó đang trễ khung giờ gốc. Nếu > 20% thì báo A trước khi chạy dịch.

### Task 3.2: Tập câu do người viết (E6) · **[A soạn thẻ + kiểm tra; B, C viết]**

**Files:**
- Create: `scripts/make_intent_cards.py`, `scripts/collect_human_items.py`, `data/benchmark/human/cards/*.md`, `data/benchmark/human/items.jsonl`

**Interfaces:**
- Consumes: `sample_gold`, `render_snapshot`, `render_editset_en`.
- Produces: `BenchmarkItem` với `level = 0`, thêm trường `writer_id: str`.

- [ ] **Step 1 [CODE] [A]:** `make_intent_cards.py --routes 40 --n 200 --seed 7`: dùng ~40 tuyến riêng (không thuộc main, pilot); sinh gold theo cùng tỷ lệ op, ~50 lệnh ghép. Mỗi thẻ là một file markdown gồm bảng tuyến rút gọn có đánh dấu điểm liên quan, và một **tình huống** (có thể viết tiếng Việt, ví dụ "Bệnh viện gọi: hôm nay 15:00 bàn nhận hàng mới mở"). A viết sẵn 6–8 mẫu tình huống cho mỗi loại lệnh. **Không** ghi câu tiếng Anh nêu lệnh lên thẻ; gold nằm trong file riêng mà người viết không xem.
- [ ] **Step 2 [HUMAN] [B, C] (11–13/11):** B và C mỗi người viết ~100 thẻ, làm độc lập, không trao đổi câu với nhau. B chưa được xem code, cấu hình hay dữ liệu benchmark (quy tắc "mù template", `00-README.md`). Hướng dẫn: *"Viết tin nhắn bạn sẽ gõ cho trợ lý điều phối. Tự nhiên, ngắn, mơ hồ hay viết tắt đều được."* Người viết không được xem template hay câu paraphrase.
- [ ] **Step 3 [HUMAN] [A]:** A đọc tuyến + câu (không xem thẻ) và trả lời: *thẻ có phải là một cách hiểu hợp lý của câu không?* (`yes`/`no`). Chỉ giữ câu `yes`; báo tỷ lệ giữ lại.
- [ ] **Step 4 [CODE]:** `collect_human_items.py` gộp câu + thẻ thành `items.jsonl`; test `test_human_items_valid`: mỗi item có gold khả thi, có `writer_id`, tuyến không thuộc main hay pilot.
- [ ] **Step 5:** Commit `exp: human-written test set`. Mục tiêu 200 câu, tối thiểu 150 câu được giữ; báo tỷ lệ giữ theo từng người viết. Nếu tới 13/11 có dưới 150 câu: xem spec 15 §3.

### Task 3.3: Kiểm duyệt 300 câu benchmark chính · **[A + B (B làm sau khi xong 3.2)]**

**Files:**
- Create: `scripts/review_items.py`, `data/benchmark/main/review_<annotator>.csv`, `src/kwd/eval/agreement.py` (`cohen_kappa(a: list[str], b: list[str]) -> float`), `tests/eval/test_agreement.py`

- [ ] **Step 1 [CODE]:** `test_kappa_known_values` (2 dãy giống hệt → 1,0; một ví dụ tính tay). Cài `cohen_kappa`.
- [ ] **Step 2 [CODE]:** `review_items.py --n 300 --seed 0 --annotator A`: lấy mẫu phân tầng op × mức; in tuyến rút gọn, câu `q`, gold dạng câu; nhận `y`/`n`/`a`; ghi CSV; dừng được và chạy tiếp được.
- [ ] **Step 3 [HUMAN] [A, B]:** A và B duyệt độc lập (mỗi người ~2–3 giờ). B chỉ bắt đầu sau khi đã nộp xong câu human (Task 3.2). Tính κ và % "yes".
- [ ] **Step 4 [EXP]:** Câu cả hai cùng chấm "no" → sửa template hoặc luật sinh, sinh lại các câu bị ảnh hưởng. Mục tiêu ≥ 90% "yes". Ghi vào `data/benchmark/main/README.md`. Commit `exp: human review of benchmark`.

### Task 3.4: Baseline L2, L4, L5, L6 và G1 · **[A]**

**Files:**
- Create: `src/kwd/signals/judge.py`, `src/kwd/signals/guardian.py`, `src/kwd/llm/prompts/judge_backtranslation_v1.txt`, `judge_edit_v1.txt`, `judge_edit_diff_v1.txt`, `tests/signals/test_baselines.py`
- Modify: `src/kwd/signals/llm_signals.py`

**Interfaces:**
- Produces:
  - `backtranslation_score(q: str, e: EditSet, p: RouteSnapshot, judge: LLMClient) -> float | None` (L2, 0–1)
  - `edit_judge_score(q: str, e: EditSet, p: RouteSnapshot, judge: LLMClient) -> float | None` (L5, xác suất lệnh sai)
  - `plan_diff_summary(p: RouteSnapshot, before: Plan, after: Plan, e: EditSet) -> str` (ETA trước → sau của các điểm được nhắc, số vị trí đổi, Δtravel)
  - `diff_judge_score(q: str, e: EditSet, p: RouteSnapshot, diff: str, judge: LLMClient) -> float | None` (L6)
  - `Guardian.fit(texts: list[str], h: np.ndarray) -> Guardian`; `Guardian.predict(texts: list[str]) -> np.ndarray` (G1; embedding M5 + logistic regression; text = `q + " || " + render_editset_en(ê)`)

- [ ] **Step 1 [CODE]:** `test_judges_with_stub`: judge trả `"85"` → 0,85; trả rác → `None`. `test_judge_model_differs`: cấu hình judge trùng mô hình dịch của cùng hàng → báo lỗi ngay khi khởi động.
- [ ] **Step 2 [CODE]:** `test_plan_diff_hospital`: lệnh sai → chuỗi diff chứa `"An Binh Hospital: 14:10 → 14:10"` và `"changed positions: 0"`.
- [ ] **Step 3 [CODE]:** `test_guardian_learns`: 200 câu giả, `h = 1` khi text chứa `"before"` → AUROC > 0,9; `test_guardian_uses_fit_only`: hàm huấn luyện từ chối dữ liệu có `route_id` ngoài `fit_routes`.
- [ ] **Step 4:** FAIL → cài đặt theo spec 11 §3, §3b → PASS. Thiết kế và chỉnh prompt judge **chỉ trên dữ liệu pilot**, rồi commit `feat(signals): baselines L2 L4 L5 L6 G1` và ghi hash commit (đóng băng baseline).

### Task 3.5: Dịch, gán nhãn, tính tín hiệu và V1 · **[A; Step 3 (V1) do B]**

- [ ] **Step 1 [EXP]:** `kwd translate` cho M1 và M2 trên main + human (để chạy nền, có `max_usd`). Sau 500 câu đầu: so chi phí thật với ước tính; vượt thì giảm theo spec 15 §3.
- [ ] **Step 2 [EXP]:** `kwd label` cho mọi dự đoán; in tỷ lệ lỗi parse và infeasible.
- [ ] **Step 3 [EXP] — V1:** chọn ngẫu nhiên 500 câu, giải lại `P*` và `P̂` với `time_limit_s × 2` và `first_solution="SAVINGS"`, gán nhãn lại. Tỷ lệ nhãn đổi phải < 1%. Không đạt → xử lý theo spec 13 §11 **trước** khi sang Phase 4.
- [ ] **Step 4 [EXP]:** `kwd signals` (S1–S5, L1–L6) cho main và human. 100% câu được thực thi có đủ tín hiệu (chỉ L4 được thiếu với M2).

### Task 3.6: Chia dữ liệu và mô hình điểm · **[B]**

**Files:**
- Create: `src/kwd/risk/splits.py`, `src/kwd/signals/score.py`, `tests/risk/test_splits.py`, `tests/signals/test_score.py`, `configs/signals.yaml`

**Interfaces:**
- Produces:
  - `Splits(fit_routes: list[str], cal_test: list[tuple[list[str], list[str]]])`
  - `make_splits(route_ids: list[str], n_splits: int = 100, fit_frac: float = 0.3, seed: int = 0) -> Splits`
  - `FEATURE_SETS: dict[str, list[str]]` (`LLM`, `LEARNED`, `L6`, `SOLVER`, `ALL`, `ALL+`, và các biến thể bỏ-một, spec 11 §4)
  - `fit_score(df: pd.DataFrame, features: list[str]) -> ScoreModel`; `ScoreModel.predict(df) -> np.ndarray`

- [ ] **Step 1 [CODE]:** `test_splits_by_route`: không tuyến nào vừa ở `fit` vừa ở `cal_test`, không tuyến nào vừa ở cal vừa ở test của cùng split; cùng seed → cùng kết quả.
- [ ] **Step 2 [CODE]:** `test_score_learns_signal`: dữ liệu giả có `h` phụ thuộc mạnh vào `S1` → AUROC của `fit_score([S1])` > 0,9; cột thiếu được điền trung vị và thêm cột chỉ báo thiếu.
- [ ] **Step 3:** FAIL → cài đặt (logistic regression L2, chuẩn hóa) → PASS. Commit `feat(risk): route-level splits and score model`.
- [ ] **Step 4 [EXP]:** Huấn luyện G1 và mọi bộ đặc trưng × M1, M2 trên `fit_routes`; lưu điểm cho các tuyến còn lại và cho tập human vào `runs/<id>/scores.parquet`. Xem nhanh AUROC; ghi nhận xét vào `CONTENT.md` §6.

---

## Song song [PAPER] (11–16/11)

- [ ] **[PAPER] [B]** `02-related-work.tex` (~0,75 trang): từ bản nháp `MoTaDeTai.md` §10 và ghi chú đọc ở Phase 2. Đoạn 1: LLM tái tối ưu (P1, P4, P3, P5, P8). Đoạn 2: risk control cho hành động LLM (P11–P14, P21, P22, P24). Câu cuối: khác biệt là tác hại mức kế hoạch + tín hiệu solver không cần gold.
- [ ] **[PAPER] [A]** `04-method.tex` (~1,25 trang): DSL (1 đoạn); solver (1 đoạn); **tín hiệu solver S1–S5 (phần dài nhất, công thức ngắn cho S3, S4)**; tín hiệu LLM và baseline G1, L6 (1 đoạn); gộp điểm; CRC chung và theo loại (công thức `λ̂`).
- [ ] **[PAPER] [B, từ 14/11]** `05-benchmark.tex` (~0,75 trang): LMRC, dựng snapshot, gold trước câu, 3 mức mơ hồ (mỗi mức 1 ví dụ), paraphrase, kiểm duyệt (κ, % yes), **tập người viết** (cách thu thập, số người, tỷ lệ giữ lại).
- [ ] **[PAPER] [B]** Hình F1 (1 cột): pipeline + ví dụ bệnh viện. Vẽ bằng TikZ ngay trong VS Code, hoặc draw.io xuất PDF vào `paper/figures/f1_pipeline.pdf`.
- [ ] **[PAPER] [A]** `01-introduction.tex` v0: bối cảnh → ví dụ bệnh viện → khoảng trống → cách làm → 3 đóng góp (con số để trống).
- [ ] Sau mỗi section: `make check` và ghi số trang. Commit `paper: draft <section>`.

## Kết thúc Phase 3 khi (M2 · 16/11)

- [ ] Main ≥ 3.000 câu (hoặc số đã chốt theo ngân sách), đã kiểm duyệt, có κ; tập human ≥ 120 câu.
- [ ] V1 đạt (< 1% nhãn đổi).
- [ ] Bảng tín hiệu S1–S5, L1–L6, G1 và điểm cho M1, M2 trên main và human.
- [ ] Paper có nháp: Intro v0, Related Work, Problem, Method, Benchmark, F1.
