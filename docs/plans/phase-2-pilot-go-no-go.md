# Phase 2 — Pilot và quyết định Go / No-go (08–10/11)

> Xem `00-README.md` cho Global Constraints và Review Focus.

**Goal:** Chạy pilot khoảng 300 câu × 2 mô hình dịch (M1, M2) để trả lời 2 câu hỏi sống còn: LLM có sai đủ nhiều không (H1), và tín hiệu solver có hơn tín hiệu LLM không (H2). Đo chi phí thật mỗi câu. Kết thúc bằng quyết định **Go / No-go** và **đóng băng tín hiệu** ngày 10/11.

**Spec:** `docs/02-specs/08-benchmark-generation.md`, `10-llm-translation.md`, `11-verification-signals.md`, `docs/03-experiments/13-experiment-protocol.md` §2

## Vấn đề cần giải quyết

Rủi ro lớn nhất của đề tài: LLM gần như không sai khi câu rõ ràng (ReOpt-LLM đạt 100% update correctness). Nếu tỷ lệ gây hại `μ` < α thì không còn gì để kiểm soát. Phải biết sớm, trước khi đầu tư vào benchmark lớn. Pilot chỉ cần bản rút gọn: sinh câu, gọi LLM, gán nhãn, và 5 tín hiệu rẻ.

---

### Task 2.1: LLM client có cache · **[A]**

**Files:**
- Create: `src/kwd/llm/client.py`, `src/kwd/llm/cache.py`, `tests/llm/test_client.py`, `configs/llm.yaml`

**Interfaces:**
- Produces:
  - `Completion(text: str, mean_logprob: float | None, prompt_tokens: int, completion_tokens: int, latency_s: float)`
  - `LLMClient` (Protocol): `complete(system: str, user: str, *, temperature: float, seed: int, json_mode: bool = True) -> Completion`
  - `OpenAICompatClient(base_url: str, model: str, api_key_env: str)` — dùng được cho hầu hết nhà cung cấp
  - `CachedClient(inner: LLMClient, cache_dir: Path)`; `StubClient(responses: dict[str, str])` (cho test)

- [ ] **Step 1 [CODE]:** `test_cache_hit_no_second_call`: bọc một client đếm số lần gọi; gọi 2 lần cùng tham số → đếm = 1, kết quả giống hệt.
- [ ] **Step 2 [CODE]:** `test_cache_key_includes_temperature_and_seed`: đổi `seed` → gọi lại.
- [ ] **Step 3:** FAIL → cài đặt (khóa `sha256` theo spec 10 §5, lưu file JSON trong `data/cache/llm/`). Có retry khi lỗi mạng (3 lần, chờ tăng dần).
- [ ] **Step 4:** PASS. Commit `feat(llm): cached OpenAI-compatible client`.

### Task 2.2: Dịch yêu cầu thành lệnh · **[A]**

**Files:**
- Create: `src/kwd/llm/prompts/translate_v1.txt`, `src/kwd/llm/translate.py`, `tests/llm/test_translate.py`
- Modify: `src/kwd/cli.py` (lệnh `kwd translate`)

**Interfaces:**
- Consumes: `LLMClient`, `render_snapshot`, `parse_editset`, `editset_json_schema`.
- Produces:
  - `Prediction` (spec 10 §6)
  - `translate(p: RouteSnapshot, q: str, client: LLMClient, k: int = 4, seed: int = 0) -> Prediction`
  - `translate_items(items: list[BenchmarkItem], snapshots: dict[str, RouteSnapshot], client: LLMClient, k: int, out_path: Path, max_usd: float) -> RunSummary` với `RunSummary(n_done: int, n_skipped: int, usd: float, stopped_by_budget: bool)`

- [ ] **Step 1 [CODE]:** `test_translate_with_stub`: `StubClient` trả JSON đúng cho greedy và 4 mẫu (trong đó 1 mẫu JSON hỏng) → `pred.greedy` là `EditSet`; `pred.samples` có đúng 1 `None`; `pred.verbalized_conf == 0.8` khi `confidence: 80`.
- [ ] **Step 2:** FAIL → cài đặt prompt theo spec 10 §3 (snapshot đặt trước, câu yêu cầu đặt cuối để tận dụng prompt caching); greedy `temperature=0`, mẫu `temperature=0.7`, seed `= seed + i`. Thêm `test_budget_guard`: client giả báo chi phí vượt `max_usd` → `translate_items` dừng và ghi rõ lý do.
- [ ] **Step 3 [CODE]:** `kwd translate --model <name> --items <file> --out runs/<id>/predictions/<model>.jsonl`, chạy tiếp được khi bị ngắt (bỏ qua item đã có); cuối lệnh in tổng token, chi phí ước tính và latency trung bình.
- [ ] **Step 4:** PASS. Commit `feat(llm): translate requests to edit sets`.

### Task 2.3: Sinh benchmark pilot · **[A — B không xem]**

