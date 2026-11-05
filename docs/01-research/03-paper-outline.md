# 03 · Paper Outline

> Trạng thái: Draft v0.2 · Cập nhật 05/11/2026 · v0.2: thêm T4 (phân loại lỗi), dòng "human" trong T2/T3, F3 gộp vào T3 nếu thiếu chỗ.
> Giới hạn: **8 trang tính cả references** (trang 9–10 phải trả phí, không dùng). IEEE conference template (LaTeX `IEEEtran`, chế độ `conference`), double-blind.

## 1. Ngân sách trang

| Mục | Trang | Nội dung chính |
|---|---:|---|
| Abstract + I. Introduction | 1,0 | Ví dụ bệnh viện; khoảng trống; 3 đóng góp; Hình F1 |
| II. Related Work | 0,75 | LLM tái tối ưu (P1, P4, P3, P5); risk control cho hành động LLM (P11–P14, P21, P22); dùng bản nháp ở `MoTaDeTai.md` §10 |
| III. Problem Formulation | 0,75 | Ký hiệu; định nghĩa harm; rủi ro kết hợp và theo loại; cận coverage tối đa |
| IV. Method | 1,25 | DSL; solver; tín hiệu solver (trọng tâm); tín hiệu LLM; gộp điểm; CRC |
| V. Benchmark | 0,75 | Sinh từ LMRC; gold trước câu; 3 mức mơ hồ; kiểm duyệt; tập ~200 câu do 2 người viết; thống kê |
| VI. Experiments | 2,25 | Thiết lập (kèm V1–V3); E1–E7; ablation |
| VII. Limitations & Conclusion | 0,3 | Câu tổng hợp; một xe; shift |
| References | ~0,95 | Khoảng 25–28 mục, viết gọn |
| **Tổng** | **8,0** | |

## 2. Hình và bảng (tối đa 3 hình + 4 bảng; T4 nhỏ)

| ID | Loại | Nội dung | Nguồn |
|---|---|---|---|
| F1 | Hình (1 cột) | Pipeline + ví dụ bệnh viện (lệnh sai, tuyến không đổi) | Vẽ tay |
| F2 | Hình (1 cột) | Đường risk–coverage: chỉ LLM, chỉ solver, gộp; đường tham chiếu oracle | E2/E4 |
| F3 | Hình (1 cột) | Rủi ro theo loại lệnh: ngưỡng chung vs theo loại, vạch `α` | E3 |
| T1 | Bảng | Benchmark: số mẫu, `μ` theo LLM × mức mơ hồ; % vô hại; % không binding | E1 |
| T2 | Bảng | AUROC từng tín hiệu + AURC các tổ hợp (ablation, G1, L6), tách nhóm không binding; cột thêm cho tập người viết | E2/E4/E6 |
| T3 | Bảng | CRC: coverage, rủi ro thực tế, tần suất vi phạm; dòng random / theo loại / shift / human | E3/E5/E6 |
| T4 | Bảng nhỏ (1 cột, ~6 dòng) | Loại lỗi thật × tỷ lệ × % bị bắt bởi SOLVER / LLM / ALL | E7 |

Nếu thiếu chỗ (theo thứ tự): bỏ F3 và giữ số theo loại trong T3; rút T1 còn các dòng tổng; đưa T4 thành 2 câu trong Results.

## 3. Thông điệp từng mục (một câu)

- **Intro:** LLM dịch sai mà vẫn khả thi là một rủi ro mới; chỉ kiểm tra lệnh là không đủ, phải nhìn kế hoạch.
- **Problem:** harm định nghĩa trên kế hoạch; muốn bảo đảm `α` thì cần điểm rủi ro tốt và chọn ngưỡng đúng.
- **Method:** solver vừa là bộ tính tuyến vừa là máy thử nghiệm để phát hiện lệnh hiểu sai.
- **Benchmark:** gold sinh trước câu, nên nhãn tái lập được mà không cần gán nhãn tay từng mẫu.
- **Experiments:** tín hiệu solver làm đường risk–coverage tốt lên rõ; CRC giữ `α`, nhưng cần hiệu chỉnh theo loại lệnh và cảnh giác với shift.

## 4. Quy ước viết

- Tiếng Anh; dùng thì hiện tại; tránh "first", "novel" khi chưa có bằng chứng.
- Tham chiếu công trình của mình ở ngôi thứ ba; không link repo thật. Dùng link ẩn danh (Spec 16).
- Mọi con số trong bài phải truy được về một file kết quả trong `runs/` (Spec 14).
