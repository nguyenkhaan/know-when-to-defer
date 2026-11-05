# Báo cáo kiểm tra nhanh (smoke test) – Phase 0b

Ngày thực hiện: 05/11/2026 · Người thực hiện: An

## 1. Mục đích

Rủi ro lớn nhất của đề tài là **LLM gần như không dịch sai** các yêu cầu sửa tuyến. Nếu điều này đúng, lớp kiểm soát rủi ro không có lỗi nào để phát hiện, và đóng góp của paper sẽ không còn ý nghĩa.

Vì vậy, trước khi đầu tư 4–5 ngày xây dựng solver và benchmark, nhóm thực hiện một phép thử nhanh: **soạn khoảng 50 câu yêu cầu có đáp án, cho hai mô hình dịch, sau đó đánh giá thủ công tần suất và loại lỗi.**

Kết quả này **không dùng trong paper**. Nó chỉ là tín hiệu sớm để quyết định có tiếp tục hướng nghiên cứu hay không. Nếu LLM gần như không mắc lỗi, nhóm sẽ dừng lại và cân nhắc chuyển sang hướng dự phòng, thay vì tiếp tục một hướng khó tạo ra đóng góp.

## 2. Phương pháp

### 2.1. Tuyến giao hàng

Hai tuyến mẫu, ở thời điểm giữa ca:

| Tuyến | Số điểm còn lại | Thời điểm | Đặc điểm |
|---|---|---|---|
| R1 | 8 | 13:00, hết ca 17:30 | Tên điểm phân biệt rõ ràng |
| R2 | 15 | 12:30, hết ca 17:00 | Nhiều tên dễ nhầm (Oak Pharmacy / Oak Clinic / Oakwood Office; 7 / 21 Birch Lane; St. Mary / St. Mark School) |

### 2.2. Câu yêu cầu

Gồm **50 câu tiếng Anh**, viết theo văn phong điều phối viên nhắn cho tài xế. Đáp án của mỗi câu được xác định **trước** khi gọi mô hình. Các câu chia thành 6 nhóm, theo loại khó khăn ngôn ngữ:

| Nhóm | Khó khăn | Ví dụ |
|---|---|---|
| Chiều thời gian | "until", "no later than", "from … on" dễ bị hiểu ngược | *Harbor Office won't take anything till 3.* |
| Gọi gián tiếp | Không nêu tên điểm, chỉ nêu loại hoặc khu | *Drop the pharmacy in zone B today.* |
| Tên dễ nhầm | Tên gần giống một điểm khác | *Oak Clinic's shut, skip them.* |
| Giờ tương đối | Mô hình phải tự tính giờ | *Truck back by twenty to five.* |
| Câu ghép | 2–4 yêu cầu trong một câu | *Cancel Riverside Bakery and get the truck back by 4:40.* |
| Ẩn ý | Chỉ mô tả sự việc, không nêu trực tiếp yêu cầu | *Minh Chau Pharmacy is on break from 1 PM to 2:30 PM.* |

Câu của R1 do An viết. Câu của R2 do trợ lý AI (Claude) soạn nháp, sau đó An chỉnh sửa và bổ sung. Cách chia này cho phép so sánh sơ bộ tỷ lệ lỗi giữa câu do người viết và câu có sự hỗ trợ của AI. Điều này liên quan đến thiết kế sau này, vì nghiên cứu sẽ có hai bộ dữ liệu: bộ chính (câu sinh tự động, được LLM diễn đạt lại) và bộ câu do người viết.

### 2.3. Mô hình

Hai mô hình được gọi qua API của OpenRouter. Mỗi câu được gọi một lần, với nhiệt độ 0 và seed cố định:

- **M1:** Qwen3.5-9B, mô hình mở cỡ nhỏ.
- **M2:** DeepSeek V4 Flash, mô hình mạnh, chi phí thấp.

Tổng chi phí API: dưới 0,01 USD.

### 2.4. Tiêu chí đánh giá

Mỗi cặp (câu, mô hình) được gán một nhãn thủ công:

