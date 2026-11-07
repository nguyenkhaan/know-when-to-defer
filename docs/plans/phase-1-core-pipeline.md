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

- [X] **Step 1 [CODE]:** Test `test_load_route_mini`: `r = load_route(FIX, "<id>")`; assert `len(r.actual_order) == 12`, `r.actual_order[0]` là depot (type `Station`), `r.travel_s[a][b] > 0`.
- [X] **Step 2 [CODE]:** Test `test_select_routes_filters_and_is_deterministic`: trên fixture có 3 tuyến (1 Low score, 1 thiếu ma trận, 1 hợp lệ, với ngưỡng số điểm hạ trong test) → trả đúng 1 tuyến; gọi 2 lần cùng seed → kết quả bằng nhau.
- [X] **Step 3:** Chạy `uv run pytest tests/data -q` → FAIL.
- [X] **Step 4 [CODE]:** Cài `models.py`, `load_route`, `select_routes` (lọc theo spec 05 §3, lấy mẫu phân tầng theo `station_code`). Chuyển `NanToNullReader` từ `scripts/inspect_lmrc.py` vào `src/kwd/data/jsonstream.py` (kèm test). Đọc `travel_times.json` **một lần** bằng `ijson` và ghi riêng file cho từng tuyến được chọn; không bao giờ nạp nguyên file vào RAM (spec 05 §2).
- [X] **Step 5:** Test PASS. Commit `feat(data): load and select LMRC routes`.

### Task 1.2: Snapshot tuyến đang chạy và bản hiển thị · **[B]**

**Files:**

- Create: `src/kwd/data/snapshot.py`, `src/kwd/data/render.py`, `src/kwd/data/names.py`, `tests/data/test_snapshot.py`, `tests/fixtures/hospital.json` (snapshot 4 điểm, spec 14 §4)

**Interfaces:**

- Consumes: `RawRoute`.
- Produces:
  - `build_snapshot(raw: RawRoute, rho: float, seed: int, shift_slack_min: int = 60) -> RouteSnapshot`
  - `baseline_arrivals(p: RouteSnapshot) -> dict[str, int]` (đi theo `p.remaining` từ `current_stop` lúc `t_now`)
  - `travel(p: RouteSnapshot) -> np.ndarray` (giây, `int64`, theo `p.node_ids`)
  - `render_snapshot(p: RouteSnapshot) -> str`
  - `load_fixture_snapshot(name: str) -> RouteSnapshot` (dùng cho test mọi module)

- [X] **Step 1 [CODE]:** Test `test_snapshot_freezes_prefix`: với `rho=0.25` trên fixture mini → `len(p.done) == 3`, `p.current_stop == p.done[-1]`, `set(p.done).isdisjoint(p.remaining)`.
- [X] **Step 2 [CODE]:** Test `test_baseline_arrivals_monotone`: arrival tăng dần theo `p.remaining`.
- [X] **Step 3 [CODE]:** Test `test_display_names_unique_and_seeded`: tên hiển thị duy nhất; cùng seed → cùng tên.
- [X] **Step 4 [CODE]:** Test `test_render_hospital`: `render_snapshot(load_fixture_snapshot("hospital"))` chứa `"Green Valley Hospital"`, `"14:10"`, `"Current time: 13:00"`.
- [X] **Step 5:** FAIL → cài đặt theo spec 05 §4 (tên giả lấy từ danh sách cố định ~10 loại trong `names.py`; múi giờ theo bảng `station_code` đã kiểm ở Phase 0). Tạo `hospital.json` bằng tay: 4 điểm + depot, ma trận thời gian sao cho ETA đúng 13:20/14:10/14:45/15:25.
- [X] **Step 6:** PASS. Commit `feat(data): in-service snapshots and renderer`.

### Task 1.3: Edit DSL · **[A]**

**Files:**

- Create: `src/kwd/dsl/models.py`, `src/kwd/dsl/parse.py`, `src/kwd/dsl/canonical.py`, `src/kwd/dsl/render.py`, `tests/dsl/test_parse.py`, `tests/dsl/test_canonical.py`

