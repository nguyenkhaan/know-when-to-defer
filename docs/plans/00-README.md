# Kế hoạch triển khai — Know When to Defer (IEEE MOST 2027)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> Phiên bản v0.2 · 05/11/2026 · Bổ sung để thí nghiệm đủ sức thuyết phục: tập câu do người viết (E6), phân loại lỗi thật (E7), kiểm tra độ bền nhãn (V1–V3), 2 baseline mạnh (G1, L6), đóng băng tín hiệu sau pilot. Giảm chi phí: còn 5 mô hình, benchmark ~3.000 câu, `k = 4`. Khóa kết quả sớm hơn (22/11) để paper có trọn 6 ngày.

**Goal:** Đi từ con số 0 tới một paper 8 trang hoàn chỉnh, nộp IEEE MOST 2027 trước **30/11/2026** (hạn chính thức 01/12), kèm code và benchmark phát hành ẩn danh.

**Architecture:** Pipeline Python gồm các bước độc lập, mỗi bước đọc file vào và ghi file ra: LMRC → snapshot → benchmark → LLM dịch → solver → nhãn tác hại → tín hiệu → CRC → bảng và hình. Paper viết bằng LaTeX trong VS Code, song song với thí nghiệm; mọi con số trong paper sinh tự động từ `runs/`.

**Tech Stack:** Python 3.12 (`uv`), OR-Tools, pydantic v2, pandas, scikit-learn, sentence-transformers (CPU), matplotlib, typer, pytest; LLM qua API tương thích OpenAI; LaTeX `IEEEtran` + VS Code LaTeX Workshop + TinyTeX.

**Spec:** `docs/CONTENT.md` và các tài liệu 01–16 trong `docs/`. Nội dung học thuật: `MoTaDeTai.md`.

## Các phase

| Phase | File | Ngày | Vấn đề cần giải quyết | Mốc |
|---|---|---|---|---|
| 0 | `phase-0-setup.md` | 05–06/11 | Chưa có repo, dữ liệu, mô hình, khung paper | `pytest` chạy; `main.pdf` biên dịch |
| 0b | `phase-0b-smoke-test.md` | 06–07/11 | Rủi ro lớn nhất: LLM gần như không dịch sai. Kiểm tra nhanh bằng ~50 câu viết tay, chưa cần solver | Quyết định sớm: làm tiếp / điều chỉnh / báo động |
| 1 | `phase-1-core-pipeline.md` | 06–08/11 | Chưa biến được một tuyến thật + một lệnh thành kế hoạch và nhãn tác hại | Ví dụ bệnh viện cho `h = 1` |
| 2 | `phase-2-pilot-go-no-go.md` | 08–10/11 | Chưa biết LLM có sai đủ nhiều và tín hiệu solver có ích không; chưa biết chi phí thật | **M1 · 10/11: Go/No-go + đóng băng tín hiệu + chốt `α_main`** (GVHD review) |
| 3 | `phase-3-benchmark-and-signals.md` | 11–16/11 | Cần benchmark lớn, tập câu người viết, đủ tín hiệu và baseline mạnh | **M2 · 16/11** |
| 4 | `phase-4-experiments.md` | 17–22/11 | Cần kết quả E1–E7, kiểm tra độ bền, bảng và hình tự động | **M3 · 22/11: khóa kết quả** (GVHD review claim) |
| 5 | `phase-5-paper-writing.md` | 23–28/11 | Viết Results, Abstract, Intro cuối; ép 8 trang; đọc soát | Bản 8 trang hoàn chỉnh |
| 6 | `phase-6-review-and-submit.md` | 29–30/11 | Đọc độc lập, ẩn danh, phát hành code, nộp | **M4 · 30/11: nộp HotCRP** |

## Hai luồng song song

| Tuần | Luồng thí nghiệm | Luồng paper |
|---|---|---|
| 1 (05–10/11) | Phase 0–2 | Template, khung section, `refs.bib`; nháp Problem; đọc CORA, P22, ConformalNL2LTL |
| 2 (11–16/11) | Phase 3 | Nháp Related Work, Method, Benchmark, Hình F1, Intro v0 |
| 3 (17–22/11) | Phase 4 | Nháp Setup; gắn bảng và hình; Intro v1 |
| 4 (23–30/11) | Chỉ sửa lỗi | Phase 5–6: viết hoàn thiện, rà soát, nộp |

Abstract và Results viết sau cùng. Mọi phần còn lại viết trước, để tuần 4 chỉ còn hoàn thiện.

## Danh sách mô hình (5)

| ID | Vai trò | Gợi ý | Chạy ở đâu |
|---|---|---|---|
| M1 | Dịch · mô hình mở nhỏ | Qwen2.5-7B-Instruct | API dịch vụ |
| M2 | Dịch · mô hình mạnh | 1 mô hình frontier | API |
| M3 | Paraphrase câu benchmark | mô hình cỡ vừa, khác họ M1/M2/M4 | API, chỉ lúc dựng benchmark |
| M4 | Judge (L2, L5, L6, kiểm tra nghĩa paraphrase) | mô hình cỡ vừa, khác họ M1/M2 | API, chỉ trên câu được thực thi |
| M5 | Embedding cho baseline G1 | `bge-small-en-v1.5` | CPU cục bộ, miễn phí |

Đã bỏ: mô hình dịch cỡ vừa (Qwen2.5-14B).

## Phân vai

