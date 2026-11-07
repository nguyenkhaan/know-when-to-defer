# CONTENT · Mục lục nghiên cứu

**Đề tài:** *Know When to Defer: Risk-Controlled Execution of LLM-Translated Dispatcher Edits for Last-Mile Route Re-planning*
**Hội nghị:** IEEE MOST 2027 · hạn nộp **01/12/2026** (mục tiêu nội bộ 30/11) · 8 trang tính cả references · double-blind
**Cập nhật:** 07/11/2026

## 1. Đọc gì trước

| Bạn là | Đọc theo thứ tự |
|---|---|
| Người mới vào dự án | `DienGiaiYTuong.md` → `MoTaCuTheThucNghiem.md` → 01 → 02 → 15 |
| Người viết code (người hoặc AI agent) | `plans/00-README.md` → phase đang làm → spec được phase đó trỏ tới (05–14) |
| Người chạy thí nghiệm | `MoTaCuTheThucNghiem.md` → 02 → 13 → 12 → 14 |
| Người viết paper | `CONTRACT.md` → `../debit-last-submit.md` → 02 → 03 → 16 → `MoTaDeTai.md` (§5, §9, §10) |

## 2. Cây tài liệu

```
docs/
├── CONTENT.md                              # mục lục này
├── MoTaDeTai.md                            # mô tả học thuật đầy đủ, 24 tài liệu tham khảo (nguồn sự thật về nội dung)
├── DienGiaiYTuong.md                       # diễn giải ý tưởng dễ đọc, kèm ví dụ
├── MoTaCuTheThucNghiem.md                  # mô tả từng bước thực nghiệm: làm gì, đo gì, tiêu chí đạt
├── 00-overview/
│   └── 01-project-brief.md                 # dự án là gì, mục tiêu, phạm vi, thuật ngữ
├── 01-research/
│   ├── 02-research-questions-and-claims.md # RQ, giả thuyết, bản đồ claim → bằng chứng
│   └── 03-paper-outline.md                 # ngân sách 8 trang, hình và bảng
├── 02-specs/                               # (tiếng Anh, cho người và AI agent viết code)
│   ├── 04-architecture.md                  # luồng dữ liệu, module, repo, công nghệ
│   ├── 05-data-lmrc.md                     # LMRC → snapshot tuyến đang chạy
│   ├── 06-edit-dsl.md                      # ngôn ngữ lệnh JSON, kiểm tra, so sánh tương đương
│   ├── 07-solver.md                        # OR-Tools TSPTW, áp lệnh, tất định
│   ├── 08-benchmark-generation.md          # gold trước câu, 3 mức mơ hồ, kiểm duyệt
│   ├── 09-harm-labeling.md                 # nhãn tác hại mức kế hoạch (đóng góp C1)
│   ├── 10-llm-translation.md               # prompt, mô hình, lấy mẫu, cache
│   ├── 11-verification-signals.md          # tín hiệu solver và LLM, điểm rủi ro (đóng góp chính C3)
│   └── 12-risk-control.md                  # CRC chung và theo loại lệnh, cách chia dữ liệu
├── 03-experiments/                         # (tiếng Anh)
│   ├── 13-experiment-protocol.md           # E0 pilot, E1–E7, kiểm tra V1–V3, baseline, chỉ số
│   └── 14-reproducibility-and-testing.md   # run, config, cache, test, phát hành ẩn danh
├── 04-delivery/
│   ├── 15-roadmap.md                       # kế hoạch 4 tuần, mốc quyết định, rủi ro
│   └── 16-submission-checklist.md          # yêu cầu IEEE MOST 2027, double-blind, ngày nộp
└── plans/                                  # kế hoạch triển khai từng bước (code + thí nghiệm + paper)
    ├── 00-README.md                        # tổng quan phase, 2 luồng song song, ràng buộc chung
    ├── phase-0-setup.md                    # 05–06/11 · repo, dữ liệu, LLM, template paper
    ├── phase-0b-smoke-test.md              # 06–07/11 · kiểm tra nhanh: LLM có dịch sai đủ nhiều không
    ├── phase-1-core-pipeline.md            # 06–08/11 · snapshot, DSL, solver, nhãn tác hại
    ├── phase-2-pilot-go-no-go.md           # 08–10/11 · pilot, quyết định Go/No-go
    ├── phase-3-benchmark-and-signals.md    # 11–16/11 · benchmark chính, tập người viết, baseline mạnh
    ├── phase-4-experiments.md              # 17–22/11 · E1–E7, kiểm tra độ bền, khóa kết quả
    ├── phase-5-paper-writing.md            # 23–28/11 · viết hoàn thiện, ép 8 trang, 2 lượt soát
    └── phase-6-review-and-submit.md        # 29–30/11 · rà soát, ẩn danh, nộp
```