**Interfaces:**

- Produces:
  - `Edit` (union theo `op`, 6 op ở spec 06 §3; `service_time` bỏ ngày 07/11), `EditSet(edits: list[Edit], confidence: int | None)`
  - `ParseError(code: str, detail: str)` với `code ∈ {invalid_json, schema, unknown_stop, unknown_zone, done_stop, bad_interval}`
  - `parse_editset(raw: str, p: RouteSnapshot) -> EditSet | ParseError` (trả `EditSet` đã đổi tên → `stop_id`, giờ → giây tính từ lúc xuất phát)
  - `canonical(e: EditSet, p: RouteSnapshot) -> tuple`
  - `equivalent(a: EditSet, b: EditSet, p: RouteSnapshot, tol_min: int = 0) -> bool`
  - `render_editset_en(e: EditSet, p: RouteSnapshot) -> str` (vd. `"Deliver to Green Valley Hospital no earlier than 15:00."`)
  - `editset_json_schema() -> dict`
  - `op_type(e: EditSet, p: RouteSnapshot) -> str` (spec 06 §5.1): tính trên dạng chuẩn hóa; một thao tác → tên thao tác (`deadline` → `"set_time_window"`); từ hai thao tác trở lên (kể cả cùng loại) → `"compound"`. Hàm dùng chung cho `ĉ = op_type(ê)` (Phase 4, CRC theo nhóm) và `c = op_type(e*)` (gold, spec 08, phân tích lỗi).

- [X] **Step 1 [CODE]:** Một test cho mỗi mã lỗi ở spec 06 §4 (`test_parse_error_<code>`).
- [X] **Step 2 [CODE]:** Review Focus #1: `test_stop_name_normalized` — `" green valley HOSPITAL "` khớp `Green Valley Hospital`; `"Valley Hospital"` → `unknown_stop`.
- [X] **Step 3 [CODE]:** Review Focus #2: `test_time_formats` — `"15:00"`, `"3:00 PM"`, `"3 pm"`, `"3pm"` đều thành cùng một số phút; `"15h"` và `"afternoon"` → `schema`.
- [X] **Step 4 [CODE]:** `test_deadline_equals_window_end` (spec 06 §7); `test_hospital_wrong_not_equivalent`; `test_op_type_deadline_canonical` (`deadline(X, 15:00)` → `"set_time_window"`); `test_op_type_compound` (hai `set_time_window` cho hai điểm → `"compound"`; một `remove_stop` → `"remove_stop"`).
- [X] **Step 5 [CODE]:** `test_roundtrip`: sinh ngẫu nhiên 1.000 `EditSet` hợp lệ trên fixture, `parse_editset(json.dumps(...)) ` rồi `equivalent(...)` với bản gốc → luôn True.
- [X] **Step 6:** FAIL → cài đặt. Giờ: `null` start → `t_now`, `null` end → `shift_end`.
- [X] **Step 7:** PASS. Commit `feat(dsl): edit language, parsing, canonical form`.

### Task 1.4: Solver · **[B]**

**Files:**

- Create: `src/kwd/solver/config.py`, `src/kwd/solver/tsptw.py`, `src/kwd/solver/check.py`, `src/kwd/solver/cache.py`, `tests/solver/test_tsptw.py`, `tests/solver/test_check.py`, `configs/solver.yaml`

**Interfaces:**

