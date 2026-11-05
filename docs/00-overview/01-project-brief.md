# 01 · Project Brief

> Trạng thái: Draft v0.1 · Cập nhật 05/11/2026
> Nguồn nội dung: `../MoTaDeTai.md` (chi tiết học thuật), `../DienGiaiYTuong.md` (bản dễ đọc).

## 1. Dự án là gì

Xây một **lớp kiểm soát rủi ro** đặt sau LLM và solver, trước bước thực thi. Khi điều phối viên gõ yêu cầu sửa tuyến bằng ngôn ngữ tự nhiên:

1. LLM dịch yêu cầu thành lệnh DSL;
2. solver tính lại tuyến;
3. lớp kiểm soát chấm **điểm rủi ro** và quyết định: **tự thực thi** hay **hỏi lại người**.

Mục tiêu là cam kết được: tỷ lệ lệnh "được thực thi mà gây hại" ≤ `α`.

**Sản phẩm cuối:** một paper 8 trang nộp IEEE MOST 2027 (hạn **01/12/2026**), kèm code và benchmark phát hành ẩn danh.

## 2. Vì sao cần

Lệnh sai ý nhưng đúng cú pháp vẫn chạy được. Ví dụ "Bệnh viện chỉ nhận từ 15:00" bị dịch thành "giao trước 15:00": tuyến cũ (14:10) đã thỏa ràng buộc sai, solver giữ nguyên tuyến và báo khả thi, nhưng tài xế đến sớm 50 phút. Không bộ kiểm tra cú pháp hay kiểm tra khả thi nào bắt được lỗi này. **Tác hại chỉ lộ ra ở mức kế hoạch.**

## 3. Đóng góp (theo thứ tự ưu tiên)

| # | Đóng góp | Ghi chú |
|---|---|---|
| C1 | Định nghĩa bài toán + nhãn tác hại **mức kế hoạch** | Spec 09 |
| C2 | Benchmark sửa tuyến trên tuyến thật LMRC, gold sinh trước câu | Spec 05, 08 |
| C3 | **Tín hiệu từ solver, không cần gold** bắt lỗi tốt hơn tín hiệu chỉ từ LLM (chứng minh bằng ablation) | **Đóng góp chính** · Spec 11 |

**Không claim:** LLM dịch lệnh (ReOpt-LLM), conformal "hỏi người" (KnowNo), khung CRC chặn hành động gây hại (CORA). CRC chỉ là công cụ.

## 4. Mục tiêu / Không làm / Thất bại dù chạy được

**Mục tiêu**
- Pipeline chạy end-to-end trên tuyến LMRC: request → DSL → solver → nhãn tác hại → tín hiệu → quyết định.
- Benchmark khoảng 3.000+ yêu cầu, 3 mức mơ hồ, nhãn tái lập.
- Đủ bảng và hình cho paper (xem `01-research/03-paper-outline.md`).

**Không làm (non-goals)**
- Nhiều xe hoặc chuyển đơn giữa các xe (ma trận thời gian chỉ có nội tuyến).
- LLM sinh code tự do; fine-tune LLM; huấn luyện guardian lớn.
- Giao diện người dùng; triển khai thật cho điều phối viên.
- Cập nhật ngưỡng online (chỉ ghi là hướng mở rộng).

**Thất bại dù kỹ thuật chạy được (anti-goals)**
- Tỷ lệ lỗi gốc `μ ≤ α`: không còn gì để kiểm soát.
- Không có ablation chứng minh tín hiệu solver tạo khác biệt: bài thành "bọc conformal quanh LLM".
- Nhãn tác hại không tái lập được (phụ thuộc seed hoặc timeout của solver).
- Lộ danh tính trong bản nộp (double-blind): có thể bị loại không cần review.

## 5. Ràng buộc

- **Thời gian:** 4 tuần (05/11 → 30/11/2026); khóa kết quả **22/11** để dành 6 ngày cho paper. Xem `04-delivery/15-roadmap.md`.
- **Paper:** 8 trang **tính cả references**, IEEE conference format, double-blind.
- **Tài nguyên:** máy cá nhân **không có GPU**; 5 mô hình (2 mô hình dịch, 1 paraphrase, 1 judge, 1 embedding chạy CPU), các LLM gọi qua API (spec 10 §2). Ngân sách API giới hạn bằng `max_usd`.
- **Paper:** viết LaTeX trong VS Code (TinyTeX, không cài qua pacman).
- **Dữ liệu:** LMRC 2021, giấy phép CC BY-NC 4.0.

## 6. Thuật ngữ

| Thuật ngữ | Nghĩa trong dự án |
|---|---|
| Request `q` | Câu yêu cầu bằng ngôn ngữ tự nhiên của điều phối viên |
| Snapshot `P` | Kế hoạch tuyến đang chạy tại thời điểm `t_now` (các điểm đã giao + các điểm còn lại) |
| Edit / lệnh DSL `e` | Lệnh sửa có cấu trúc (JSON), ví dụ `set_time_window` |
| Gold edit `e*` | Lệnh đúng, sinh **trước** câu chữ khi xây benchmark |
| `ê` | Lệnh do LLM sinh |
| `P̂`, `P*` | Kế hoạch sau khi áp `ê`, và sau khi áp `e*` |
| Harm `h` | Nhãn tác hại 0/1 của `P̂` (Spec 09) |
| Binding | Ràng buộc làm kế hoạch phải thay đổi. **Không binding**: kế hoạch cũ đã tình cờ thỏa ràng buộc đó |
| Signal | Đặc trưng dùng để ước lượng rủi ro (Spec 11) |
| Risk score `s` | Điểm rủi ro gộp từ các signal; `s` càng cao càng đáng ngờ |
| `λ`, `α` | Ngưỡng thực thi (`s ≤ λ` thì thực thi) và mức rủi ro cam kết |
| `μ` | Tỷ lệ gây hại khi luôn thực thi (base harm rate) |
| Coverage | Tỷ lệ lệnh được tự thực thi |
| Defer | Chuyển người duyệt |
| CRC | Conformal Risk Control, cách chọn `λ` có bảo đảm thống kê |
| Ambiguity level | Mức mơ hồ của câu: 1 tường minh, 2 tham chiếu gián tiếp, 3 ghép hoặc ẩn ý |
