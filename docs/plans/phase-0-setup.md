# Phase 0 — Chuẩn bị (05–06/11)

> Xem `00-README.md` cho Global Constraints và Review Focus.

**Goal:** Có repo Python chạy được test, dữ liệu LMRC trên máy, 5 mô hình gọi được và có ngân sách, khung paper IEEE biên dịch được trong VS Code với đủ section và trích dẫn.

**Spec:** `docs/02-specs/04-architecture.md`, `docs/01-research/03-paper-outline.md`, `docs/04-delivery/16-submission-checklist.md`

## Vấn đề cần giải quyết

Hiện chỉ có tài liệu. Chưa có git, môi trường Python, dữ liệu, LaTeX, template hội nghị. Máy không có GPU, nên mọi LLM gọi qua API; LaTeX dùng TinyTeX cài ở thư mục người dùng (không dùng pacman). Phải dựng xong nền móng trong ~1,5 ngày để Phase 1 bắt đầu code ngay.

---

### Task 0.1: Repo và môi trường Python · **[B]**

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `src/kwd/__init__.py`, `src/kwd/cli.py`, `tests/test_smoke.py`, `configs/` (thư mục rỗng có `.gitkeep`)

**Interfaces:**
- Produces: lệnh `kwd` (typer app `kwd.cli:app`), package `kwd`.

- [x] **Step 1 [CODE]:** `git init`; tạo `.gitignore` gồm `data/`, `runs/`, `.venv/`, `__pycache__/`, `paper/build/`, `paper/*.aux`, `paper/*.log`.
- [x] **Step 2 [CODE]:** `uv init --package --name kwd --python 3.12`; thêm dependency: `uv add ortools pydantic pandas pyarrow numpy scipy scikit-learn matplotlib typer pyyaml httpx tqdm ijson sentence-transformers` và `uv add --dev pytest ruff`. Ép `torch` bản CPU (khai báo index `https://download.pytorch.org/whl/cpu` cho `torch` trong `pyproject.toml`) để không tải bản CUDA nặng.
- [x] **Step 3 [CODE]:** Viết test `tests/test_smoke.py::test_cli_help` gọi `typer.testing.CliRunner().invoke(app, ["--help"])`, assert `exit_code == 0`.
- [x] **Step 4 [CODE]:** Tạo `kwd.cli:app` (typer) với một lệnh `version`. Khai báo `[project.scripts] kwd = "kwd.cli:app"`.
- [x] **Step 5:** Chạy `uv run pytest -q` → `1 passed`. Chạy `uv run kwd --help` → in danh sách lệnh.
- [ ] **Step 6:** Commit `chore: init kwd package`.

### Task 0.2: Tải dữ liệu LMRC · **[B]**

**Files:**
- Create: `scripts/download_lmrc.sh`, `data/raw/lmrc/` (không commit)

- [ ] **Step 1 [CODE]:** Viết `scripts/download_lmrc.sh` dùng `uvx --from awscli aws s3 cp --no-sign-request --recursive s3://amazon-last-mile-challenges/almrrc2021/almrrc2021-data-training/model_build_inputs/ data/raw/lmrc/`. Kiểm tra trước dung lượng bằng `aws s3 ls --summarize --human-readable --recursive`. Lưu ý `travel_times.json` có thể nặng vài GB, cần đủ chỗ đĩa.
- [ ] **Step 2 [EXP]:** Chạy script. Kiểm tra có đủ 4 file `route_data.json`, `package_data.json`, `travel_times.json`, `actual_sequences.json`.
- [ ] **Step 3 [READ]:** Mở 1 tuyến bằng `python -c` + `json` (đọc stream nếu file quá lớn, dùng `ijson`). Ghi tên trường thật vào spec 05 §2 nếu khác. Đặc biệt kiểm tra định dạng thời gian của `time_window` và danh sách `station_code` để làm bảng múi giờ.
- [ ] **Step 4:** Commit `chore: add LMRC download script` (+ sửa spec 05 nếu có).

### Task 0.3: Chốt 5 mô hình và ngân sách API · **[A]**

**Files:**
- Create: `configs/llm.yaml`, `.env` (không commit), `scripts/ping_models.py`

- [ ] **Step 1 [DECIDE]:** Chọn nhà cung cấp và mô hình cụ thể cho M1–M4 (bảng ở `00-README.md`). Tiêu chí: endpoint tương thích OpenAI, có `seed`; M1 có `logprobs`; M3 và M4 khác họ với M1, M2 và khác nhau. Ghi giá input/output mỗi triệu token.
- [ ] **Step 2 [DECIDE]:** Đặt `max_usd` cho từng mô hình trong `configs/llm.yaml`. Ước lượng ban đầu cho bản chính (~3.000 câu, `k = 4`, prompt ~2,5k token, có prompt caching): M1 và M2 mỗi mô hình ~3.000 × 5 lời gọi; M4 ~3 lời gọi cho mỗi câu được thực thi, mỗi mô hình dịch; M3 ~3.000 lời gọi ngắn. Con số chính xác chốt lại sau pilot (Phase 2).
- [ ] **Step 3 [CODE]:** `scripts/ping_models.py`: gọi 1 prompt ngắn tới M1–M4, in latency, số token, có/không có logprobs; tải `bge-small-en-v1.5` (M5) và encode thử 2 câu trên CPU.
- [ ] **Step 4 [EXP]:** Chạy script; mọi mô hình trả lời được.
- [ ] **Step 5:** Ghi mô hình đã chọn vào spec 10 §2 và `docs/CONTENT.md` §6. API key nằm trong `.env` (đã gitignore). Commit `chore: model roster and budget`.