**Files:**
- Create: `src/kwd/bench/gold.py`, `src/kwd/bench/templates.py`, `src/kwd/bench/resolve.py`, `src/kwd/bench/paraphrase.py`, `src/kwd/bench/build.py`, `tests/bench/test_gold.py`, `tests/bench/test_templates.py`, `configs/bench.yaml`
- Modify: `src/kwd/cli.py` (lệnh `kwd bench`)

**Interfaces:**
- Produces:
  - `BenchmarkItem` (spec 08 §7)
  - `sample_gold(p: RouteSnapshot, op: str, want_binding: bool, rng: np.random.Generator, n_ops: int = 1) -> EditSet | None`
  - `verbalize(e: EditSet, p: RouteSnapshot, level: int, rng) -> tuple[str, str]` (câu, `template_id`)
  - `unique_reference(p: RouteSnapshot, stop_id: str) -> str | None` (vd. `"the hospital"` nếu chỉ còn một bệnh viện)
  - `paraphrase(q: str, client: LLMClient, seed: int) -> str`
  - `build_items(snapshots, cfg, paraphraser: LLMClient, judge: LLMClient) -> list[BenchmarkItem]`

- [ ] **Step 1 [CODE]:** `test_gold_feasible_and_binding_flag`: 200 lần `sample_gold` → mọi gold giải được; với `want_binding=True` thì `solve` làm đổi digest, với `False` thì không đổi.
- [ ] **Step 2 [CODE]:** `test_level2_reference_unique`: khi có 2 bệnh viện, `unique_reference` không trả `"the hospital"`.
- [ ] **Step 3 [CODE]:** `test_templates_cover_all_ops_levels`: mỗi cặp (op, level) có ≥ 2 template; câu sinh ra chứa đúng giờ (dạng `3 pm` hoặc `15:00`) hoặc cụm thời gian tương đối đúng.
- [ ] **Step 4:** FAIL → cài đặt theo spec 08 §3–§5. Mỗi op cần **ít nhất 3 template** cho mỗi mức. Mức 3 ghép 2–3 op. Paraphrase kiểm tra nghĩa bằng judge so `q` với `q_template` (không lọc bằng cách dịch ngược).
- [ ] **Step 5:** PASS. Commit `feat(bench): gold sampling, templates, paraphrase`.
- [ ] **Step 6 [EXP]:** `kwd bench --config configs/bench.yaml --set pilot` → khoảng 300 câu trên 30 tuyến, tỷ lệ mức 1/2/3 là 20/40/40. Đọc tay 30 câu ngẫu nhiên: câu có tự nhiên không, gold có đúng ý không. Sửa template nếu sai.

### Task 2.4: Toàn bộ tín hiệu solver (S1–S5) và hai tín hiệu LLM rẻ (L1, L3) · **[A]**

**Files:**
- Create: `src/kwd/signals/solver_signals.py`, `src/kwd/signals/llm_signals.py`, `src/kwd/signals/counter.py`, `tests/signals/test_signals.py`, `tests/signals/test_isolation.py`

**Interfaces:**
- Consumes: `Prediction`, `solve_cached`, `check_constraints`, `equivalent`.
- Produces:
  - `counter_readings(e: EditSet, p: RouteSnapshot, max_n: int = 4) -> list[EditSet]` (spec 11 §2.1)
  - `mentions(q: str, p: RouteSnapshot) -> set[str]` (tên, loại, zone xuất hiện trong câu)
  - `solver_signals(p, q, pred, solver_cfg, cache_dir) -> dict[str, float]` (đủ `S1`, `S2_changed`, `S2_dmax`, `S2_dtravel`, `S3_flag`, `S3_frac`, `S4_disagree`, `S4_dcost`, `S5_jaccard`)
  - `llm_signals(pred, p) -> dict[str, float | None]` (pilot: `L1`, `L3`)

- [ ] **Step 1 [CODE]:** `test_hospital_signals`: lệnh sai → `S1 == 1`, `S3_flag == 1`, `S2_changed == 0`. `test_s5_scope_mismatch`: câu nói "pharmacy", lệnh nhắm "school" → `S5_jaccard == 1.0`.
- [ ] **Step 2 [CODE]:** `test_counter_readings_flip_window`: `[a, b]` sinh ra `[t_now, a]` hoặc `[b, shift_end]`; tối đa 4; thứ tự cố định.
- [ ] **Step 3 [CODE]:** Review Focus #4: `test_all_samples_failed` → `L1 == 0.0`, `S4_disagree == 1.0`, không lỗi chia 0.
- [ ] **Step 4 [CODE]:** `test_signals_do_not_import_harm`: dùng `ast` duyệt mọi file trong `src/kwd/signals/`, không có `import kwd.harm`; schema đầu vào không có trường `gold`.
- [ ] **Step 5:** FAIL → cài đặt → PASS. Commit `feat(signals): solver signals S1-S5 and L1, L3`.

### Task 2.5: Chạy pilot (E0) và ra quyết định · **[A; Step 1 do B]**