| Người | Vai trò | Phụ trách chính | Phần paper |
|---|---|---|---|
| **A** | Research lead | DSL, sinh benchmark, LLM (dịch, judge), tín hiệu S1–S5, L1–L6, G1; pilot và Go/No-go; đọc và phân tích kết quả; soạn thẻ và kiểm tra câu human; kiểm duyệt 300 câu; gán nhãn 100 lỗi | Intro, Problem, Method, Results, Abstract, Conclusion |
| **B** | Engineering lead | Repo, LMRC → snapshot, solver, nhãn tác hại, CRC, chia dữ liệu, chạy E1–E7, V1–V3, `kwd report`; viết ~100 câu human; kiểm duyệt 300 câu; gán lại 30 lỗi; phát hành ẩn danh, nộp bài | Template và khung paper, `refs.bib`, Related Work, Benchmark, Setup, Hình F1, bảng và hình |
| **C** | Người viết câu human | Viết ~100 câu từ thẻ tình huống (11–13/11, ~2 giờ) | — |
| **GVHD** | Review độc lập (chỉ đọc) | 10/11: báo cáo pilot (~20 phút) · 22/11: claim và bảng chính (~30 phút) · 27–28/11: toàn bài (~1,5 giờ) | — |

**Quy tắc "mù template" (giữ tập human sạch):**
- Cho tới khi nộp xong câu human (13/11), **B không xem** `src/kwd/bench/`, `configs/bench.yaml`, `data/benchmark/`, cũng không review code benchmark của A.
- **C không bao giờ xem** code, template hay dữ liệu benchmark.
- B kiểm duyệt bộ chính (Task 3.3) **sau khi** đã viết xong câu human (Task 3.2).

**Review code chéo:** A review code của B; B review code không thuộc benchmark của A (code benchmark: từ 14/11). Khi dùng AI agent, người phụ trách task là người duyệt kết quả của agent.

Nhãn người phụ trách ghi ở cuối tiêu đề mỗi task, dạng **[A]**, **[B]**, **[A + B]**…

## Loại step

**[CODE]** viết code (TDD) · **[EXP]** chạy thí nghiệm · **[PAPER]** viết paper · **[READ]** đọc hoặc tra tài liệu · **[HUMAN]** việc cần người làm (kiểm duyệt, viết câu, phân loại lỗi) · **[GVHD]** mốc review của giảng viên · **[DECIDE]** ra quyết định (ghi vào `docs/CONTENT.md` §6).

## Global Constraints

- Paper: **≤ 8 trang tính cả references**, `\documentclass[conference]{IEEEtran}`, double-blind, PDF nhúng font.
- LaTeX viết trong **VS Code** (LaTeX Workshop) với **TinyTeX** cài ở thư mục người dùng. **Không** cài qua `pacman`, không dùng `sudo`.
- Hạn nộp nội bộ **30/11/2026**; chính thức 01/12/2026 qua https://most2027.hotcrp.com/.
- **Khóa kết quả 22/11**: sau mốc này chỉ sửa lỗi, không chạy thí nghiệm mới.
- **Đóng băng tín hiệu 10/11**: không sửa định nghĩa tín hiệu sau khi đã nhìn kết quả benchmark chính hoặc tập người viết.
- Thời gian nội bộ là **giây nguyên** tính từ giờ xuất phát; chỉ hiển thị `HH:MM` giờ địa phương; kết quả báo bằng phút.
- `kwd.signals` không import `kwd.harm`, không đọc `gold` (spec 04 §5).
- Mọi lời gọi LLM và solver đi qua cache trên đĩa. Mỗi mô hình có giới hạn `max_usd` trong `configs/llm.yaml`.
- Mọi random lấy seed từ YAML trong `configs/`. Chia dữ liệu **theo tuyến**.
- Judge (M4) và paraphraser (M3) không bao giờ là mô hình dịch của cùng hàng dữ liệu.
- LMRC giấy phép CC BY-NC 4.0: chỉ dùng phi thương mại, phải ghi nguồn.

## Review Focus

Các tình huống spec không nói rõ nhưng dễ làm hỏng kết quả. Mỗi dòng đã có test trong task sở hữu nó.

1. **LLM viết tên điểm dừng khác chữ hoa/thường hoặc thừa khoảng trắng** → khớp sau chuẩn hóa; tên lạ → `unknown_stop`. Phase 1, Task 1.3.
2. **LLM viết giờ dạng "3 pm", "3:00 PM"** → chấp nhận; "15h", "afternoon" → `schema`. Phase 1, Task 1.3.
3. **Lệnh ghép mâu thuẫn** (cửa sổ giờ rỗng, precedence vòng) → `Infeasible`, tự chuyển người duyệt, không làm sập pipeline. Phase 1, Task 1.4.
4. **Mọi mẫu k của LLM đều lỗi parse** → L1 = 0, S4 = 1, không chia cho 0. Phase 2, Task 2.4.
5. **Một loại lệnh có rất ít mẫu calibration** (n < 20) → CRC theo loại trả `λ = −∞`, không lỗi. Phase 4, Task 4.1.

## Quy ước chung

- Commit sau mỗi task: `git commit -m "<type>: <mô tả>"` (`feat`, `test`, `paper`, `exp`, `docs`, `fix`).
- Cuối mỗi ngày: thêm một dòng trạng thái vào `docs/CONTENT.md` §6.
- Kết quả thí nghiệm nằm trong `runs/<run_id>/`; không chép tay con số vào paper.
