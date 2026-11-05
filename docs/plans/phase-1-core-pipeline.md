# Phase 1 — Pipeline lõi: dữ liệu, DSL, solver, nhãn tác hại (06–08/11)

> Xem `00-README.md` cho Global Constraints và Review Focus.

**Goal:** Với một tuyến thật và một lệnh sửa, hệ thống tính được kế hoạch mới và nhãn tác hại. Ví dụ bệnh viện chạy end-to-end và cho `h = 1`.

**Spec:** `docs/02-specs/05-data-lmrc.md`, `06-edit-dsl.md`, `07-solver.md`, `09-harm-labeling.md`, `docs/03-experiments/14-reproducibility-and-testing.md` §4

## Vấn đề cần giải quyết

Đây là các mảnh không phụ thuộc LLM nhưng mọi thứ sau đều dựa vào: biểu diễn tuyến đang chạy, ngôn ngữ lệnh, cách giải lại tuyến, và định nghĩa "gây hại". Nếu phần này sai thì mọi nhãn của benchmark đều sai, nên mỗi task đều làm theo TDD.

**Song song [PAPER]:** xem cuối file.

---

### Task 1.1: Mô hình dữ liệu và đọc LMRC · **[B]**

**Files:**
- Create: `src/kwd/data/models.py`, `src/kwd/data/lmrc.py`, `tests/data/test_lmrc.py`, `tests/fixtures/lmrc_mini/` (1 tuyến thật cắt còn 12 điểm, chép từ dữ liệu đã tải)

**Interfaces:**
- Produces:
  - `Stop`, `RouteSnapshot` (pydantic, đúng trường ở spec 05 §5, thêm `node_ids: list[str]` = thứ tự hàng/cột của ma trận).
  - `RawRoute` (pydantic): `route_id, station_code, departure_utc: datetime, stops: dict, packages: dict, travel_s: dict[str, dict[str, float]], actual_order: list[str], route_score: str`.
  - `load_route(raw_dir: Path, route_id: str) -> RawRoute`
  - `select_routes(raw_dir: Path, n: int, seed: int) -> list[str]`

- [ ] **Step 1 [CODE]:** Test `test_load_route_mini`: `r = load_route(FIX, "<id>")`; assert `len(r.actual_order) == 12`, `r.actual_order[0]` là depot (type `Station`), `r.travel_s[a][b] > 0`.
- [ ] **Step 2 [CODE]:** Test `test_select_routes_filters_and_is_deterministic`: trên fixture có 3 tuyến (1 Low score, 1 thiếu ma trận, 1 hợp lệ, với ngưỡng số điểm hạ trong test) → trả đúng 1 tuyến; gọi 2 lần cùng seed → kết quả bằng nhau.
- [ ] **Step 3:** Chạy `uv run pytest tests/data -q` → FAIL.
- [ ] **Step 4 [CODE]:** Cài `models.py`, `load_route`, `select_routes` (lọc theo spec 05 §3, lấy mẫu phân tầng theo `station_code`). Chuyển `NanToNullReader` từ `scripts/inspect_lmrc.py` vào `src/kwd/data/jsonstream.py` (kèm test). Đọc `travel_times.json` **một lần** bằng `ijson` và ghi riêng file cho từng tuyến được chọn; không bao giờ nạp nguyên file vào RAM (spec 05 §2).
- [ ] **Step 5:** Test PASS. Commit `feat(data): load and select LMRC routes`.

### Task 1.2: Snapshot tuyến đang chạy và bản hiển thị · **[B]**

**Files:**
- Create: `src/kwd/data/snapshot.py`, `src/kwd/data/render.py`, `src/kwd/data/names.py`, `tests/data/test_snapshot.py`, `tests/fixtures/hospital.json` (snapshot 4 điểm, spec 14 §4)

**Interfaces:**
- Consumes: `RawRoute`.
- Produces:
  - `build_snapshot(raw: RawRoute, rho: float, seed: int, shift_slack_min: int = 60) -> RouteSnapshot`
  - `baseline_arrivals(p: RouteSnapshot) -> dict[str, int]` (đi theo `p.remaining` từ `current_stop` lúc `t_now`)
  - `travel(p: RouteSnapshot) -> np.ndarray` (phút, theo `p.node_ids`)
  - `render_snapshot(p: RouteSnapshot) -> str`
  - `load_fixture_snapshot(name: str) -> RouteSnapshot` (dùng cho test mọi module)