**Files:**
- Create: `src/kwd/eval/metrics.py` (`auroc_ci(score, y, groups, n_boot=1000, seed=0) -> (float, float, float)` bootstrap theo tuyến), `src/kwd/eval/pilot_report.py`, `configs/exp/e0.yaml`, `tests/eval/test_metrics.py`
- Modify: `src/kwd/cli.py` (`kwd label`, `kwd signals`, `kwd report --exp e0`)

- [ ] **Step 1 [CODE]:** `test_auroc_ci_perfect` (điểm tách hoàn hảo → AUROC = 1); `test_auroc_ci_random` (≈ 0,5 ± 0,1 trên 2.000 điểm ngẫu nhiên). Cài đặt → PASS.
- [ ] **Step 2 [EXP]:** Chạy `kwd translate` cho M1 và M2 → `kwd label` → `kwd signals` (S1–S5, L1, L3).
- [ ] **Step 3 [EXP]:** `kwd report --exp e0` sinh `runs/<id>/e0_report.md` có đủ mục ở spec 13 §2: `μ` theo mô hình × mức và theo op; tỷ lệ lỗi parse và infeasible; tỷ lệ lỗi không binding; AUROC (CI 95%) của S1–S5 so với L3; coverage tối đa theo α; **chi phí thật mỗi câu cho từng mô hình** và ước tính chi phí bản chính.
- [ ] **Step 4 [DECIDE]: Go / No-go (10/11).** Go khi (1) ở mức 2–3, `μ ≥ 3–5%` với ít nhất 1 mô hình và lớn hơn rõ α dự kiến; và (2) ít nhất 1 tín hiệu solver có AUROC cao hơn L3 (CI không chồng lấn hoặc hơn ≥ 0,05). Nếu No-go: thử theo thứ tự (a) nhấn mạnh mô hình nhỏ, (b) tăng câu ghép khó ở mức 3, chạy lại pilot trong 1 ngày; nếu vẫn thất bại, chuyển đề tài dự phòng (`MoTaDeTai.md` §6.2).
- [ ] **Step 5 [DECIDE]:** Chốt danh sách 6–8 op (bỏ op gần như không bao giờ sai). Chốt kích thước benchmark chính (mặc định ~3.000) và `k` (mặc định 4) theo chi phí thật; nếu vượt ngân sách thì giảm theo spec 15 §3. Sửa spec 06 §3 và spec 10 §5.
- [ ] **Step 5a [DECIDE] — Chốt `α_main`:** giá trị lớn nhất trong `{0,01; 0,02; 0,05; 0,10}` mà ≤ `μ` của M1 ở mức 2–3 chia 2 (spec 13 §14.0). Ghi vào `configs/risk.yaml` và `CONTENT.md` §6.
- [ ] **Step 5b [DECIDE] — Đóng băng tín hiệu solver:** chốt định nghĩa S1–S5 và quy tắc counter-reading (phần đóng góp). Commit riêng `exp: freeze solver signal definitions`, ghi hash commit vào `docs/CONTENT.md` §6. Từ đây không sửa tín hiệu dựa trên kết quả benchmark chính hay tập người viết (kiểm tra V3). Các baseline L2, L4–L6, G1 (Phase 3) chỉ được thiết kế và chỉnh trên **dữ liệu pilot**, rồi cũng đóng băng trước khi chạy bản chính.
- [ ] **Step 5c [GVHD] (10/11, ~20 phút):** GVHD đọc `e0_report.md` và trả lời: có nên làm tiếp không, có số liệu nào đáng ngờ không. Quyết định Go/No-go chỉ chốt sau khi có ý kiến GVHD.
- [ ] **Step 6:** Ghi quyết định vào `docs/CONTENT.md` §6. Commit `exp: pilot E0 and go/no-go decision`.

---

## Song song [READ] / [PAPER] (08–10/11)

- [ ] **[READ] [B]** Đọc toàn văn ConformalNL2LTL (arXiv 2504.21022); ghi 3–5 dòng khác biệt vào `paper/NOTES.md`.
- [ ] **[READ] [B]** Đọc CORA (P21) Eq. 3 và phần HR/mHR; Role-Stratified CRC (P22) phần cận `α·p_r`. Ghi câu trích để dùng ở Related Work và Method.
- [ ] **[READ] [B]** Tra IEEE Xplore và ACM DL với các chuỗi ở `MoTaDeTai.md` §8. Có công trình trùng thì ghi vào `paper/NOTES.md` và báo ngay (có thể ảnh hưởng claim).
- [ ] **[READ] [B]** Kiểm tra bản NeurIPS 2026 camera-ready của ReOpt-LLM: câu "validator does not perform a separate semantic check" và Table 8.4; sửa số trang trong `refs.bib` hoặc ghi chú.

## Kết thúc Phase 2 khi

- [ ] Có `e0_report.md` và quyết định Go / No-go đã ghi lại.
- [ ] Danh sách op và mô hình đã chốt.
- [ ] `paper/NOTES.md` có ghi chú từ các bài đã đọc và kết quả tra cứu.