- Consumes: `RouteSnapshot`, `EditSet`, `travel()`.
- Produces:
  - `SolverConfig(solution_limit: int = 100, time_limit_s: float = 10.0, warm_start: bool = True, first_solution: str = "PATH_CHEAPEST_ARC", late_penalty=10.0, shift_penalty=10.0, dev_weight=2.0)` — `solution_limit` là điểm dừng chính, chỉnh trong task này sao cho median ≤ 3 s trên 150 điểm rồi ghi vào `configs/solver.yaml`; `time_limit_s` chỉ là chốt an toàn (spec 07 §4). `solution_limit`, `warm_start` và `first_solution` đổi được để chạy kiểm tra V1 (spec 13 §11). Các trọng số phạt chỉ dùng khi tìm kiếm; cost cho harm dùng phút, trọng số 1 (spec 09 §2)
  - `Plan`, `Infeasible` (spec 07 §5); `Plan.digest() -> str` (băm thứ tự **và** `service_start` làm tròn phút, cùng `end_time`; quyết định 06/11)
  - `schedule(p: RouteSnapshot, sequence: list[str], e: EditSet | None) -> tuple[dict[str, int], dict[str, int], int]` (`arrival`, `service_start`, `end_time`; spec 07 §5). Mọi giờ trong `Plan` lấy từ hàm này, không đọc cumul của OR-Tools; dùng lại `travel()` và quy tắc đi tuyến của spec 05 §4.
  - `current_plan(p: RouteSnapshot) -> Plan` (= `schedule(p, p.remaining, None)`)
  - `is_fixed_point(p: RouteSnapshot, cfg: SolverConfig) -> bool` (= `solve(p, None, cfg).digest() == current_plan(p).digest()`; bộ lọc snapshot của spec 08 §2.1)
  - `solve(p: RouteSnapshot, e: EditSet | None, cfg: SolverConfig) -> Plan | Infeasible`
  - `check_constraints(p: RouteSnapshot, plan: Plan, e: EditSet, tol_min: int = 1) -> list[Violation]` với `Violation(op: str, stop: str | None, amount_min: float)`; mức vi phạm từng op theo bảng ở spec 07 §5
  - `solve_cached(p, e, cfg, cache_dir: Path) -> Plan | Infeasible` (khóa: `snapshot_id` + `canonical(e)` + hash cfg)

- [X] **Step 1 [CODE]:** `test_empty_edit_keeps_plan`: `solve(hospital, None)` có hàm mục tiêu solver (spec 07 §3) ≤ của `current_plan`; `is_fixed_point(hospital, cfg)` là True.
- [X] **Step 2 [CODE]:** Một test cho mỗi op: sau `solve`, `check_constraints(p, plan, e) == []`.
- [X] **Step 3 [CODE]:** `test_hospital_gold_moves_after_15` (`service_start` của bệnh viện ≥ 15:00); `test_hospital_wrong_keeps_plan` (`plan.digest() == current_plan(p).digest()`).
- [X] **Step 4 [CODE]:** Review Focus #3: `test_conflicting_edits_infeasible` — `set_time_window(H, 15:00, 16:00)` + `deadline(H, 14:00)` → `Infeasible`; `precedence(A,B)` + `precedence(B,A)` → `Infeasible(reason="precheck")`. Không ném exception.
- [X] **Step 5 [CODE]:** `test_deterministic`: 3 lần `solve` trên snapshot thật 120 điểm, và 3 lần chia cho 4 process chạy song song → cùng digest; không lần nào dừng vì `time_limit_s`. `test_solve_time`: median ≤ 3 s. `test_current_plan_matches_baseline`: `current_plan(p).arrival == baseline_arrivals(p)`. `test_digest_detects_wait_only_change`: giữ nguyên thứ tự, thêm `set_time_window` có `start` muộn hơn giờ phục vụ hiện tại của một điểm → digest khác `current_plan`; `start` sớm hơn → digest bằng.
- [X] **Step 6:** FAIL → cài đặt theo spec 07 §2–§4 (warm start bằng `ReadAssignmentFromRoutes`; `GUIDED_LOCAL_SEARCH`; 1 worker). `check_constraints` tính độc lập với OR-Tools, từ `plan.service_start`.
- [X] **Step 7:** PASS. Commit `feat(solver): TSPTW re-optimization with edits`.

### Task 1.5: Nhãn tác hại · **[B]**

**Files:**

- Create: `src/kwd/harm/label.py`, `tests/harm/test_label.py`, `configs/harm.yaml`

**Interfaces:**

