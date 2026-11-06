# 02 · Research Questions & Claims

> Trạng thái: Draft v0.3 · Cập nhật 07/11/2026 · v0.3: tinh gọn paper: bỏ F3, shift chỉ còn theo trạm (C6), C7 gộp hai người viết trong bảng. · v0.2: thêm claim C7 (câu do người viết), C3' (không "tự ra đề tự giải"), baseline mạnh hơn, kiểm tra độ bền nhãn.
> Tài liệu này là "hợp đồng" giữa paper và thí nghiệm: mỗi claim phải có bằng chứng cụ thể; thí nghiệm nào không phục vụ claim nào thì cân nhắc bỏ.

## 1. Câu hỏi nghiên cứu và giả thuyết

| RQ | Câu hỏi | Giả thuyết | Bác bỏ khi |
|---|---|---|---|
| RQ1 | LLM dịch sai bao nhiêu, theo loại lệnh và mức mơ hồ? Bao nhiêu lỗi gây hại, bao nhiêu không binding? | **H1:** Ở mức mơ hồ 2–3, `μ` ≥ 3–5% với ít nhất một LLM thực tế; `μ` chênh lệch giữa các loại lệnh; một phần lỗi là vô hại | `μ` < 3% ở mọi mô hình và mức mơ hồ (xem go/no-go, Spec 13) |
| RQ2 *(chính)* | Tín hiệu từ solver có dự báo lỗi gây hại tốt hơn tín hiệu chỉ từ LLM, và tốt hơn một bộ chấm học có giám sát không? | **H2:** Ít nhất một tín hiệu solver có AUROC cao hơn rõ verbalized confidence, nhất là với lỗi không binding; gộp tín hiệu solver + LLM cho AURC tốt hơn chỉ dùng LLM và không kém bộ chấm học (G1); kết quả giữ được trên câu do người viết | Khoảng tin cậy AUROC chồng lấn hoàn toàn; ablation bỏ tín hiệu solver không làm AURC xấu đi |
| RQ3 | CRC có giữ rủi ro ≤ `α` mà coverage vẫn cao không? Ngưỡng chung có che giấu vi phạm ở loại lệnh hiếm không? Bảo đảm còn giữ khi phân phối đổi không? | **H3:** Split ngẫu nhiên: giữ `α`. Ngưỡng chung: vi phạm ở loại có `μ` cao; hiệu chỉnh theo loại khắc phục được, đổi lại mất một ít coverage. Split theo trạm: có thể vỡ | — (RQ3 mang tính mô tả, báo cáo trung thực cả khi bảo đảm vỡ) |

## 2. Bản đồ claim → bằng chứng

| Claim trong paper | Bằng chứng | Thí nghiệm (Spec 13) | Hình / bảng |
|---|---|---|---|
| C1. Nhãn tác hại mức kế hoạch khác nhãn mức chuỗi | Tỷ lệ lệnh sai JSON nhưng vô hại, và ngược lại | E1 | Bảng T1 |
| C1'. Lỗi không binding là có thật và đáng kể | Tỷ lệ lỗi gây hại mà `P̂ = P` (kế hoạch không đổi) | E1 | Bảng T1 |
| C2. Benchmark có `μ` khác 0 và tăng theo mức mơ hồ | `μ` theo LLM × mức mơ hồ | E1 | Bảng T1 |
| **C3. Tín hiệu solver tốt hơn tín hiệu LLM và bộ chấm học** | AUROC từng tín hiệu; AURC của các tổ hợp; so với G1 (học có giám sát) và L6 (LLM xem thay đổi kế hoạch); tách riêng nhóm không binding | E2, E4 | Bảng T2, Hình F2 |
| C3'. Tín hiệu bắt được lỗi **tự nhiên** của LLM, không chỉ khớp với template | Phân loại ~100 lỗi thật, mỗi loại do tín hiệu nào bắt; tín hiệu được đóng băng sau pilot | E7, V3 | Bảng T4 |
| C4. CRC giữ `α` trên split ngẫu nhiên | Rủi ro thực tế và tần suất vi phạm qua 100 split | E3 | Bảng T3 |
| C5. Ngưỡng chung che giấu vi phạm theo loại; hiệu chỉnh theo loại sửa được | Rủi ro theo nhóm `ĉ` (loại lệnh LLM sinh), ngưỡng chung vs theo nhóm, ở `α_F3` (spec 13 §14.0) | E3 | Bảng T3 (dòng theo nhóm) |
| C6. Dưới dịch chuyển phân phối, bảo đảm có thể vỡ | Rủi ro thực tế khi calibrate trên một số trạm, test trên trạm khác | E5 | Bảng T3 (dòng shift) |
| **C7. Kết quả giữ được trên câu do người thật viết** | Thứ hạng AUROC và rủi ro thực tế trên ~200 câu do 2 người viết (B, C), bảng gộp hai người, theo từng người một câu | E6 | Bảng T2/T3 (dòng "human") |
| C8. Hệ thống ngăn được tác hại vận hành cụ thể | Số lần thực thi gây hại, phút trễ, khung giờ bị vi phạm được tránh trên 1.000 yêu cầu ở `α_main` | E3 | 1 câu trong Results + Intro |
| (Độ tin cậy của C1) Nhãn tác hại ổn định | Tỷ lệ nhãn đổi khi giải lại < 1%; kết luận không đổi với ε ∈ {0, 5, 10} | V1, V2 | 1 câu trong Setup |

**Tiêu chí đạt của từng claim** được chốt trước ở spec 13 §14.6; `α_main` chọn từ pilot (spec 13 §14.0).

**Quy tắc viết claim:** chỉ viết claim nào bảng hoặc hình chống đỡ được. Không viết "first" trừ khi đã tra IEEE Xplore và ACM DL. Không claim mới cho CRC/LTT, rủi ro kết hợp vs có điều kiện, hay weighted CRC.

## 3. Những gì sẽ được báo cáo dù kết quả xấu

- `μ` thấp ở mô hình mạnh: báo cáo, và dùng làm lập luận cho triển khai LLM nhỏ chạy cục bộ.
- Bảo đảm vỡ dưới shift: báo cáo như một phát hiện, không giấu.
- Tín hiệu nào không có ích: vẫn để trong bảng ablation.