| Nhãn | Ý nghĩa |
|---|---|
| ✅ Đúng | Cùng ý với đáp án |
| 🟡 Sai vô hại | Khác đáp án nhưng không làm sai tuyến |
| 🔴 Sai có hại | Tuyến sau khi sửa không đúng ý người yêu cầu |
| ⚪ Bị chặn | Lệnh không hợp lệ (ví dụ giờ đã qua); hệ thống tự chuyển cho người duyệt |

Hai câu (s40, s48) bị loại vì bản thân câu có hơn một cách hiểu hợp lý. Số câu được đánh giá là **48**.

**Quy tắc quyết định** (đặt trước khi chạy), dựa trên số câu 🔴 của M1:

| Số câu 🔴 | Quyết định |
|---|---|
| ≥ 5 | Tiếp tục Phase 1 |
| 1–4 | Tiếp tục, điều chỉnh thiết kế pilot |
| Gần 0 (cả M1 và M2) | Báo động: báo GVHD, thử thêm câu khó; nếu vẫn không có lỗi thì cân nhắc hướng dự phòng |

Quyết định chính thức về việc tiếp tục đề tài được đưa ra ở pilot (10/11), không phải ở bước này.

## 3. Kết quả

| | ✅ Đúng | 🟡 Sai vô hại | 🔴 Sai có hại | ⚪ Bị chặn |
|---|---|---|---|---|
| **M1** (Qwen3.5-9B) | 21 | 4 | **18 (38%)** | 5 |
| **M2** (DeepSeek V4 Flash) | 40 | 3 | **5 (10%)** | 0 |

Do cỡ mẫu nhỏ (48 câu), khoảng tin cậy 95% còn rộng: khoảng 25–52% với M1 và 5–22% với M2.

**Theo tuyến (số câu 🔴):**

| | R1 (An viết, 22 câu) | R2 (AI soạn, An chỉnh, 26 câu) |
|---|---|---|
| M1 | 7 (32%) | 11 (42%) |
| M2 | 1 (5%) | 4 (15%) |

Tỷ lệ lỗi giữa hai tuyến tương đương nhau. Vì vậy không có dấu hiệu câu do AI soạn dễ hơn câu do người viết.

## 4. Nhận xét

### 4.1. Xuất hiện lỗi "vô hình", đúng loại lỗi đề tài hướng tới

Đây là các lỗi mà **tuyến sau khi sửa không thay đổi**, nên người điều phối không thể phát hiện khi chỉ nhìn kế hoạch.

Ví dụ điển hình (s20, M1):

- Yêu cầu: *"Minh Chau Pharmacy is on break from 1 PM to 2:30 PM."* Nghĩa là chỉ được giao **sau 14:30**.
- M1 dịch thành: chỉ giao **trong khoảng 13:00–14:30**, tức là đúng giờ nhà thuốc nghỉ.
- Giờ dự kiến hiện tại là 13:20, nằm trong khoảng sai đó. Vì vậy tuyến không thay đổi, và lỗi không bị phát hiện.

Có 3 lỗi loại này ở M1 và 2 ở M2. Đáng chú ý, **mô hình mạnh cũng mắc lỗi này**. Ví dụ, M2 dịch "bệnh viện phải được giao trong vòng 1 giờ" thành khung 13:10–15:10, trong khi giờ dự kiến 14:10 đã nằm sẵn trong khung.

### 4.2. Mô hình sai nhưng vẫn tự tin cao

Mỗi câu trả lời có kèm mức tự tin do mô hình tự đánh giá (0–100). **Tất cả các câu sai có hại của cả hai mô hình đều có mức tự tin 85–100.** Trường hợp duy nhất có mức tự tin thấp (70) lại là một câu M2 trả lời đúng.

Như vậy, mức tự tin do mô hình tự khai không đủ để nhận biết lỗi. Đây là cơ sở để đề tài đề xuất sử dụng tín hiệu từ solver.

### 4.3. Phân loại lỗi