## 3. Bản đồ nhanh: câu hỏi → tài liệu

| Câu hỏi | Xem |
|---|---|
| "Gây hại" được định nghĩa thế nào? | 09 §2 |
| Lệnh DSL có những loại nào? | 06 §3 |
| Điểm rủi ro tính từ đâu? | 11 §2–§4 |
| Chọn ngưỡng `λ` thế nào? | 12 §2 |
| Khi nào dừng đề tài (go/no-go)? | `plans/phase-0b-smoke-test.md` (báo động sớm), 13 §3, 15 §2 |
| Paper cần những bảng và hình nào? | `CONTRACT.md` §4 ("Reported results"), 03 §2, 13 §1 |
| Ví dụ kiểm thử chuẩn (bệnh viện) ở đâu? | 14 §4 |
| Yêu cầu nộp bài? | 16 |

## 4. Ba tài liệu tổng hợp (tiếng Việt, cho người đọc)

| File | Vai trò |
|---|---|
| `MoTaDeTai.md` | Mô tả học thuật đầy đủ: định vị, khoảng trống, bảng 24 tài liệu tham khảo, bản nháp Related Work. **Nguồn sự thật về nội dung nghiên cứu.** |
| `DienGiaiYTuong.md` | Bản diễn giải ý tưởng dễ đọc kèm ví dụ |
| `MoTaCuTheThucNghiem.md` | Mô tả từng bước thực nghiệm bằng ngôn ngữ dễ hiểu, có ví dụ: làm gì, đo gì, mục tiêu, cách làm, tiêu chí đạt |

Khi nội dung học thuật thay đổi (claim, RQ, đóng góp), sửa `MoTaDeTai.md` trước, rồi cập nhật 01–03 cho khớp. Khi thực nghiệm thay đổi (spec 08–13, plans), cập nhật `MoTaCuTheThucNghiem.md` theo.

## 4b. Tài liệu ngoài `docs/`

| Thư mục | Vai trò |
|---|---|
| `../reference-documents/` | PDF tài liệu tham khảo (P1–P20) |

## 5. Quy ước

- Mỗi tài liệu có dòng trạng thái (`Draft` / `Approved` / `Frozen`) và ngày cập nhật.
- Spec trong `02-specs/` và `03-experiments/` viết bằng tiếng Anh, mỗi spec kết thúc bằng **tiêu chí hoàn thành**. Code chỉ được coi là xong khi đạt tiêu chí đó.
- Số tài liệu tham khảo dùng mã `[P#]` như trong `MoTaDeTai.md` §9.

## 6. Trạng thái