- [ ] **Step 1 [CODE]:** Test `test_snapshot_freezes_prefix`: với `rho=0.25` trên fixture mini → `len(p.done) == 3`, `p.current_stop == p.done[-1]`, `set(p.done).isdisjoint(p.remaining)`.
- [ ] **Step 2 [CODE]:** Test `test_baseline_arrivals_monotone`: arrival tăng dần theo `p.remaining`.
- [ ] **Step 3 [CODE]:** Test `test_display_names_unique_and_seeded`: tên hiển thị duy nhất; cùng seed → cùng tên.
- [ ] **Step 4 [CODE]:** Test `test_render_hospital`: `render_snapshot(load_fixture_snapshot("hospital"))` chứa `"An Binh Hospital"`, `"14:10"`, `"Current time: 13:00"`.
- [ ] **Step 5:** FAIL → cài đặt theo spec 05 §4 (tên giả lấy từ danh sách cố định ~10 loại trong `names.py`; múi giờ theo bảng `station_code` đã kiểm ở Phase 0). Tạo `hospital.json` bằng tay: 4 điểm + depot, ma trận thời gian sao cho ETA đúng 13:20/14:10/14:45/15:25.
- [ ] **Step 6:** PASS. Commit `feat(data): in-service snapshots and renderer`.

### Task 1.3: Edit DSL · **[A]**

**Files:**
- Create: `src/kwd/dsl/models.py`, `src/kwd/dsl/parse.py`, `src/kwd/dsl/canonical.py`, `src/kwd/dsl/render.py`, `tests/dsl/test_parse.py`, `tests/dsl/test_canonical.py`

**Interfaces:**
- Produces:
  - `Edit` (union theo `op`, 7 op ở spec 06 §3), `EditSet(edits: list[Edit], confidence: int | None)`
  - `ParseError(code: str, detail: str)` với `code ∈ {invalid_json, schema, unknown_stop, unknown_zone, done_stop, bad_interval}`
  - `parse_editset(raw: str, p: RouteSnapshot) -> EditSet | ParseError` (trả `EditSet` đã đổi tên → `stop_id`, giờ → giây tính từ lúc xuất phát)
  - `canonical(e: EditSet, p: RouteSnapshot) -> tuple`
  - `equivalent(a: EditSet, b: EditSet, p: RouteSnapshot, tol_min: int = 0) -> bool`
  - `render_editset_en(e: EditSet, p: RouteSnapshot) -> str` (vd. `"Deliver to An Binh Hospital no earlier than 15:00."`)
  - `editset_json_schema() -> dict`

- [ ] **Step 1 [CODE]:** Một test cho mỗi mã lỗi ở spec 06 §4 (`test_parse_error_<code>`).
- [ ] **Step 2 [CODE]:** Review Focus #1: `test_stop_name_normalized` — `" an binh HOSPITAL "` khớp `An Binh Hospital`; `"Binh Hospital"` → `unknown_stop`.
- [ ] **Step 3 [CODE]:** Review Focus #2: `test_time_formats` — `"15:00"`, `"3:00 PM"`, `"3 pm"`, `"3pm"` đều thành cùng một số phút; `"15h"` và `"afternoon"` → `schema`.
- [ ] **Step 4 [CODE]:** `test_deadline_equals_window_end` (spec 06 §7); `test_hospital_wrong_not_equivalent`.
- [ ] **Step 5 [CODE]:** `test_roundtrip`: sinh ngẫu nhiên 1.000 `EditSet` hợp lệ trên fixture, `parse_editset(json.dumps(...)) ` rồi `equivalent(...)` với bản gốc → luôn True.
- [ ] **Step 6:** FAIL → cài đặt. Giờ: `null` start → `t_now`, `null` end → `shift_end`.
- [ ] **Step 7:** PASS. Commit `feat(dsl): edit language, parsing, canonical form`.

### Task 1.4: Solver · **[B]**

**Files:**
- Create: `src/kwd/solver/config.py`, `src/kwd/solver/tsptw.py`, `src/kwd/solver/check.py`, `src/kwd/solver/cache.py`, `tests/solver/test_tsptw.py`, `tests/solver/test_check.py`, `configs/solver.yaml`

**Interfaces:**
- Consumes: `RouteSnapshot`, `EditSet`, `travel()`.
- Produces:
  - `SolverConfig(time_limit_s=3.0, solution_limit: int | None = None, first_solution: str = "PATH_CHEAPEST_ARC", late_penalty=10.0, dev_weight=2.0, shift_penalty=10.0)` — `time_limit_s` và `first_solution` đổi được để chạy kiểm tra V1 (spec 13 §11)
  - `Plan`, `Infeasible` (spec 07 §5); `Plan.digest() -> str`
  - `current_plan(p: RouteSnapshot) -> Plan`
  - `solve(p: RouteSnapshot, e: EditSet | None, cfg: SolverConfig) -> Plan | Infeasible`
  - `check_constraints(p: RouteSnapshot, plan: Plan, e: EditSet, tol_min: int = 1) -> list[Violation]` với `Violation(op: str, stop: str | None, amount_min: float)`
  - `solve_cached(p, e, cfg, cache_dir: Path) -> Plan | Infeasible` (khóa: `snapshot_id` + `canonical(e)` + hash cfg)