### Task 0.4: Template paper IEEE và khung section · **[B]**

**Files:**
- Create: `paper/main.tex`, `paper/sections/{00-abstract,01-introduction,02-related-work,03-problem,04-method,05-benchmark,06-experiments,07-conclusion}.tex`, `paper/refs.bib`, `paper/figures/`, `paper/tables/`, `paper/Makefile`, `paper/NOTES.md`

- [ ] **Step 1 [READ]:** Mở https://www.ieeemobility.org/submission.html và CFP PDF. Ghi các điểm bắt buộc vào `paper/NOTES.md`: 8 trang tính cả references, double-blind, PDF nhúng font, HotCRP, ngày. Nếu có thay đổi so với spec 16 thì sửa spec 16.
- [ ] **Step 2 [PAPER]:** Cài TeX ở thư mục người dùng (không sudo, không pacman): `curl -sL "https://yihui.org/tinytex/install-bin-unix.sh" | sh`, sau đó `tlmgr install IEEEtran latexmk booktabs cite xcolor`. Kiểm tra `latexmk -v`.
- [ ] **Step 2b [PAPER]:** VS Code: cài extension **LaTeX Workshop**. Thêm vào `.vscode/settings.json` (giữ các thiết lập cũ): recipe `latexmk (pdf)`, `"latex-workshop.latex.outDir": "%DIR%/build"`, build khi lưu. Mở `paper/main.tex`, nhấn lưu → PDF hiện trong tab xem trước.
- [ ] **Step 3 [PAPER]:** Tải template chính thức từ https://www.ieee.org/conferences/publishing/templates.html (gói LaTeX conference) hoặc CTAN `IEEEtran`. Tạo `main.tex` với `\documentclass[conference]{IEEEtran}`, gói `amsmath, amssymb, graphicx, booktabs, cite, xcolor`; khối tác giả là `\author{\IEEEauthorblockN{Anonymous Authors}}`; `\input` 8 file section; `\bibliographystyle{IEEEtran}`.
- [ ] **Step 4 [PAPER]:** Mỗi file section có tiêu đề và một comment ghi **ngân sách trang** và **thông điệp một câu** (copy từ doc 03 §1, §3). Ví dụ đầu `01-introduction.tex`: `% Budget: 1.0 page incl. abstract. Message: an LLM mistranslation can be feasible and invisible; you must look at the plan.`
- [ ] **Step 5 [PAPER]:** Tạo `refs.bib` với 24 mục P1–P24 từ `MoTaDeTai.md` §9.2 (key dạng `li2023optiguide`, `ye2026reoptllm`…). ReOpt-LLM dùng bản NeurIPS 2026; CORA, Role-Stratified CRC, When-Can-CRC, ConformalNL2LTL dùng arXiv.
- [ ] **Step 6 [PAPER]:** `Makefile` (dùng khi build ngoài VS Code và để kiểm tra số trang): `make` = `latexmk -pdf -outdir=build main.tex`; `make pages` = in số trang của `build/main.pdf` (dùng `pdfinfo`, hoặc `python -c` với `pypdf` nếu máy không có poppler); `make check` = báo lỗi nếu số trang > 8.
- [ ] **Step 7:** Chạy `make` (hoặc lưu file trong VS Code) → `build/main.pdf` biên dịch, có 8 tiêu đề section và danh sách tham khảo khi `\nocite{*}` tạm bật. Tắt `\nocite{*}` sau khi kiểm tra.
- [ ] **Step 8:** Commit `paper: add IEEEtran skeleton and bibliography`.

### Task 0.5: Chốt các quyết định mở · **[A]**

- [ ] **Step 1 [DECIDE]:** Xác nhận luật R2 ("bỏ nhầm điểm dừng là gây hại", spec 09). Nếu giữ: sửa `MoTaDeTai.md` §2.2 và `DienGiaiYTuong.md` cho khớp.
- [ ] **Step 2 [DECIDE]:** Xác nhận câu yêu cầu bằng tiếng Anh (spec 08 §5).
- [ ] **Step 3:** Ghi các quyết định vào `docs/CONTENT.md` §6; commit `docs: record phase-0 decisions`.

## Kết thúc Phase 0 khi

- [ ] `uv run pytest -q` pass; `uv run kwd --help` chạy.
- [ ] 4 file LMRC có trên máy.
- [ ] Gọi được M1–M4 qua API, M5 chạy trên CPU; `max_usd` đã đặt.
- [ ] `paper/build/main.pdf` biên dịch trong VS Code, `make check` pass.
