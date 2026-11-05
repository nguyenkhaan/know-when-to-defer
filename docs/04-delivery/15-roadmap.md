# 15 · Roadmap & Milestones

> Trạng thái: Draft v0.2 · Cập nhật 05/11/2026
> v0.2: khóa kết quả sớm hơn (**22/11**) để paper có trọn 6 ngày hoàn thiện; thêm tập câu người viết, phân loại lỗi, kiểm tra độ bền nhãn, 2 baseline mạnh; còn 5 mô hình, benchmark chính ~3.000 câu để giảm chi phí API.

## 1. Kế hoạch 4 tuần

| Tuần | Ngày | Thí nghiệm | Paper | Mốc |
|---|---|---|---|---|
| 1 | 05–10/11 | Repo, LMRC, DSL, solver, nhãn tác hại; pilot E0 | Template (VS Code + TinyTeX), khung section, `refs.bib`; nháp Problem | **M1 (10/11): Go/No-go**; đóng băng tín hiệu |
| 2 | 11–16/11 | Benchmark chính ~3.000; kiểm duyệt 300; **tập ~200 câu người viết (B, C)**; dịch; đủ tín hiệu + **G1, L6**; kiểm tra độ bền nhãn V1 | Nháp Related Work, Method, Benchmark, F1, Intro v0 | **M2 (16/11):** benchmark + bảng tín hiệu |
| 3 | 17–22/11 | CRC; E1–E7; V2; sinh bảng và hình tự động | Nháp Setup; Intro v1; gắn bảng và hình | **M3 (22/11): khóa kết quả** |
| 4 | 23–30/11 | Chỉ sửa lỗi | Results, Conclusion, Intro cuối, Abstract, ép 8 trang, đọc độc lập, ẩn danh, nộp | **M4 (30/11): nộp HotCRP** |

## 2. Mốc quyết định

| Ngày | Quyết định | Căn cứ |
|---|---|---|
| 06/11 | Chốt 5 mô hình và ngân sách `max_usd` | Giá, có logprobs, chạy thử (spec 10 §2) |
| 08/11 | Chốt 6–8 loại lệnh DSL | Chạy thử pilot |
| 10/11 | **Go / No-go**; đóng băng định nghĩa tín hiệu; chốt `α_main` | E0 (spec 13 §3, §14.0) |
| 10/11 | Kích thước benchmark chính và `k` | Chi phí thật mỗi câu từ E0 |
| 14/11 | Giữ hay cắt LTT (mặc định: **cắt**) | Tiến độ tuần 2 |
| 14/11 | Dùng CRC theo loại lệnh hay không | `μ` có chênh lệch giữa các loại không |
| 22/11 | **Khóa kết quả**: không chạy thí nghiệm mới | — |

## 3. Rủi ro chính và cách xử lý

| Rủi ro | Dấu hiệu sớm | Xử lý |
|---|---|---|
| `μ` quá thấp (H1 sai) | Pilot: `μ` < 3% ở mức 2–3 | Nhấn mạnh M1 (mô hình nhỏ); câu ghép khó hơn; nếu vẫn thất bại thì chuyển đề tài dự phòng |
| Tín hiệu solver không hơn LLM hoặc G1 (H2 sai) | AUROC E0 chồng lấn | Vẫn báo cáo trung thực; nếu L6 thắng thì nhấn mạnh "phản hồi kế hoạch có giá trị" |
| Thiếu câu cho tập human | Tới 13/11 có dưới 150 câu | B và C viết thêm tới ngày 14/11; tối thiểu 150 câu |
| Chi phí API vượt | Ước tính từ E0 vượt ngân sách | Giảm benchmark chính còn ~2.000 câu; `k = 3`; judge chỉ chạy trên tập con 1.000 câu |
| Solver chậm hoặc nhãn không ổn định | > 3 s/lần giải; V1 ≥ 1% | Tăng time limit cho `P*`; chạy song song; cache |
| Trễ viết paper | 22/11 chưa có bảng | Results viết với số nháp trước, thay bằng macro khi có số cuối |
| Vi phạm double-blind | — | Rà checklist (spec 16) trước 29/11 |

## 4. Người phụ trách

A (research lead), B (engineering lead), C (viết câu human 11–13/11), GVHD (review 10/11, 22/11, 27–28/11). Chi tiết vai trò và quy tắc "mù template": `plans/00-README.md` §Phân vai.

## 5. Nhịp làm việc

- Cuối mỗi ngày: thêm một dòng trạng thái vào `CONTENT.md` §6.
- Cuối mỗi tuần: kiểm tra tiêu chí hoàn thành của các spec liên quan trước khi sang tuần mới.