- [ ] **Step 1 [CODE]:** `test_empty_edit_keeps_plan`: `solve(hospital, None)` có `cost ≤ cost(current_plan)`.
- [ ] **Step 2 [CODE]:** Một test cho mỗi op: sau `solve`, `check_constraints(p, plan, e) == []`.
- [ ] **Step 3 [CODE]:** `test_hospital_gold_moves_after_15` (arrival ≥ 15:00); `test_hospital_wrong_keeps_plan` (`plan.digest() == current_plan(p).digest()`).
- [ ] **Step 4 [CODE]:** Review Focus #3: `test_conflicting_edits_infeasible` — `set_time_window(H, 15:00, 16:00)` + `deadline(H, 14:00)` → `Infeasible`; `precedence(A,B)` + `precedence(B,A)` → `Infeasible`. Không ném exception.
- [ ] **Step 5 [CODE]:** `test_deterministic`: 3 lần `solve` trên snapshot thật 120 điểm → cùng digest. `test_solve_time`: median ≤ 3 s.
- [ ] **Step 6:** FAIL → cài đặt theo spec 07 §2–§4 (warm start bằng `ReadAssignmentFromRoutes`; `GUIDED_LOCAL_SEARCH`; 1 worker). `check_constraints` tính độc lập với OR-Tools, từ `plan.arrival`.
- [ ] **Step 7:** PASS. Commit `feat(solver): TSPTW re-optimization with edits`.

### Task 1.5: Nhãn tác hại · **[B]**

**Files:**
- Create: `src/kwd/harm/label.py`, `tests/harm/test_label.py`, `configs/harm.yaml`

**Interfaces:**
- Consumes: `solve_cached`, `check_constraints`, `equivalent`.
- Produces:
  - `HarmConfig(eps_abs=5.0, eps_rel=0.02, tol_min=1)`
  - `HarmLabel` (spec 09 §5)
  - `label_item(p: RouteSnapshot, gold: EditSet, pred: EditSet | ParseError, solver_cfg, harm_cfg, cache_dir) -> HarmLabel`

- [ ] **Step 1 [CODE]:** `test_hospital_is_harm_r1_nonbinding` → `h == 1`, `rule == "R1"`, `nonbinding_error is True`.
- [ ] **Step 2 [CODE]:** `test_r2_wrong_stop_removed`; `test_r3_excess_cost` (lệnh thêm precedence vô lý gây đi vòng > ε); `test_equivalent_is_harmless`.
- [ ] **Step 3 [CODE]:** `test_parse_error_not_executed` và `test_infeasible_not_executed` → `executed is False`, `h is None`.
- [ ] **Step 4:** FAIL → cài đặt theo spec 09 §2–§4. PASS. Commit `feat(harm): plan-level harm labels`.

### Task 1.6: Lệnh CLI và kiểm thử end-to-end · **[B]**

**Files:**
- Modify: `src/kwd/cli.py`
- Create: `configs/data.yaml`, `tests/test_e2e_hospital.py`

- [ ] **Step 1 [CODE]:** Thêm `kwd snapshot --config configs/data.yaml` (chọn tuyến, dựng snapshot, ghi `data/interim/snapshots.jsonl` + `.npy`).
- [ ] **Step 2 [CODE]:** `test_e2e_hospital`: fixture + gold + lệnh sai → `label_item` cho `h = 1`; lệnh đúng cho `h = 0`.
- [ ] **Step 3 [EXP]:** Chạy `kwd snapshot` cho 30 tuyến pilot. In thống kê spec 05 §7: số điểm/tuyến, % điểm có khung giờ. Chạy 2 lần, so hash file → bằng nhau.
- [ ] **Step 4:** Commit `feat(cli): snapshot command and e2e test`.

---

## Song song [PAPER] (06–08/11)

- [ ] **[PAPER] [A]** Viết nháp `03-problem.tex` (~0,75 trang) từ `MoTaDeTai.md` §2 và spec 09: ký hiệu `P, q, e*, ê, P̂, P*, h, s, λ, α, μ`; định nghĩa harm R1–R3; rủi ro kết hợp `E[1{s≤λ}h] ≤ α`; rủi ro theo loại; cận coverage oracle `1 − max(0, μ − α)`. Không có số liệu.
- [ ] **[READ] [A]** Đọc lại CRC (P11) Thm. 1 và Prop. 1 để viết đúng điều kiện đơn điệu; ghi trích dẫn vào section.
- [ ] Commit `paper: draft problem formulation`.

## Kết thúc Phase 1 khi

- [ ] `uv run pytest -q` pass toàn bộ, gồm `test_e2e_hospital`.
- [ ] Có snapshot cho 30 tuyến pilot.
- [ ] `03-problem.tex` có bản nháp đầy đủ.