- Consumes: `solve_cached`, `check_constraints`, `equivalent`.
- Produces:
  - `HarmConfig(eps_abs=5.0, eps_rel=0.02, tol_min=1)`
  - `HarmLabel` (spec 09 §5)
  - `label_item(item_id: str, model: str, p: RouteSnapshot, gold: EditSet, pred: EditSet | ParseError, solver_cfg, harm_cfg, cache_dir) -> HarmLabel` (cost tính bằng phút, trọng số 1; `rule` theo thứ tự R1 > R2 > R3; `late_min`, `tw_violations` theo spec 09 §4)

- [X] **Step 1 [CODE]:** `test_hospital_is_harm_r1_nonbinding` → `h == 1`, `rule == "R1"`, `nonbinding_error is True`.
- [X] **Step 2 [CODE]:** `test_r2_wrong_stop_removed`; `test_r3_excess_cost` (lệnh thêm precedence vô lý gây đi vòng > ε); `test_equivalent_is_harmless`; `test_rule_precedence` (R1 và R3 cùng kích hoạt → `rule = "R1"`); `test_cost_in_minutes` (thêm 1 phút trễ → `delta_cost` tăng 1, không phải 10); `test_late_min_and_tw_violations_zero_when_equal_to_gold`.
- [X] **Step 3 [CODE]:** `test_parse_error_not_executed` và `test_infeasible_not_executed` → `executed is False`, `h is None`.
- [X] **Step 4:** FAIL → cài đặt theo spec 09 §2–§4. PASS. Commit `feat(harm): plan-level harm labels`.

### Task 1.6: Lệnh CLI và kiểm thử end-to-end · **[B]**

**Files:**

- Modify: `src/kwd/cli.py`
- Create: `configs/data.yaml`, `tests/test_e2e_hospital.py`

- [X] **Step 1 [CODE]:** Thêm `kwd snapshot --config configs/data.yaml` (chọn tuyến, dựng snapshot, ghi `data/interim/snapshots.jsonl` + `.npy`).
- [X] **Step 2 [CODE]:** `test_e2e_hospital`: fixture + gold + lệnh sai → `label_item` cho `h = 1`; lệnh đúng cho `h = 0`.
- [X] **Step 3 [EXP]:** Chạy `kwd snapshot` cho 30 tuyến pilot. In thống kê spec 05 §7: số điểm/tuyến, % điểm có khung giờ. Chạy 2 lần, so hash file → bằng nhau.
- [ ] **Step 4:** Commit `feat(cli): snapshot command and e2e test`.

---

## Song song [PAPER] (06–08/11)

- [X] **[PAPER] [A]** Viết nháp `03-problem.tex` (~0,75 trang) từ `MoTaDeTai.md` §2 và spec 09: ký hiệu `P, q, e*, ê, P̂, P*, h, s, λ, α, μ`; định nghĩa harm R1–R3; rủi ro kết hợp `E[1{s≤λ}h] ≤ α`; rủi ro theo loại; điều kiện áp CRC Thm. 1 (đổi biến `θ = −λ`, `λ = −∞` có loss 0; spec 12 §2.1); cận coverage oracle `1 − π − max(0, μ − α)` với `π` là tỷ lệ lệnh không thực thi được. Không có số liệu.
- [X] **[READ] [A]** Đọc lại CRC (P11) Thm. 1 và Prop. 1 để viết đúng điều kiện đơn điệu; ghi trích dẫn vào section.
- [X] Commit `paper: draft problem formulation`. (Xong 06/11: commit `9a87b93`. Bản nháp 4 đoạn: bối cảnh, tác hại R1–R3, quy tắc quyết định + CRC (ngưỡng theo `ĉ`), cận coverage; ~520 từ, vượt ngân sách ~0,75 trang, cắt khi có PDF đủ trang.)

## Kết thúc Phase 1 khi

- [X] `uv run pytest -q` pass toàn bộ, gồm `test_e2e_hospital`.
- [X] Có snapshot cho 30 tuyến pilot.
- [X] `03-problem.tex` có bản nháp đầy đủ.
