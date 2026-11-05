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
| Khi nào dừng đề tài (go/no-go)? | 13 §2, 15 §2 |
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
