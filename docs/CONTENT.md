# CONTENT · Mục lục nghiên cứu

**Đề tài:** *Know When to Defer: Risk-Controlled Execution of LLM-Translated Dispatcher Edits for Last-Mile Route Re-planning*
**Hội nghị:** IEEE MOST 2027 · hạn nộp **01/12/2026** (mục tiêu nội bộ 30/11) · 8 trang tính cả references · double-blind
**Cập nhật:** 05/11/2026

## 1. Đọc gì trước

| Bạn là | Đọc theo thứ tự |
|---|---|
| Người mới vào dự án | `DienGiaiYTuong.md` → `MoTaCuTheThucNghiem.md` → 01 → 02 → 15 |
| Người viết code (người hoặc AI agent) | `plans/00-README.md` → phase đang làm → spec được phase đó trỏ tới (05–14) |
| Người chạy thí nghiệm | `MoTaCuTheThucNghiem.md` → 02 → 13 → 12 → 14 |
| Người viết paper | 02 → 03 → 16 → `MoTaDeTai.md` (§5, §9, §10) |

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
│   └── 12-risk-control.md                  # CRC chung và theo loại lệnh, LTT tùy chọn, cách chia dữ liệu
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
| Paper cần những bảng và hình nào? | 03 §2, 13 §1 |
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
