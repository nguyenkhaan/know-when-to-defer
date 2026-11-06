Author: Nguyen Kha An

Tài liệu này diễn giải ngắn gọn ý tưởng nghiên cứu *Know When to Defer: Risk-Controlled Execution of LLM-Translated Dispatcher Edits for Last-Mile Route Re-planning*. Mô tả chính thức, danh mục tài liệu kiểm chứng và kế hoạch thực hiện nằm trong `MoTaDeTai.md`. Cập nhật 05/11/2026 theo kết quả đánh giá tính mới ngày 04/11/2026.

# Tổng quan ý tưởng

Nghiên cứu xây dựng một **lớp kiểm soát rủi ro** đặt giữa LLM và solver, dùng khi tự động thực thi các chỉnh sửa tuyến giao hàng mà LLM diễn giải từ yêu cầu của điều phối viên.

Trong ngày giao hàng, điều phối viên thường xuyên phải sửa kế hoạch đang chạy: đổi khung giờ giao, hủy một điểm dừng, yêu cầu giao điểm A trước điểm B, hoặc yêu cầu tài xế về kho trước một giờ nhất định. LLM có thể chuyển các yêu cầu bằng ngôn ngữ tự nhiên này thành lệnh có cấu trúc để solver tối ưu lại tuyến.

Vai trò của từng thành phần:

- **LLM** dịch yêu cầu thành lệnh chỉnh sửa theo một ngôn ngữ lệnh JSON giới hạn (edit DSL), không sinh code tự do.
- **Solver** (OR-Tools, bài toán TSPTW) áp lệnh vào kế hoạch hiện tại và giải lại, có warm-start từ kế hoạch cũ và phạt độ lệch so với kế hoạch cũ.
- **Cơ chế kiểm soát rủi ro** tính điểm rủi ro `s` cho lệnh, chủ yếu từ **phản hồi của solver**, rồi so với ngưỡng `λ`: nếu `s ≤ λ` thì tự động thực thi, ngược lại chuyển cho người duyệt. Ngưỡng `λ` được chọn bằng Conformal Risk Control (CRC) để tỷ lệ gây hại không vượt mức mục tiêu `α`.

**Đầu vào**

- Kế hoạch tuyến hiện tại.
- Yêu cầu bằng ngôn ngữ tự nhiên.
- Mức rủi ro mục tiêu `α`.

**Đầu ra**

- Quyết định: thực thi hoặc chuyển người duyệt.
- Điểm rủi ro `s`.
- Kế hoạch mới (nếu lệnh được thực thi).

**Các loại lệnh trong DSL (dự kiến):** `set_time_window(stop, a, b)`, `remove_stop`, `precedence(i, j)`, `driver_end_time(t)`, `avoid_zone_until(z, t)`, `deadline(stop, t)`. (`service_time` đã bỏ 07/11: đổi dữ liệu, không phải ràng buộc.) Danh sách cuối sẽ chốt ở tuần 1 (6–8 loại).

**Phạm vi MVP:** chỉ chỉnh sửa trên **một tuyến (một xe)** của bộ dữ liệu Amazon Last Mile Routing Research Challenge 2021 (LMRC). Yêu cầu kiểu "chuyển đơn sang tài xế B" nằm ngoài MVP, vì ma trận thời gian di chuyển chỉ có trong nội bộ từng tuyến.

## Bài toán giải quyết

Lỗi cú pháp không phải rủi ro chính, vì kiểm tra định dạng bắt được dễ. Rủi ro chính là **lỗi ngữ nghĩa nhưng vẫn hợp lệ về kỹ thuật**: lệnh đúng định dạng, dùng đúng tên điểm dừng, solver giải thành công, nhưng nội dung không đúng ý điều phối viên. Ví dụ:

- Chọn nhầm điểm dừng.
- Hiểu ngược "sau 15 giờ" thành "trước 15 giờ" (đảo chiều ràng buộc). Lỗi đảo dấu bất đẳng thức kiểu này đã xuất hiện thật trong user study của MeetMate ("meeting needs to start after 11am").
- Đảo quan hệ thứ tự giữa hai điểm dừng.
- Bỏ sót một phần của yêu cầu gồm nhiều điều kiện.
- Thêm ràng buộc mà điều phối viên không yêu cầu.

Solver vẫn trả về kế hoạch khả thi trong các trường hợp này, vì solver chỉ kiểm tra những ràng buộc LLM đưa vào. Nó không biết các ràng buộc đó đã diễn giải sai ý định ban đầu. Lỗi càng khó lộ khi ràng buộc bị dịch sai **không binding** trên kế hoạch hiện tại, tức là kế hoạch cũ tình cờ đã thỏa ràng buộc sai. Khi đó lệnh sai trông hoàn toàn vô hại nếu chỉ nhìn vào chính lệnh: **tác hại chỉ lộ ra ở mức kế hoạch**.

Câu hỏi trung tâm:

> Với mỗi lệnh chỉnh sửa tuyến do LLM diễn giải, làm thế nào để quyết định lệnh đó đủ an toàn để tự động thực thi hay cần chuyển cho con người, sao cho tỷ lệ gây hại được kiểm soát dưới mức `α`?

**Câu hỏi nghiên cứu:**

- **RQ1.** LLM dịch sai ngữ nghĩa với tần suất bao nhiêu, theo loại lệnh và mức độ mơ hồ? Bao nhiêu phần trăm lỗi gây tác hại vận hành thực sự, bao nhiêu phần trăm vô hại, bao nhiêu phần trăm là lỗi không binding?
- **RQ2 (trọng tâm).** Các tín hiệu kiểm chứng dựa trên solver có dự báo lỗi tốt hơn các tín hiệu chỉ từ LLM (độ tự tin tự khai, xác suất token, self-consistency, LLM tự chấm lệnh) không?
- **RQ3.** Với ngưỡng chọn bằng CRC, tỷ lệ "thực thi và gây hại" có giữ ≤ `α` mà vẫn tự động hóa cao không? Một `α` chung có che giấu vi phạm ở những loại lệnh hiếm không? Bảo đảm còn đứng được không khi phân phối yêu cầu thay đổi (điều phối viên mới, cách diễn đạt mới, loại yêu cầu mới)?

**Tác hại được đánh giá ở mức kế hoạch**, không bằng cách so chuỗi văn bản hay JSON với đáp án. Một kế hoạch do lệnh của LLM tạo ra bị gán nhãn **gây hại** khi:

- **R1:** vi phạm ràng buộc của lệnh chuẩn (gold edit), ví dụ khung giờ, thứ tự hoặc giờ về kho;
- **R2:** ghé sai tập điểm so với kế hoạch đúng, ví dụ bỏ nhầm điểm, hoặc bỏ một điểm trong khi yêu cầu chỉ là dời giờ; hoặc
- **R3:** tệ hơn kế hoạch tối ưu dưới gold edit quá ngưỡng `ε` (phút đi thêm, phút trễ).

Như vậy, một lệnh dịch sai nhưng không vi phạm luật nào được tính là **lỗi vô hại**. Lệnh lỗi định dạng hoặc solver báo không giải được thì không được thực thi và luôn chuyển cho người duyệt. RQ1 tách riêng hai loại này.

## Ví dụ minh họa

Một tài xế đang chạy tuyến sau:

| Thứ tự | Điểm giao            | Giờ dự kiến |
| ------ | -------------------- | ----------: |
| 1      | Nhà thuốc Minh Châu  |       13:20 |
| 2      | Bệnh viện An Bình    |       14:10 |
| 3      | Trường Nguyễn Du     |       14:45 |
| 4      | Cửa hàng Thành Công  |       15:25 |

Điều phối viên nhập: *"Bệnh viện An Bình chỉ nhận hàng từ 15 giờ trở đi."*

Lệnh đúng (gold edit):

```json
{
  "operation": "set_time_window",
  "stop": "Bệnh viện An Bình",
  "start": "15:00",
  "end": "<giờ kết thúc ca>"
}
```

Yêu cầu không nêu giờ kết thúc, nên cận trên lấy theo quy ước chung của benchmark (ví dụ giờ kết thúc ca). Quy ước này phải cố định khi sinh gold edit để nhãn có tính tái lập.

Áp lệnh đúng, solver đổi tuyến thành *Nhà thuốc → Trường Nguyễn Du → Bệnh viện An Bình → Cửa hàng*, bệnh viện được giao lúc khoảng 15:10, đúng yêu cầu.

Nếu LLM hiểu nhầm thành "phải giao trước 15 giờ", nó sẽ tạo lệnh:

```json
{
  "operation": "set_time_window",
  "stop": "Bệnh viện An Bình",
  "start": "00:00",
  "end": "15:00"
}
```

Lệnh này đúng cú pháp, và solver giải thành công. Tuyến cũ giao bệnh viện lúc 14:10, đã thỏa ràng buộc sai, nên solver giữ nguyên kế hoạch và báo khả thi. Thực tế kế hoạch này giao **sớm 50 phút** so với yêu cầu thật, tức vi phạm gold edit, nên được gán nhãn **gây hại**. Đây đúng là trường hợp ràng buộc sai không binding mà phần trên đã nêu.

Các tín hiệu kiểm chứng (RQ2) có thể bắt được lỗi này. Hai tín hiệu đầu dựa trên solver và là phần đóng góp chính:

- **Probe làm ràng buộc trở nên binding:** dựng tình huống mà các cách hiểu khác nhau cho ra kế hoạch khác nhau (ví dụ đặt bệnh viện vào thời điểm sau 15:00), để lộ ra lệnh nào thực sự có hiệu lực.
- **Độ thay đổi kế hoạch so với phạm vi yêu cầu:** yêu cầu nói về giờ giao của bệnh viện nhưng kế hoạch không đổi gì là dấu hiệu đáng nghi.
- **Đồng thuận giữa nhiều lần dịch (self-consistency):** lấy mẫu nhiều lần, đo mức độ các lệnh khớp nhau.
- **Dịch ngược (back-translation):** chuyển lệnh về câu tự nhiên ("giao trước 15:00") rồi kiểm tra có khớp nghĩa với yêu cầu gốc không.