| Loại lỗi | M1 | M2 | Ví dụ |
|---|---|---|---|
| Dùng sai loại lệnh (bỏ điểm thay vì dời giờ; đặt thứ tự thay vì đặt khung giờ) | 8 | 0 | *"St. Mary School only from 2 onwards"*: M1 **loại bỏ** trường khỏi tuyến |
| Hiểu ngược chiều thời gian | 5 | 0 | *"not more than 1 hour ahead of schedule"*: M1 yêu cầu giao **trước** 14:00 |
| Sai giá trị thời gian | 3 | 2 | *"twenty to five"*: M1 hiểu thành 16:20 thay vì 16:40 |
| Mở rộng phạm vi (áp dụng cho cả khu thay vì một điểm) | 2 | 3 | *"Lakeside Shop: nothing before 4:15"*: M2 chặn **toàn bộ khu D** |

M1 mắc đủ các loại lỗi. M2 mắc ít lỗi hơn, chủ yếu thuộc hai loại "mở rộng phạm vi" và "sai giá trị thời gian".

### 4.4. Lỗi nhầm sáng/chiều được hệ thống chặn

M1 có 4 câu hiểu giờ buổi chiều thành giờ buổi sáng (ví dụ "3" thành 03:00). Vì thời điểm hiện tại đã quá trưa, các giờ này nằm trong quá khứ. Bộ kiểm tra của hệ thống sẽ từ chối và chuyển cho người duyệt, nên các lỗi này không gây hại.

Nhóm **không bổ sung cơ chế tự sửa** (ví dụ đổi 03:00 thành 15:00), vì cơ chế đó sẽ che giấu lỗi thật của mô hình và làm sai lệch phép đo.

## 5. Hạn chế

- **Cỡ mẫu nhỏ** (48 câu): kết quả chỉ mang tính định hướng.
- **Đánh giá thủ công:** chưa có solver để kiểm chứng tác hại thực tế trên tuyến.
- **Câu được thiết kế khó:** pilot và benchmark chính có cả câu dễ, nên tỷ lệ lỗi thực tế dự kiến sẽ thấp hơn.
- **Mới kiểm tra một phần giả thuyết:** smoke test cho thấy mô hình mắc lỗi đủ nhiều (H1). Nó **chưa** kiểm tra được việc tín hiệu từ solver phát hiện lỗi tốt hơn tín hiệu từ mô hình (H2), vốn là đóng góp chính của paper.

## 6. Kết luận

**Tiếp tục thực hiện đề tài.** Số câu sai có hại của cả hai mô hình vượt xa ngưỡng đặt trước (5/50 câu). Ngoài ra:

- có lỗi vô hình, xuất hiện ở cả mô hình mạnh;
- mô hình vẫn tự tin cao khi sai.

Hai kết quả này ủng hộ hướng tiếp cận của đề tài.

**Các bước tiếp theo:**

1. **Phase 1:** xây dựng solver, bộ kiểm tra lệnh (bao gồm kiểm tra giờ đã qua) và cơ chế chấm tác hại tự động.
2. **Pilot (10/11):** chạy khoảng 300 câu trên tuyến thực tế. Đây là mốc quyết định chính (Go/No-go), yêu cầu đồng thời:
   - tỷ lệ sai có hại ≥ 3–5%;
   - ít nhất một tín hiệu từ solver phát hiện lỗi tốt hơn rõ rệt so với mức tự tin của mô hình.
3. **Điều chỉnh cho pilot:**
   - bổ sung câu yêu cầu áp dụng cho một điểm trong khu, để đo lỗi mở rộng phạm vi;
   - kiểm tra kỹ từng vế của câu ghép, vì cả hai câu bị loại đều mơ hồ ở vế bổ sung.

## 7. Tệp đính kèm

Thư mục `smoke/` trong gói nộp gồm:

| Tệp | Nội dung |
|---|---|
| `routes.md` | Bảng hai tuyến R1, R2 (đúng như mô hình nhìn thấy) |
| `items_draft.txt` | 50 câu yêu cầu và đáp án, bản viết tay |
| `items.jsonl` | 50 câu yêu cầu và đáp án, định dạng máy đọc |
| `outputs.jsonl` | Câu trả lời gốc của hai mô hình |
| `review.md` | Bảng đối chiếu và nhãn đánh giá từng câu |
| `GUIDE.md` | Hướng dẫn viết câu đã dùng |