| Ngày | Ghi chú |
|---|---|
| 05/11/2026 | Tạo bộ tài liệu v0.1 (16 tài liệu). Chưa triển khai code. |
| 05/11/2026 | Tạo kế hoạch triển khai `plans/` (7 phase). Máy không có GPU: mô hình mở gọi qua API. Bước tiếp theo: duyệt kế hoạch, bắt đầu Phase 0. |
| 05/11/2026 | Nâng cấp v0.2: thêm tập câu người viết (E6), phân loại lỗi (E7), kiểm tra độ bền nhãn (V1–V3), baseline G1 và L6, đóng băng tín hiệu sau pilot; còn 5 mô hình, benchmark ~3.000 câu, `k = 4`; khóa kết quả 22/11; paper viết bằng VS Code + TinyTeX. |
| 05/11/2026 | Bổ sung định nghĩa chỉ số và tiêu chí đạt (spec 13 §14); `α_main` chọn từ pilot; fit 30%; tập human ~200 câu (B, C); phân vai A/B/C/GVHD trong `plans/`. |
| 05/11/2026 | Chuyển `MoTaDeTai.md`, `DienGiaiYTuong.md`, `MoTaCuTheThucNghiem.md` vào `docs/`. |
| 05/11/2026 | Task 0.1 xong (chờ commit): package `kwd` (Python 3.12, `uv`), `kwd --help`/`kwd version`, 2 test pass, ruff sạch; `.gitignore` thêm `data/`, `runs/`, file phụ LaTeX. `torch`/`sentence-transformers` để Phase 3. |
| 05/11/2026 | Quyết định (Task 0.5): câu yêu cầu của bộ chính và bộ human bằng **tiếng Anh**; tình huống trên thẻ bộ human được viết tiếng Việt. |
| 05/11/2026 | Task 0.2 xong (chờ commit): LMRC 2,3 GB tải đủ; 6.112 tuyến, 17 trạm / 5 thành phố, 2.571 tuyến đủ điều kiện; kho ở vị trí 0; ~6% điểm có khung giờ. Đổi đơn vị thời gian nội bộ sang **giây** (spec 04 §5). |
| 05/11/2026 | Thêm `plans/phase-0b-smoke-test.md`: kiểm tra nhanh ~50 câu viết tay × M1, M2 ngay sau Task 0.3, để phát hiện sớm rủi ro "LLM gần như không sai". |
| 05/11/2026 | Task 0.3 xong (chờ commit): chốt 5 mô hình qua **OpenRouter**, ngân sách API tổng **10 USD** (8 USD chia cho mô hình + 2 USD dự phòng). M1 `qwen/qwen3.5-9b` (có logprobs; Qwen2.5-7B bị loại vì không có logprobs trên OpenRouter), M2 `deepseek/deepseek-v4-flash` (không phải frontier vì ngân sách), M3 `meta-llama/llama-3.3-70b-instruct`, M4 `openai/gpt-oss-120b` (không dùng bản free Nemotron vì giới hạn 1.000 request/ngày), M5 `bge-small-en-v1.5` CPU. `scripts/ping_models.py`: cả 5 chạy được. Chi tiết: spec 10 §2, `configs/llm.yaml`. |
| 05/11/2026 | **Smoke test (Phase 0b) xong** — chi tiết: `SMOKE_TEST_RESULT.md`. 50 câu viết tay trên 2 tuyến mẫu (R1 do A viết, R2 do Claude soạn và A chỉnh); loại s40, s48 vì câu mơ hồ → 48 câu. Nhãn chấm bằng mắt (Claude chấm tạm, A duyệt). Sai có hại: **M1 18/48 (38%)**, **M2 5/48 (10%)**; R1 và R2 không chênh nhiều. Loại lỗi chính: M1 đổi sang lệnh khác (bỏ điểm thay vì dời giờ), đảo chiều thời gian; M2 chặn cả khu thay vì một điểm. Có lỗi vô hình (tuyến không đổi): M1 3, M2 2. Mọi câu sai có hại đều khai confidence 85–100. M1 hiểu nhầm sáng/chiều 4 câu, bị chặn vì giờ đã qua (cần test `bad_interval` ở Task 1.3; không tự sửa giờ). **Quyết định: làm tiếp Phase 1.** H2 (tín hiệu solver tốt hơn LLM) chưa kiểm tra được, chờ pilot 10/11. |
| 06/11/2026 | Task 0.4 xong: `paper/` dựng theo template IEEE 06/2024 (`IEEEtran.cls` V1.8b copy nguyên; tác giả ẩn danh; 8 section ghi ngân sách trang và thông điệp; `refs.bib` P1–P24, tên tác giả lấy từ PDF/arXiv). TinyTeX cài ở `~/.TinyTeX`, lệnh nằm trong `~/.local/bin`. `make check` pass (1 trang), font nhúng đủ. Thêm `\pagestyle{plain}` vì MOST yêu cầu đánh số trang (spec 16). Paper viết trong VS Code, commit trong repo (Overleaf chỉ làm phương án dự phòng). |