Mức độ mơ hồ và loại lệnh được dùng để phân tầng kết quả (RQ1), để hiệu chỉnh ngưỡng theo loại lệnh và để thiết kế thí nghiệm dịch chuyển phân phối (RQ3).

Nếu điểm rủi ro vượt ngưỡng, hệ thống dừng lại và hỏi điều phối viên: *"Bạn muốn Bệnh viện An Bình chỉ được giao từ 15:00 trở đi, đúng không?"*

## Kiểm soát rủi ro

CRC và các biến thể ở đây là **công cụ chuẩn**, không phải đóng góp mới.

- **Chính – rủi ro kết hợp** `E[1{thực thi ∧ gây hại}] ≤ α`: loss đơn điệu theo ngưỡng, nên áp dụng được CRC.
- **Theo loại lệnh:** nếu tỷ lệ lỗi gốc `μ` chênh lệch lớn giữa các loại lệnh, hiệu chỉnh ngưỡng riêng cho từng loại (theo hướng Role-Stratified CRC), vì một `α` chung có thể che giấu vi phạm ở loại hiếm nhưng dễ sai.
- **Dịch chuyển phân phối:** calibrate trên tuyến của một số trạm, kiểm tra trên trạm khác, và báo cáo trung thực khi bảo đảm bị phá vỡ. Chia dữ liệu theo tuyến, vì các yêu cầu trên cùng tuyến phụ thuộc nhau.
- **Rủi ro có điều kiện** `P(gây hại | thực thi) ≤ α`: loss **không đơn điệu**, không áp CRC được (CRC, Prop. 1). Đã cắt khỏi bài (07/11/2026).
- **Mở rộng (ngoài MVP):** cập nhật ngưỡng online khi con người chỉ kiểm tra ngẫu nhiên một phần lệnh đã thực thi.

## Rủi ro lớn nhất

LLM có thể gần như không dịch sai khi yêu cầu được nói tường minh (ReOpt-LLM báo update correctness 100% trên 30 case). Nếu tỷ lệ gây hại gốc `μ` nhỏ hơn `α`, CRC sẽ cho thực thi gần như tất cả và bài không còn gì để kiểm soát. Vì vậy pilot tuần 1 dồn mẫu vào yêu cầu mơ hồ và yêu cầu ghép, chạy thêm một LLM mở nhỏ (M1, `qwen/qwen3.5-9b`, gọi qua API), báo `μ` theo từng loại lệnh, và đo riêng tỷ lệ lỗi không binding. Chi tiết tiêu chí go/no-go ở `MoTaDeTai.md`, Mục 6.

## Đóng góp dự kiến

1. **Định nghĩa bài toán:** hình thức hóa việc thực thi có kiểm soát rủi ro cho các chỉnh sửa do LLM dịch trên một kế hoạch tuyến last-mile đang chạy, với loss là **tác hại vận hành ở mức kế hoạch**.
2. **Benchmark:** tập yêu cầu chỉnh sửa tuyến bằng ngôn ngữ tự nhiên trên các tuyến LMRC thực. Gold edit được sinh trước câu chữ, nên nhãn có tính tái lập. Câu được diễn đạt ở 3 mức mơ hồ: tường minh, tham chiếu gián tiếp, ghép nhiều yêu cầu hoặc ẩn ý.
3. **Tín hiệu kiểm chứng từ solver, không cần gold (đóng góp chính):** chứng minh bằng ablation rằng probe binding và độ thay đổi kế hoạch cải thiện đường risk–coverage so với tín hiệu chỉ từ LLM, đặc biệt với lỗi không binding; kèm phân tích bảo đảm CRC theo loại lệnh và dưới dịch chuyển phân phối.

**Không phải đóng góp mới:**

- LLM dịch yêu cầu thành patch cho mô hình tối ưu (ReOpt-LLM, OptiGuide đã làm).
- Cơ chế "conformal + từ chối/hỏi người" cho LLM (KnowNo, conformal abstention).
- Khung CRC chặn hành động "thực thi ∧ gây hại", phân biệt rủi ro kết hợp với có điều kiện, kiểm tra dưới shift. CORA (2026) đã làm cho agent GUI. Khác biệt của đề tài: tác hại tính ở mức kế hoạch thay vì từng hành động, và điểm rủi ro lấy từ phản hồi solver thay vì một mô hình guardian phải huấn luyện.

Tóm lại, nghiên cứu đề xuất một lớp an toàn giữa LLM và solver, ngăn các lệnh bị diễn giải sai nhưng vẫn hợp lệ về kỹ thuật được tự động đưa vào vận hành, kèm một mức rủi ro có thể cam kết.