| 06/11/2026 | Task 1.1 xong (nhánh `feat/1.1-lmrc-loader`, chờ duyệt): `kwd.data` có `Stop`, `RouteSnapshot`, `RawRoute`, `select_routes`, `extract_routes`, `load_route`, `NanToNullReader`; fixture `lmrc_mini` 12 điểm. Đo trên dữ liệu thật: **2.571 tuyến đủ điều kiện**, cả 6.112 ma trận đều đầy đủ nên điều kiện ma trận không loại tuyến nào. Ô `0.0` ngoài đường chéo là có thật (7.722 ô), đã ghi vào spec 05 §2. |
| 06/11/2026 | Task 1.2 xong (nhánh `feat/1.2-snapshot`, chờ duyệt cùng Task 1.1): `build_snapshot`, `baseline_arrivals`, `travel` (giây, `int64`), `clock_str`/`clock_to_s`, `render_snapshot`, tên hiển thị có trọng số; fixture bệnh viện thêm 2 khung giờ gốc để lệnh gold thật sự đổi thứ tự (vét cạn 24 thứ tự: 180/196, 196/206, 180/351). `departure_local` đổi sang `HH:MM:SS`. Trên 30 tuyến: còn 43–149 điểm, 2/260 điểm khung giờ đến trễ, render ~6.500 ký tự cho 150 điểm. |

| 06/11/2026 | Chốt 3 chỗ lệch trước khi viết `03-problem.tex`: (1) tác hại có đủ 3 luật R1–R3 theo spec 09 (thêm R2 "sai tập điểm" vào `MoTaDeTai.md` §2.2, `DienGiaiYTuong.md`); (2) cận coverage oracle `1 − π − max(0, μ − α)`, `π` = tỷ lệ lệnh không thực thi được (`MoTaDeTai.md` §2.3, spec 12 §2.4); (3) ghi rõ điều kiện áp CRC Thm. 1: đổi biến `θ = −λ`, lưới ngưỡng luôn có `−∞` (spec 12 §2.1). Còn mở: tính hoán đổi được khi chia theo tuyến nhưng tính rủi ro theo yêu cầu, hỏi GVHD 10/11. |
| 06/11/2026 | Quyết định: CRC theo loại lệnh nhóm theo **loại của lệnh LLM sinh (`ĉ`)**, không theo loại gold `c`, vì lúc triển khai không có gold. Lệnh ghép → nhóm `compound`. Rủi ro theo `c` chỉ báo cáo để phân tích; C5 viết lại theo `ĉ`. Đã sửa `MoTaDeTai.md` §2.3, spec 12 v0.3 §2.2, spec 13 v0.3 §14.3/§14.6, roadmap mốc 14/11, phase 4 Task 4.1. Cần báo B trước Task 4.1 (17/11). |
| 06/11/2026 | Chốt cỡ mẫu cho CRC theo nhóm `ĉ`: (1) `min_n(α) = max(20, ⌈1/α⌉ − 1)` (99 ở α = 0,01; 49 ở 0,02), nhóm dưới ngưỡng bị chuyển duyệt hết và phải báo `deferred_groups`; (2) CRC theo nhóm chạy ở mọi α, T3 luôn có hàng này ở `α_main`; F3 và C5 dùng `α_F3` = α nhỏ nhất ≥ `α_main` mà mọi nhóm đủ mẫu, chọn chỉ từ số mẫu; **không đổi `α_main`**; (3) hàm chung `op_type` (spec 06 §5.1) tính trên dạng chuẩn hóa, dùng cho cả `ĉ` và `c`; spec 08 thêm `gold_type`; (4) `evaluate` tách `group_types` / `gold_types`. Mốc 14/11 chỉ còn: có gộp nhóm nhỏ thành `other` không (mặc định không). Đã sửa spec 06 v0.2, 08 v0.3, 12 v0.5, 13 v0.5, roadmap v0.3, phase 1 Task 1.3, phase 4 Task 4.1, `02-research-questions-and-claims.md` (C5), `03-paper-outline.md` (F3). Cần báo B trước Task 4.1 (17/11). |
| 06/11/2026 | Rà Mục III với tài liệu: (1) bảo đảm theo nhóm sửa thành `E[L(λ_ĉ) \| x = 1, ĉ] ≤ α` (paper, spec 12, `MoTaDeTai.md`); (2) ký hiệu thời điểm hiện tại thống nhất `t_now` ở paper, spec và code; (3) **lỗi non-binding chọn phương án (a)**: `Plan.digest()` băm thứ tự + giờ bắt đầu phục vụ (làm tròn phút) + giờ về kho; mọi giờ trong `Plan` lấy từ hàm chung `schedule()`, không đọc cumul của OR-Tools; OR-Tools thêm cận dưới `tw_start` của khung giờ gốc (spec 07 v0.2; spec 08, 09, 11, 14; Task 1.4). Câu `P̂ = P` trong paper giữ nguyên. Còn mở (P1): trên tuyến thật `solve(P, ê)` có thể đổi thứ tự dù `ê` đã thỏa, cần chốt trước pilot 10/11. Cần báo B trước Task 1.4. |
| 06/11/2026 | Đo `solve(P, ∅)` trên 20 tuyến thật (solver tạm theo spec 07, `dev_weight` 2 phút): **18/20 giữ nguyên kế hoạch**; 1 tuyến solver sửa 9,9 phút trễ khung giờ gốc, 1 tuyến rút ngắn 6,8 phút đường đi. **Quyết định: bộ lọc fixed point**, benchmark chỉ giữ snapshot có `solve(P, ∅).digest == P.digest`; tuyến hỏng thay bằng tuyến dự bị cùng station (spec 05 v0.2 §3, spec 07 §5 `is_fixed_point`, spec 08 v0.4 §2.1, spec 13 E0, Task 1.4, 2.3, 3.x). Paper giữ định nghĩa `P` là thứ tự tài xế thật; Mục V thêm một câu, Mục VII thêm giới hạn. File nợ: từ nay nợ đã trả thì xóa. |
| 07/11/2026 | Task 1.3 xong (chờ commit): `kwd.dsl` có 7 op, `EditSet` (1–4 lệnh), `ParseError` 6 mã, `parse_editset`, `canonical`, `equivalent`, `op_type`, `render_editset_en`, `dump_editset` (JSON ngược của parse), `editset_json_schema` (~4.300 ký tự). 111 test mới, round-trip 1.000 `EditSet` trên 2 snapshot. Chi tiết chưa ghi ở spec 06: (1) `EditSet` giữ `null` và `deadline` như LLM viết, chỉ `canonical` mới đóng cận và đổi `deadline`; (2) `bad_interval` cho **mọi** giờ đã qua, tính theo phút (phút hiện tại vẫn hợp lệ); (3) `schema` cho cửa sổ không có cận nào, `precedence` một điểm với chính nó, `minutes`/`confidence` không phải số nguyên; (4) code fence ```` ``` ```` → `invalid_json`; tên kho `Depot` → `unknown_stop`; điểm xe đang đứng → `done_stop`; (5) `equivalent` với `tol_min` cũng áp cho `service_time` (tính bằng giây). |
| 07/11/2026 | Quyết định: **cân bằng benchmark theo op và theo mức**, bỏ điều kiện "mỗi ô op × mức ≥ 100 câu" (vô lý về số học: mức 1 chỉ 600 câu < 7 op × 100; ô op ở mức 3 không rõ nghĩa với lệnh ghép). Mức 1–2 chỉ có câu một op; mức 3 một nửa lệnh ghép 2–3 op, một nửa câu một op có ý ngầm; bộ chính ~2.400 câu một op + ~600 lệnh ghép. Kiểm tra: mỗi op ≥ 250 câu một op (đủ `min_n(0,02) = 49` câu calibration cho mỗi nhóm `ĉ`, đúng với 6–8 op), mỗi ô op × mức có ≥ 3 template. Đã sửa spec 08 v0.5 §3, §4, §10; Task 2.3 Step 3 (≥ 3 template), Step 4, Step 6; Task 3.1; `MoTaDeTai.md` §4.3; `MoTaCuTheThucNghiem.md` §6.2. Cùng lúc dọn chỗ lỗi thời: op `priority` → `deadline`, `service_time` tính bằng phút (`MoTaDeTai.md` §4.2, `DienGiaiYTuong.md`); quy mô "3.000–6.000" và "LLM 7–14B chạy cục bộ" thay bằng bộ chính ~3.000 và M1/M2 qua API (`MoTaDeTai.md` §4.6, §5, checklist; `MoTaCuTheThucNghiem.md`); tick Task 0.5 Step 1 (R2 đã chốt 06/11). Phương án CRC theo câu (a) tạm chốt, chờ GVHD 10/11 (`debit-last-submit.md` §5). |
| 07/11/2026 | Quyết định: `bad_interval` áp cho **mọi** mốc giờ đã qua (hai cận cửa sổ, `deadline`, `driver_end_time`, `avoid_zone_until`), so theo phút; phút hiện tại vẫn hợp lệ; không bao giờ tự sửa giờ (vd. `03:00` không đọc thành 15:00). Lý do: lỗi giờ đã qua validator nào cũng bắt được, tính vào gây hại sẽ thổi phồng `μ` và làm tín hiệu solver trông mạnh hơn thực tế. Paper chỉ nêu một mệnh đề ở §IV, không tách `bad_interval` thành dòng riêng trong T1. Đã sửa spec 06 v0.3 §4; thêm nợ P2 cho §IV; thêm quy tắc "Keep the paper lean" vào `CLAUDE.md`. Code Task 1.3 đã cài đúng quy tắc này. |
| 07/11/2026 | **Tinh gọn paper (A duyệt, sửa `CONTRACT.md` theo quy tắc 2).** (1) Shift E5 chỉ còn theo trạm, một dòng T3; bỏ shift theo mức, theo op, template → paraphrase (bộ human E6 là phép thử shift thứ hai). (2) T2 chỉ còn 5 bộ điểm (`LLM`, `LEARNED`, `L6`, `SOLVER`, `ALL`) + AUROC S1–S5; bỏ `ALL+`, bỏ AUPRC khỏi paper; bỏ-một và recall nhóm không binding mỗi thứ một câu. (3) Bỏ F3; CRC theo nhóm `ĉ` là một dòng T3 (thêm dòng nếu `α_F3 ≠ α_main`); rủi ro theo loại gold `c` chỉ ở `runs/`, paper không còn ký hiệu `c`. (4) **Cắt LTT**; rủi ro có điều kiện không kiểm soát, chỉ ghi `runs/`; bỏ câu Prop. 1 ở §III. (5) §IV chỉ có công thức `λ̂` và lưới, lập luận liên tục để ở spec 12. (6) E6 gộp hai người viết trong bảng, theo từng người một câu. (7) "Always execute" trùng validator chỉ kiểm tra khả thi; bỏ baseline `s ≤ 0,5` và S3 cắt cứng. (8) Bộ lọc fixed point: một câu ở §V (gồm ý tuyến đang trễ bị loại bớt), §III trỏ tới §V, bỏ ý riêng ở §VII. (9) Giới hạn còn 4 câu. (10) §V chỉ báo κ, % "yes", tỷ lệ giữ câu human. Thêm: độ nhạy ε một mệnh đề trong Setup. Đã sửa: `CONTRACT.md` (§1 `ĉ`/`c`, §3 Target và CRC grid, §4 `α_F3` và dòng mới "Reported results", §6 bỏ LTT); spec 08 v0.6, 09 v0.3, 11 v0.4, 12 v0.6, 13 v0.6; claims v0.3; outline v0.3; roadmap v0.4; Phase 3–5; `MoTaDeTai.md`, `DienGiaiYTuong.md`, `MoTaCuTheThucNghiem.md`; `paper/NOTES.md`; §III (510 từ, trước 525) và chú thích đầu §VI, §VII; file nợ (xóa 2 nợ đã trả hoặc gộp, sửa 5 nợ). |
| 07/11/2026 | Ghi vào spec 06 v0.4 (§4, §5) 4 quy tắc DSL mà code Task 1.3 đã làm: parse giữ nguyên op như LLM viết, chỉ `canonical` mới chuẩn hóa; các ca `schema` (cửa sổ không cận, precedence với chính nó, `minutes`/`confidence` sai); code fence → `invalid_json`, kho → `unknown_stop`, điểm xe đang đứng → `done_stop`; `tol_min` áp cả `service_time`. |
| 07/11/2026 | Quyết định: **bỏ op `service_time`**, DSL còn 6 op (`set_time_window`, `deadline`, `remove_stop`, `precedence`, `driver_end_time`, `avoid_zone_until`). Lý do: `service_time` đổi dữ liệu bài toán chứ không phải ràng buộc lên kế hoạch, nên luật R1 phải tách "thời lượng theo gold, giờ chờ theo `ê`"; bỏ đi thì định nghĩa harm ở §III không có ngoại lệ. Paper §IV thêm một mệnh đề phạm vi. Trả nợ P1 "`service_time` trong R1" (gỡ chặn Task 1.4–1.5). Đã sửa: `kwd.dsl` + test (372 pass); spec 06 v0.5, 07 v0.3, 11 v0.5, 12, 13; Task 1.3; `CONTRACT.md` §6 (danh sách op vẫn chưa khóa, pilot có thể bỏ thêm); `MoTaDeTai.md`, `DienGiaiYTuong.md`, `MoTaCuTheThucNghiem.md`; file nợ. `scripts/smoke_translate.py` giữ nguyên vì là bản ghi smoke test đã chạy. |
| 07/11/2026 | **Hoàn thiện cây tài liệu sau rà soát độc lập (A duyệt 5 quyết định, sửa `CONTRACT.md` theo quy tắc 2).** (a) `α_main` = giá trị lớn nhất trong lưới ≤ `min(μ_M1, μ_M2)/2`, `μ` trên toàn bộ pilot; không đạt → 0,01 và claim của mô hình có `μ ≤ 0,02` chỉ mô tả. (b) `cost` cho harm tính bằng phút, trọng số 1 (di chuyển + trễ + quá ca), để so được với `ε` tính bằng phút; trọng số phạt 10 chỉ dùng khi solver tìm kiếm; §III sửa câu định nghĩa `cost`. (c) Ba phép so sánh chính: `ALL` vs `LLM`, `ALL` vs `LEARNED`, `SOLVER` vs `L6`, mỗi phép có luật trong spec 13 §14.6. (d) Thay recall@20% bằng AUROC trong nhóm kế hoạch không đổi (`P̂ = P`), nơi S1 là hằng số. (e) Shift theo trạm = leave-one-city-out (5 thành phố). Bổ sung spec còn thiếu: solver dừng theo `solution_limit` (tất định), `time_limit_s` chỉ là chốt an toàn; `Infeasible` có lý do `precheck`/`no_solution`; số hạng quá ca trong hàm mục tiêu; `HarmLabel` có `tw_violations`, `late_min` định nghĩa so với `P*`, `rule` theo thứ tự R1 > R2 > R3; `remove_stop` luôn binding; S1–S5 và counter-reading định nghĩa đầy đủ, tất định (sẵn sàng đóng băng 10/11). Sửa: ví dụ bệnh viện viết lệnh sai với cận `null` (viết `00:00` sẽ bị `bad_interval`); op mô tả theo giờ phục vụ ("served", cả docstring schema gửi LLM); bỏ `μ` theo op khỏi H1; AURC ghi rõ là selective; bộ human `level = 0` + `writer_id`, ~40 lệnh ghép, tối thiểu 150 câu; "6–8 op" → tối đa 6; H3 và bản nháp Related Work trong `MoTaDeTai.md` bỏ LTT và tần suất vi phạm; tham chiếu chéo, Python 3.12, `e0…e6`, ngày cập nhật; thêm dòng "spec thắng" vào hai tài liệu diễn giải. Phiên bản: spec 04 v0.2, 05 v0.3, 06 v0.6, 07 v0.4, 08 v0.7, 09 v0.4, 11 v0.6, 13 v0.7, 14 v0.2; claims v0.4. File nợ: xóa nợ hệ số phạt trễ (đã trả), sửa nợ §IV về trọng số solver, thêm nợ §V về tỷ lệ gold non-binding. |
| 07/11/2026 | **Hoàn thiện cây tài liệu theo lượt rà độc lập thứ hai (80/100), A duyệt sửa hết rồi khóa lại `CONTRACT.md`.** Spec: mức vi phạm từng op của `check_constraints` (spec 07 §5, dùng cho R1, S1, `V` ở §III; ràng buộc trên điểm bị bỏ để R2 xử lý); `late_min` cộng theo từng điểm; test solver so **hàm mục tiêu** chứ không phải `cost`; `changed_positions` định nghĩa; `warm_start` để V1 thật sự đổi chiến lược; S5 có danh sách từ chỉ loại điểm, cận mở không bị dời khi tạo counter-reading, zone gần nhất theo khoảng cách Euclid; prompt dùng `editset_json_schema()`; CRC theo nhóm luôn chạy (bỏ chữ "dùng nếu"). Plan: Phase 5 trỏ tới `CONTRACT.md` + file nợ và ghi đúng 3 phép so sánh chính; Phase 6 phát hành theo danh sách cho phép, xóa tác giả trong `pyproject.toml`; `00-README` nhắc đọc file nợ; test bệnh viện kiểm `service_start`. Code: fixture bệnh viện đổi sang tên trung tính (Green Valley Hospital, Cedar Pharmacy, Lincoln School, Harbor Shop), múi giờ America/Chicago, tọa độ Chicago (ma trận không đổi); `render_editset_en` viết "Do not serve…"; 372 test pass. Tài liệu diễn giải: quy tắc `α_main`, bảng T2 ví dụ, tiêu chí C3, S4/L1 theo 4 mẫu, ví dụ Gym, 70/30 kèm ngoại lệ `remove_stop`, tên điểm mới. Phiên bản: spec 06 v0.7, 07 v0.5, 09 v0.5, 10 v0.4, 11 v0.7, 12 v0.7, 13 v0.8. File nợ: cập nhật nợ "báo B trước Task 1.4–1.5" và nợ §V về tỷ lệ non-binding. |
| 07/11/2026 | Task 1.4 (solver) do **A tự làm** (commit `667b331`), không cần bàn giao cho B. File nợ: xóa nợ P1 "Báo B trước khi làm Task 1.4–1.5". |

