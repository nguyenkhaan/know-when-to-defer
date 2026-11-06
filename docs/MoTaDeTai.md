# MÔ TẢ ĐỀ TÀI NGHIÊN CỨU

**Hội nghị mục tiêu:** IEEE MOST 2027, hạn nộp **01/12/2026**, tối đa 8 trang, IEEE format, double-blind.
**Tài liệu liên quan:** bản diễn giải ngắn `DienGiaiYTuong.md`; PDF tham khảo trong `../reference-documents/`.
**Cập nhật:** 05/11/2026, đồng bộ kết quả đánh giá tính mới ngày 04/11/2026 (bổ sung CORA, Role-Stratified CRC; định vị lại đóng góp; kế hoạch pilot tuần 1). 06/11/2026: §2.2 đủ 3 luật tác hại R1–R3 theo spec 09; §2.3 thêm điều kiện áp CRC Thm. 1 và cận coverage có `π`; ngưỡng theo loại dùng loại `ĉ` của lệnh LLM sinh.

---

## 0. Tên đề tài

- **Tiếng Anh:** *Know When to Defer: Risk-Controlled Execution of LLM-Translated Dispatcher Edits for Last-Mile Route Re-planning*
- **Tiếng Việt:** Kiểm soát rủi ro khi tự động thực thi các chỉnh sửa tuyến giao hàng chặng cuối do LLM dịch từ yêu cầu của điều phối viên

**Tóm tắt một câu:** Khi LLM dịch yêu cầu sửa tuyến của điều phối viên thành lệnh cho solver, hệ thống phải quyết định lệnh nào được **tự động thực thi** và lệnh nào phải **chuyển cho người duyệt**, sao cho tỷ lệ lệnh được thực thi nhưng gây hại vận hành không vượt mức `α` cam kết trước. Điểm rủi ro được xây từ **phản hồi của solver**, không cần đáp án chuẩn lúc triển khai.

---

## 1. Tổng quan nghiên cứu

### 1.1. Bối cảnh

Trong ngày giao hàng, kế hoạch tuyến liên tục phải sửa: khách đổi giờ nhận, đơn bị hủy, điểm này phải giao trước điểm kia, tài xế phải về kho sớm. Điều phối viên diễn đạt những thay đổi này bằng ngôn ngữ tự nhiên, ví dụ "khách ở điểm 17 chỉ nhận sau 15h". Trong khi đó, solver chỉ hiểu ràng buộc có cấu trúc.

LLM lấp được khoảng trống này: nó dịch câu nói thành lệnh chỉnh sửa, rồi solver tối ưu lại. Hướng "LLM là người mô hình hóa" đang phát triển nhanh (OptiGuide, DRoC, ARS, Constraint Injection, ReOpt-LLM). Survey VRP–LLM năm 2026 cũng nêu lớp tương tác điều phối viên ↔ solver là một hướng tương lai [P2].

### 1.2. Động lực

Rủi ro chính **không phải lỗi cú pháp**, vì loại lỗi này dễ bắt. Rủi ro chính là **lệnh sai ý nhưng vẫn chạy được**. Solver chỉ kiểm tra các ràng buộc mà LLM đưa vào, nên nếu LLM hiểu ngược "sau 15h" thành "trước 15h", solver vẫn trả về một kế hoạch khả thi, trông hợp lệ, nhưng sai ý định. Lỗi đảo dấu bất đẳng thức kiểu này đã được ghi nhận thực tế trong user study của MeetMate [P8, Table 2]. Tác giả OptiGuide tự ghi nhận hiện tượng code *"runs smoothly, but it may be totally wrong"* và cho rằng tối ưu tương tác cần *"more comprehensive safeguards"* [P1]. Muốn tự động hóa thật, phải có cơ chế quyết định **khi nào tin LLM, khi nào hỏi lại người**, kèm một mức rủi ro có thể cam kết.

### 1.3. Mục tiêu

1. Hình thức hóa bài toán thực thi có kiểm soát rủi ro cho chỉnh sửa tuyến do LLM dịch, với loss là **tác hại vận hành ở mức kế hoạch**.
2. Xây dựng benchmark yêu cầu sửa tuyến trên tuyến last-mile thực (LMRC 2021), có nhãn đúng tái lập.
3. **(Trọng tâm phương pháp)** Thiết kế các **tín hiệu kiểm chứng dựa trên phản hồi solver, không cần gold**, và chứng minh bằng ablation rằng chúng tạo ra khác biệt so với tín hiệu chỉ từ LLM.
4. Dùng CRC như công cụ chuẩn để chọn ngưỡng thực thi; đánh giá bảo đảm theo từng loại lệnh và dưới dịch chuyển phân phối yêu cầu.

---

## 2. Phát biểu bài toán

### 2.1. Hình thức hóa

Với mỗi mẫu `i`:

| Ký hiệu | Ý nghĩa |
|---|---|
| `P_i` | Kế hoạch tuyến hiện tại (trình tự điểm dừng, giờ dự kiến) |
| `q_i` | Yêu cầu bằng ngôn ngữ tự nhiên của điều phối viên |
| `e*_i` | Lệnh chỉnh sửa chuẩn (gold edit), chỉ biết khi xây benchmark |
| `c_i` | Loại lệnh của `e*_i` (một trong 6–8 loại DSL) |
| `ê_i = LLM(P_i, q_i)` | Lệnh do LLM sinh, theo DSL |
| `P̂_i = Solver(P_i, ê_i)` | Kế hoạch mới khi áp lệnh của LLM |
| `P*_i = Solver(P_i, e*_i)` | Kế hoạch tối ưu khi áp gold edit |
| `h_i ∈ {0,1}` | Nhãn tác hại của `P̂_i` (định nghĩa ở 2.2) |
| `s_i` | Điểm rủi ro, tính **không cần** `e*_i` |
| `λ` | Ngưỡng: thực thi nếu `s_i ≤ λ`, ngược lại chuyển người duyệt |
| `μ` | Tỷ lệ gây hại gốc `E[h]` khi luôn thực thi |

- **Đầu vào:** `P_i`, `q_i`, mức rủi ro `α`.
- **Đầu ra:** quyết định thực thi hoặc chuyển duyệt, điểm `s_i`, và `P̂_i` nếu thực thi.

### 2.2. Định nghĩa tác hại

`h_i = 1` khi xảy ra ít nhất một trong ba điều sau (chi tiết và tham số: spec 09):

1. **R1 · Vi phạm đáp án:** `P̂_i` vi phạm một ràng buộc của `e*_i` (khung giờ, thứ tự, giờ về kho, khu cấm, điểm phải bỏ…) quá `tol_min`, tức yêu cầu thật không được thực hiện;
2. **R2 · Sai tập điểm:** tập điểm được ghé trong `P̂_i` khác trong `P*_i` (bỏ nhầm điểm, hoặc bỏ một điểm mà yêu cầu không hề đòi bỏ); hoặc
3. **R3 · Chi phí vượt:** `cost(P̂_i) − cost(P*_i) > ε`, với `cost` = phút di chuyển + phạt phút trễ, `ε = max(5 phút, 2% · cost(P*_i))`.

Cần R2 vì nếu thiếu nó, lỗi "bỏ điểm thay vì dời giờ" (loại lỗi nhiều nhất của M1 ở smoke test) bị chấm vô hại: khung giờ của đáp án gắn với một điểm không còn trong tuyến nên R1 không bắt, và tuyến ngắn hơn nên R3 không bắt.

Lệnh lỗi parse hoặc bị solver báo infeasible thì **không được thực thi** (`h_i` không xác định), luôn chuyển người duyệt, nhưng vẫn nằm trong mẫu số khi tính coverage và rủi ro.

Hệ quả là một lệnh sai nhưng không vi phạm luật nào thì được tính là **lỗi vô hại** (`h_i = 0`). Cách chấm này khác các benchmark hiện có, vốn chấm theo trùng giá trị mục tiêu [P5], Pass@1 [P3] hay update correctness [P4]. Nó cũng khác CORA [P21], nơi tác hại được gán cho từng hành động: ở đây một lệnh sai có thể đúng cú pháp, khả thi, thậm chí không làm kế hoạch thay đổi (khi ràng buộc sai không binding), nên tác hại **chỉ nhìn thấy ở mức kế hoạch**.

### 2.3. Các dạng rủi ro cần kiểm soát

| Dạng | Công thức | Công cụ | Vai trò trong bài |
|---|---|---|---|
| Rủi ro kết hợp | `E[1{s ≤ λ} · h] ≤ α` | CRC [P11] Thm. 1 (xem ghi chú điều kiện bên dưới) | **Chính** |
| Rủi ro theo loại lệnh | `E[1{s ≤ λ_ĉ} · h \| x = 1, ĉ] ≤ α` với mỗi loại `ĉ` của **lệnh LLM sinh** | CRC hiệu chỉnh riêng từng nhóm `ĉ`, theo hướng Role-Stratified CRC [P22] | Dùng nếu pilot cho thấy `μ` chênh lệch lớn giữa các nhóm `ĉ` |
| Rủi ro có điều kiện | `P(h = 1 \| s ≤ λ) ≤ α` | LTT [P12], cận selective classification [P16] (loss **không đơn điệu**, không dùng CRC được — CRC Prop. 1 [P11]) | **Không làm** (đã cắt 07/11/2026); không báo cáo trong paper |

Phân biệt rủi ro kết hợp với rủi ro có điều kiện, và kiểm tra bảo đảm dưới shift, **đã có trong CORA** [P21] (chỉ số HR và mHR, weighted CRC). Đề tài dùng các công cụ này để đánh giá, không claim mới. Báo cáo sai loại bảo đảm vẫn là lỗi reviewer dễ bắt nhất.

**Điều kiện áp CRC Thm. 1 [P11].** Định lý yêu cầu loss *không tăng* theo tham số, liên tục phải, bị chặn bởi `B`, và `L(λmax) ≤ α` tại mức thận trọng nhất. Loss của đề tài `L_i(λ) = x_i · h_i · 1{s_i ≤ λ}` (`x_i = 1` nếu lệnh thực thi được) lại *không giảm* theo `λ`, nên áp định lý cho `θ = −λ`, với `B = 1`. Mức thận trọng nhất là `λ = −∞` (chuyển duyệt tất cả), có loss 0, vì vậy lưới ngưỡng phải luôn chứa `−∞`. Lưới ngưỡng chỉ gồm điểm calibration (spec 12 §2.1) cho ngưỡng bằng hoặc chặt hơn CRC chuẩn, nên bảo đảm vẫn giữ. Rủi ro có điều kiện không đơn điệu theo `λ` (CRC Prop. 1), nên không kiểm soát; LTT đã cắt (07/11/2026).

**Loại dùng để chọn ngưỡng là loại của lệnh LLM sinh (`ĉ`), không phải của đáp án (`c`).** Lúc triển khai không có đáp án, nên ngưỡng `λ_c` theo loại đáp án không áp được cho yêu cầu mới. Nhóm theo `ĉ` đọc được từ chính `ê`, và CRC chạy riêng trong từng nhóm vẫn giữ bảo đảm `E[L | x = 1, ĉ] ≤ α` (chỉ xét lệnh thực thi được, `x = 1`, vì lệnh không thực thi được luôn chuyển duyệt). Rủi ro theo loại đáp án `c` chỉ tính để phân tích trong `runs/`, không đưa lên paper. Quyết định ngày 06/11/2026.

**Lý do cần hiệu chỉnh theo loại lệnh:** Role-Stratified CRC [P22] chỉ ra rằng nếu loại `c` chiếm tần suất `p_c`, thì muốn bảo đảm `α` cho riêng loại đó bằng một ngưỡng chung, ngân sách tổng phải co lại còn `α · p_c`. Một `α` chung có thể che giấu vi phạm tập trung ở các loại lệnh hiếm nhưng dễ sai.

**Cận dưới cho tỷ lệ chuyển duyệt.** Trên `N` yêu cầu, `μ = Σ x_i h_i / N` (tỷ lệ gây hại khi thực thi mọi lệnh thực thi được, spec 13 §14) và `π = 1 − Σ x_i / N` (tỷ lệ lệnh lỗi parse hoặc infeasible, luôn bị chuyển duyệt). Nếu `μ ≤ α`, CRC cho thực thi gần như tất cả và bài không còn gì để kiểm soát. Nếu `μ > α`, kể cả với điểm rủi ro hoàn hảo:

- rủi ro kết hợp cần chuyển duyệt thêm ít nhất `μ − α` mẫu, nên coverage tối đa là **`1 − π − max(0, μ − α)`**.

Từ đó suy ra tỷ lệ tự động hóa tối đa có thể đạt, dùng làm mốc so sánh cho điểm rủi ro thực tế và làm tiêu chí go/no-go (Mục 6).

### 2.4. Phạm vi (MVP)

- Chỉ chỉnh sửa trên **một tuyến (một xe)** của LMRC. Chuyển đơn giữa các xe nằm ngoài phạm vi, vì ma trận thời gian chỉ có trong nội tuyến [P20].
- LLM chỉ xuất **DSL JSON**, không xuất code tự do.
- Yêu cầu đến từng lần một. Phần cập nhật ngưỡng online là mở rộng, không thuộc MVP.

### 2.5. Giả định

- Dữ liệu calibration và test **hoán đổi được (exchangeable)** cho bảo đảm CRC. Giả định này **không** đúng với các phiên điều phối tuần tự, nên phải kiểm tra bằng thí nghiệm dịch chuyển phân phối (RQ3) và báo cáo trung thực.
- Các yêu cầu trên cùng một tuyến phụ thuộc nhau, nên chia calibration/test **theo tuyến**, không theo từng yêu cầu (tương tự CORA tách split theo khối [P21]).
- Gold edit phản ánh đúng ý định của câu. Điều này được bảo đảm bằng cách sinh gold edit trước rồi mới diễn đạt thành câu, cộng kiểm duyệt thủ công một mẫu con.
- Câu sinh bằng template và LLM paraphrase có thể dễ hơn ngôn ngữ thật của điều phối viên. Đây là giới hạn đã biết, cần nêu trong paper.

---

## 3. Câu hỏi nghiên cứu và giả thuyết

| RQ | Câu hỏi | Giả thuyết (cần kiểm chứng bằng thực nghiệm) |
|---|---|---|
| **RQ1** | Trên tuyến last-mile thực, LLM dịch sai ngữ nghĩa yêu cầu sửa tuyến với tần suất bao nhiêu, theo loại lệnh và mức mơ hồ? Bao nhiêu lỗi gây tác hại thực sự, bao nhiêu lỗi không binding (kế hoạch không đổi dù lệnh sai)? | **H1:** Tỷ lệ lỗi có hại tăng theo mức mơ hồ. Ở mức mơ hồ 2–3 và yêu cầu ghép, mô hình mạnh nhất vẫn có `μ` ≥ 3–5%, và `μ` chênh lệch rõ giữa các loại lệnh. Một phần đáng kể lỗi là vô hại, nên nhãn mức kế hoạch khác nhãn mức chuỗi ký tự. **Đây là giả thuyết rủi ro nhất** (xem Mục 6). |
| **RQ2** *(trọng tâm)* | Tín hiệu kiểm chứng dựa trên phản hồi solver có dự báo lỗi có hại tốt hơn các tín hiệu chỉ từ LLM (độ tự tin tự khai, log-prob, self-consistency, LLM tự chấm lệnh) không? | **H2:** Ít nhất một tín hiệu dựa trên solver (probe binding, độ thay đổi kế hoạch) có AUROC cao hơn rõ so với verbalized confidence, đặc biệt trên nhóm lỗi không binding. Kết hợp các tín hiệu cho đường risk–coverage tốt hơn chỉ dùng tín hiệu từ LLM. |
| **RQ3** | Với ngưỡng chọn bằng CRC, rủi ro có giữ ≤ `α` mà vẫn tự động hóa cao không? Một `α` chung có che giấu vi phạm ở loại lệnh hiếm không? Bảo đảm còn giữ được khi phân phối yêu cầu đổi không? | **H3:** Trên split ngẫu nhiên, tần suất vi phạm `α` qua 100 split nằm trong mức lý thuyết cho phép. Ngưỡng chung có thể vi phạm `α` ở loại lệnh có `μ` cao; hiệu chỉnh theo loại khắc phục được với chi phí coverage. Trên split theo loại yêu cầu, bảo đảm có thể bị phá vỡ. |

---

## 4. Phương pháp đề xuất

### 4.1. Pipeline

```
Yêu cầu q + kế hoạch P
        │
        ▼
  LLM → lệnh DSL ê  (lấy k mẫu để tính đồng thuận)
        │
        ▼
  OR-Tools TSPTW: áp ê, giải lại (warm-start từ P, phạt độ lệch) → P̂
        │
        ▼
  Tính tín hiệu kiểm chứng (từ solver + từ LLM) → điểm rủi ro s
        │
        ▼
  s ≤ λ ?  ── có ──► thực thi P̂
        │
       không
        ▼
  Chuyển người duyệt ("Bạn muốn … đúng không?")
```

### 4.2. Ngôn ngữ lệnh (edit DSL)

`set_time_window(stop, a, b)`, `remove_stop(stop)`, `precedence(i, j)`, `driver_end_time(t)`, `avoid_zone_until(z, t)`, `deadline(stop, t)`. Mọi lệnh là ràng buộc lên kế hoạch; lệnh đổi dữ liệu bài toán (thời gian di chuyển, thời gian phục vụ) nằm ngoài phạm vi, nên `service_time` đã bỏ (07/11/2026). Pilot có thể bỏ thêm loại lệnh gần như không bao giờ sai.

Dùng DSL thay code tự do để thu hẹp bề mặt lỗi và để chấm điểm được. ReOpt-LLM cho thấy patch có cấu trúc tin cậy hơn hẳn sửa code trực tiếp [P4], và Drossman et al. ghi nhận chatbot đa dụng mắc *"silent modeling errors through free-form code"* [P9]. Mỗi lệnh DSL là một tool call có cấu trúc, nên có thể áp dụng trực tiếp lập luận hiệu chỉnh theo loại của [P22].

### 4.3. Sinh benchmark có nhãn tái lập

1. Lấy tuyến LMRC, trích kế hoạch `P` (trình tự quan sát, ma trận transit nội tuyến, service time, khung giờ nếu có).
2. Lấy mẫu một **gold edit** `e*` hợp lệ cho tuyến đó. Ghi lại ràng buộc của `e*` có **binding** trên `P` hay không, để phân tích riêng nhóm lỗi không binding.
3. Diễn đạt `e*` thành câu `q` bằng template cộng LLM paraphrase, theo **3 mức mơ hồ**:
   - **Mức 1 – Tường minh:** "Điểm 17 chỉ nhận từ 15:00." Chỉ dùng làm mốc so sánh.
   - **Mức 2 – Tham chiếu gián tiếp:** "khách gần trạm nhất", "trong 2 tiếng tới", "buổi chiều" (MeetMate ghi nhận LLM và người hiểu khác nhau về "buổi chiều bắt đầu lúc nào" [P8]).
   - **Mức 3 – Ghép hoặc ẩn ý:** một nửa là nhiều yêu cầu trong một câu (lệnh ghép 2–3 op), một nửa là một yêu cầu nêu qua lý do thay vì nói thẳng.
   Dồn phần lớn mẫu vào mức 2–3 và yêu cầu ghép, vì ở mức 1 LLM gần như không sai.
4. Kiểm duyệt thủ công khoảng 300 câu, báo cáo inter-annotator agreement.
5. Quy mô: 6–8 loại lệnh × 3 mức mơ hồ (20/40/40), bộ chính ~3.000 yêu cầu, trong đó ~600 lệnh ghép; mỗi loại lệnh ≥ 250 câu một op (spec 08 §3).

Gold edit có trước câu chữ, nên nhãn đúng **tái lập được** mà không cần người gán nhãn cho từng mẫu.

### 4.4. Tín hiệu kiểm chứng (các thành phần của `s`)

| Tín hiệu | Cách tính | Lỗi mà tín hiệu nhắm tới | Cơ sở |
|---|---|---|---|
| Probe làm ràng buộc binding *(solver)* | Dựng biến thể instance hoặc so các diễn giải ứng viên sao cho ràng buộc trở nên chặt, rồi xem kế hoạch có phân biệt được các cách hiểu không | Đảo chiều, thừa hoặc thiếu ràng buộc không binding | [P3] §1; [P8] §5.3 (đánh giá trên hai horizon để lộ lỗi không hiện ra trên horizon nhỏ); [P7] §3.1 |
| Độ thay đổi kế hoạch so với phạm vi yêu cầu *(solver)* | So mức thay đổi của `P̂` so với `P` (logical edits, tỷ lệ giữ nguyên, độ lệch giờ, km) với phạm vi mà câu yêu cầu đề cập | Lệnh không có hiệu lực (như ví dụ bệnh viện), lệnh tác động sai điểm | [P10] §2.3 |
| Đồng thuận nhiều mẫu (self-consistency) *(LLM)* | Lấy k lệnh DSL, chuẩn hóa JSON, đo tỷ lệ khớp ngữ nghĩa với lệnh đa số | Mơ hồ, chọn nhầm điểm | [P18], [P14] |
| Dịch ngược (back-translation) *(LLM)* | Chuyển `ê` về câu tự nhiên, kiểm tra khớp nghĩa với `q` | Đảo chiều, sai điểm | Đề xuất của đề tài |
| Baseline: độ tự tin tự khai, log-prob | Lấy trực tiếp từ LLM | — | [P19] |
| Baseline: LLM tự chấm `(q, ê)` không dùng solver | LLM đánh giá lệnh có đúng ý không, chỉ từ câu và lệnh | — | Tương ứng "guardian" chấm theo hành động của CORA [P21], nhưng không cần huấn luyện |

Tín hiệu đánh dấu *(solver)* là phần đóng góp chính, không cần gold lúc triển khai. Các tín hiệu được tổng hợp thành `s` bằng một mô hình đơn giản (ví dụ hồi quy logistic) học trên một phần dữ liệu tách riêng khỏi calibration và test. Đây là lựa chọn thiết kế, sẽ chốt sau pilot.

### 4.5. Kiểm soát rủi ro

- **(i) Chính – rủi ro kết hợp:** chọn `λ` bằng CRC [P11] Thm. 1.
- **(ii) Theo loại lệnh:** nếu pilot cho thấy `μ` chênh lệch lớn giữa các loại, hiệu chỉnh `λ_ĉ` riêng cho từng loại `ĉ` của lệnh LLM sinh [P22] (xem §2.3). So sánh với ngưỡng chung về tỷ lệ vi phạm từng loại và coverage. Đây cũng là một điểm khác so với CORA.
- **(iii) Dịch chuyển phân phối:** calibrate trên tuyến của một số trạm, test trên trạm khác (spec 13 §8). Chỉ mô tả, không sửa.
- **(iv) Rủi ro có điều kiện (LTT):** đã cắt 07/11/2026 để paper tập trung vào tín hiệu solver.
- **(Mở rộng, ngoài MVP)** Cập nhật ngưỡng online khi người chỉ kiểm tra ngẫu nhiên một phần lệnh đã thực thi; ACI [P17] là baseline; khi người chỉ kiểm tra ngẫu nhiên thì cần biến thể ACI cho phản hồi gián đoạn (sẽ tra cứu khi làm phần mở rộng). Có thể dùng bộ mô phỏng stakeholder có utility ẩn của [P9] để mô phỏng điều phối viên trả lời câu hỏi xác nhận, đo giá trị đầu–cuối của việc chuyển duyệt.

### 4.6. Thiết lập thí nghiệm

- **LLM:** hai mô hình dịch, gọi qua API vì máy không có GPU (spec 10 §2): M1 mô hình mở nhỏ `qwen/qwen3.5-9b` (có log-prob, thường sai nhiều hơn) và M2 mô hình mạnh chi phí thấp `deepseek/deepseek-v4-flash`.
- **Chia dữ liệu:** 100 lần chia calibration/test ngẫu nhiên **theo tuyến**, cộng một split theo trạm (shift).
- **Baseline:** luôn thực thi (trùng với validator chỉ kiểm tra khả thi của ReOpt-LLM [P4]); độ tự tin tự khai; log-prob; chỉ self-consistency; LLM tự chấm không dùng solver (L5), LLM chấm có xem thay đổi kế hoạch (L6); bộ chấm học G1 (spec 13 §12).
- **Chỉ số:** tỷ lệ tự động hóa (coverage), so với mức tối đa lý thuyết ở Mục 2.3; tỷ lệ thực thi-gây-hại thực tế so với `α`, tổng và **theo từng loại lệnh**, kèm tần suất vi phạm qua 100 split; đường risk–coverage và AURC [P16]; chi phí tác hại (km thêm, phút trễ, số khung giờ bị vi phạm); độ lệch so với kế hoạch cũ.
- **Ablation (bắt buộc):** bỏ lần lượt từng tín hiệu, và so "chỉ tín hiệu LLM" với "LLM + tín hiệu solver", báo riêng trên nhóm lỗi không binding. Đây là bằng chứng rằng chính tín hiệu đặc thù miền tạo ra khác biệt, chứ không phải bản thân cơ chế conformal.

### 4.7. Ví dụ

Tuyến: Nhà thuốc (13:20) → **Bệnh viện (14:10)** → Trường học (14:45) → Cửa hàng (15:25). Yêu cầu: *"Bệnh viện An Bình chỉ nhận hàng từ 15 giờ trở đi."*

- **Gold edit:** `set_time_window(Bệnh viện, 15:00, <giờ kết thúc ca>)`. Solver đổi tuyến, giao bệnh viện lúc khoảng 15:10.
- **LLM dịch sai:** `set_time_window(Bệnh viện, 00:00, 15:00)`. Kế hoạch cũ (14:10) đã thỏa ràng buộc sai, nên solver giữ nguyên và báo khả thi. Kết quả vi phạm gold edit 50 phút, tức `h = 1`.
- **Vì sao chỉ kiểm tra khả thi hay chấm từng hành động không bắt được:** lệnh đúng cú pháp, đúng tên điểm dừng, solver giải thành công, kế hoạch không đổi. Tác hại chỉ lộ ra khi so kế hoạch với ý định thật.
- **Tín hiệu bắt được lỗi:** câu yêu cầu nói đến giờ của bệnh viện nhưng kế hoạch không đổi (độ thay đổi kế hoạch); probe đặt bệnh viện vào thời điểm sau 15:00 cho thấy hai cách hiểu cho kế hoạch khác nhau; dịch ngược ra "giao trước 15:00", ngược nghĩa với câu gốc.
- Khi `s > λ`, hệ thống hỏi: *"Bạn muốn Bệnh viện An Bình chỉ được giao từ 15:00 trở đi, đúng không?"*

---

## 5. Khoảng trống nghiên cứu và tính mới

### 5.1. Kết luận định vị (đánh giá 04/11/2026)

Tính mới ở **mức bài toán** vẫn còn, nhưng khung "lớp CRC chặn các hành động được thực thi mà gây hại" đã có người làm (CORA [P21]), nên phải thu hẹp claim. Đến 04/11/2026 chưa tìm thấy công trình nào có đủ cả ba yếu tố:

- điều phối viên sửa một tuyến **đang chạy** bằng ngôn ngữ tự nhiên;
- nhãn tác hại tính **ở mức kế hoạch**;
- điểm rủi ro lấy từ **phản hồi solver**, không cần gold.

| Hạng mục | Đánh giá | Vai trò trong paper |
|---|---|---|
| Định nghĩa bài toán + loss tác hại mức kế hoạch | Còn mới | Đóng góp 1 |
| Benchmark sửa tuyến trên LMRC, gold sinh trước câu | Còn mới | Đóng góp 2 |
| Tín hiệu solver không cần gold (probe binding, độ thay đổi kế hoạch) | Còn mới, phải chứng minh bằng ablation | **Đóng góp chính** (3) |
| CRC/LTT, rủi ro kết hợp vs có điều kiện, kiểm tra dưới shift | Đã có trong CORA [P21] | Thành phần đánh giá, trích CORA |
| Một `α` chung cho mọi loại lệnh | Bị phản biện bởi Role-Stratified CRC [P22] | Hiệu chỉnh theo loại lệnh nếu `μ` chênh lệch |

### 5.2. Các vấn đề đã được giải quyết, phương pháp và hạn chế còn lại

| Nhóm | Đã giải quyết | Phương pháp | Hạn chế còn lại | Liên quan đến đề tài |
|---|---|---|---|---|
| LLM sửa mô hình tối ưu theo yêu cầu [P1], [P4], [P7] | Dịch câu hỏi what-if hoặc yêu cầu thành chỉnh sửa mô hình rồi giải lại | Sinh code [P1]; patch có cấu trúc + validator [P4]; function call + code [P7] | Safeguard chỉ kiểm tra chạy được hoặc khả thi; validator ReOpt-LLM *"does not perform a separate semantic check on the LLM's intent"* [P4, tr.52 bản arXiv v2]; trong số lỗi còn lại của o3, 65% là lỗi logic sai ý định [P7, tr.15]; đánh giá nhỏ (30 case mỗi biến thể [P4]) | **Trực tiếp:** chưa có cơ chế từ chối có bảo đảm, chưa áp dụng cho định tuyến |
| LLM xây mô hình VRP từ đầu [P3], [P5], [P6] | Sinh code solver cho nhiều biến thể VRP | RAG + self-debug [P5]; heuristic + checker [P6]; constraint injection [P3] | Chấm theo trùng giá trị mục tiêu, bỏ lọt ràng buộc không binding [P5, tr.17]; bộ kiểm chứng cần ground-truth [P3, tr.5]; chỉ xây từ đầu, không sửa kế hoạch đang chạy | **Phương pháp:** mượn ý tưởng probe nhưng phải bỏ phụ thuộc vào gold |
| Tối ưu tương tác qua hội thoại [P8], [P9], [P10] | Xếp lịch họp [P8], xếp giờ học [P9], sửa lịch trình du lịch [P10] | LLM + CP; agent mô phỏng stakeholder; so sánh replan/repair/edit | Safeguard [P8] chỉ kiểm tra đủ thông tin, trong khi user study vẫn có lỗi đảo dấu bất đẳng thức [P8, Table 2]; [P9] thừa nhận hệ thống có thể *"fails silently"*; không có bảo đảm rủi ro; [P10] xử lý gián đoạn do môi trường, không do ngôn ngữ người | **Thiết kế:** độ ổn định kế hoạch [P10], benchmark có ground truth và mô phỏng người dùng [P9] |
| Conformal / risk control cho LLM [P11]–[P15] | Bảo đảm phân phối tự do cho tập dự đoán, từ chối, factuality | CRC, LTT, KnowNo, conformal abstention, back-off | Bảo đảm marginal, giả định exchangeable; KnowNo giả định hành động thực thi được là đủ [P13, tr.9]; chưa áp cho lệnh tối ưu có tác hại vận hành | **Công cụ:** dùng đúng loại bảo đảm; không claim mới ở đây |
| Risk control cho hành động của agent [P21]–[P24] | Chặn hành động GUI gây hại với ngân sách `α` [P21]; CRC theo vai trò đối số tool call [P22]; điều kiện để CRC có ích [P23]; dịch NL → LTL có conformal và hỏi người [P24] | Guardian VLM fine-tune + CRC, HR/mHR, weighted CRC [P21]; CRC phân tầng [P22] | Tác hại gán theo từng hành động, guardian cần nhãn để huấn luyện, không có tín hiệu từ solver [P21]; rủi ro xét là prompt injection, không phải dịch sai ý [P22]; [P24] là đặc tả robot, không phải sửa kế hoạch tối ưu | **Va chạm gần nhất về khung kiểm soát rủi ro:** phải trích và định vị |
| Selective prediction và tín hiệu bất định [P16]–[P19] | Đường risk–coverage, SGR, self-consistency, verbalized confidence | — | Verbalized confidence quá tự tin, AUROC chỉ khoảng 0,52–0,61 [P19] | **Baseline và chỉ số** |
| Survey VRP–LLM [P2] | Bản đồ lĩnh vực | — | §VIII-A/B/C nêu cần giao diện kiểm chứng, lớp tương tác điều phối viên ↔ solver, dữ liệu vận hành, nhưng **không trích công trình nào** ở §VIII-B | **Bằng chứng gap** |

### 5.3. Đề tài khác các nghiên cứu hiện có ở đâu

1. **Đối tượng:** sửa một **kế hoạch tuyến đang chạy**, không xây mô hình từ đầu như [P3], [P5], [P6], và không thuộc miền chuỗi cung ứng hay xếp lịch thi như [P1], [P4].
2. **Loss:** **tác hại vận hành ở mức kế hoạch** (vi phạm ràng buộc gold, chi phí vượt `ε`), thay cho trùng giá trị mục tiêu [P5], Pass@1 [P3], update correctness [P4], "câu trả lời sai" [P13], [P14], hay tác hại gán theo từng hành động [P21].
3. **Lỗi không binding:** lệnh sai có thể khả thi và không làm kế hoạch thay đổi, nên mọi bộ chấm chỉ nhìn vào lệnh hoặc hành động đều khó bắt. Đề tài đo và phân tích riêng nhóm lỗi này.
4. **Tín hiệu:** điểm rủi ro dựa trên **phản hồi của solver**, không cần gold lúc triển khai (Constraint Injection [P3] cần gold) và không cần huấn luyện một mô hình chấm lớn (guardian của CORA [P21] cần nhãn để fine-tune).
5. **Hiệu chỉnh theo loại lệnh** (nếu pilot cho thấy `μ` chênh lệch): áp lập luận của [P22] cho lệnh chỉnh sửa tối ưu.

### 5.4. Phân loại mức độ chắc chắn của đóng góp

| Loại | Nội dung |
|---|---|
| **Đã được tài liệu xác lập (không phải đóng góp của ta)** | LLM dịch yêu cầu thành patch [P4]; conformal "hỏi người khi không chắc" [P13]; loss "không từ chối ∧ sai" với CRC [P14, tr.3 Eq. (1)–(2)]; CRC chặn hành động "thực thi ∧ gây hại", báo cả rủi ro kết hợp lẫn có điều kiện, weighted CRC cho shift, tách split theo khối [P21]; CRC phân tầng cho tool call [P22]; self-consistency là tín hiệu bất định [P18]; lỗi không binding qua mặt kiểm tra giá trị mục tiêu [P3] |
| **Gap có bằng chứng tường minh** | Lỗi ngữ nghĩa im lặng chưa được giải quyết [P1, tr.17]; [P7, tr.15]; [P9, tr.25–26]; validator không kiểm tra ngữ nghĩa [P4, tr.52 bản v2]; lớp điều phối viên ↔ solver là hướng tương lai chưa có công trình [P2, tr.13–14]; chấm theo route cost không đủ [P2, tr.13] |
| **Đóng góp đề xuất** | (1) Định nghĩa bài toán và loss tác hại mức kế hoạch; (2) benchmark trên LMRC có nhãn tái lập; (3) tín hiệu solver không cần gold, chứng minh bằng ablation, cùng phân tích bảo đảm CRC theo loại lệnh và dưới shift |
| **Giả thuyết chưa kiểm chứng** | H1–H3 (Mục 3). Đặc biệt, H1 quyết định đề tài có còn ý nghĩa không: nếu `μ ≤ α` thì không còn gì để kiểm soát |

### 5.5. Những điều không được tuyên bố và rủi ro False Novelty

- **Không** tuyên bố mới ở phần LLM dịch yêu cầu thành lệnh (ReOpt-LLM [P4], OptiGuide [P1]).
- **Không** tuyên bố mới về phương pháp UQ. CRC, LTT, KnowNo, conformal abstention [P11]–[P14] và CORA [P21] đã có.
- **Không** claim mới cho việc phân biệt rủi ro kết hợp với rủi ro có điều kiện, hay cho việc kiểm tra bảo đảm dưới shift (CORA [P21] đã làm).
- **Không** dùng con số 65% của OptiChat để gợi ý LLM hay sai: đó là tỷ lệ *trong số các lỗi*, độ chính xác tổng thể vẫn trên 80% ở phần lớn loại truy vấn [P7].
- **Không** viết "first", trừ khi đã hoàn thành tìm kiếm trên IEEE Xplore và ACM DL.
- Phải có **ablation** chứng minh tín hiệu đặc thù miền tạo khác biệt. Nếu không, bài sẽ bị xem là "bọc conformal quanh LLM" hoặc "CORA cho miền định tuyến".
- Các gap ở dạng "chưa tìm thấy" (sửa kế hoạch VRP hiện có bằng ngôn ngữ tự nhiên; benchmark sửa tuyến trên dữ liệu thực; cận rủi ro cho lệnh thực thi sai trong tái tối ưu bằng LLM) chỉ có nghĩa là **chưa tìm thấy trong phạm vi tra cứu đến 04/11/2026**.

---

## 6. Tính khả thi

| Khía cạnh | Đánh giá | Ghi chú |
|---|---|---|
| **Dữ liệu** | Tốt | LMRC 2021 công khai trên AWS Open Data, giấy phép CC BY-NC 4.0: 6.112 route huấn luyện cộng 3.072 route đánh giá [P20, tr.3]. Có trình tự quan sát, zone, khung giờ, service time, transit time nội tuyến [P20, Table 1]. Hạn chế: khung giờ thưa, trung bình chỉ 18,6/238,5 gói có khung giờ mỗi tuyến [P20, Table 2, tr.4]; không có ca làm tài xế. Yêu cầu loại này phải tổng hợp. |
| **Kỹ thuật** | Khá | Python, OR-Tools (TSPTW nội tuyến, khoảng 100–190 điểm dừng [P20, Table 2]), một thư viện conformal đơn giản. Không cần huấn luyện mô hình lớn. |
| **Độ phức tạp cài đặt** | Trung bình | Thành phần tốn công nhất: bộ sinh gold edit cộng câu ở 3 mức mơ hồ; bộ chấm tác hại; các probe. CRC chỉ khoảng vài chục dòng code. |
| **Tài nguyên tính toán** | Thấp–trung bình | Máy không có GPU, mọi LLM gọi qua API (spec 10 §2); khoảng 3.000 yêu cầu × (1 + k mẫu) × 2 mô hình dịch. Mỗi lần giải lại TSPTW một tuyến chỉ mất vài giây. |
| **Thời gian** | Sát | Còn khoảng 4 tuần đến hạn 01/12/2026 (xem bảng dưới). |

### 6.1. Rủi ro lớn nhất: H1

LLM có thể gần như không dịch sai khi yêu cầu được nói tường minh. Nếu `μ < α`, CRC cho thực thi gần như tất cả và bài không còn gì để kiểm soát. Các paper đã đọc đều nghiêng về phía này:

- ReOpt-LLM: update correctness **100%** với cả gpt-4.1-mini, gpt-4.1 và gpt-5 trên 30 case OCP; final success 96,7% (lỗi duy nhất ở case OCP5–P1) [P4, Table 8.4].
- MeetMate: code biên dịch đúng trên 95%, precision/recall trên 90% [P8, Table 1].
- OptiChat: độ chính xác trên 80% ở phần lớn loại truy vấn [P7].

### 6.2. Pilot tuần 1 và tiêu chí go/no-go (trước 08/11)

Pilot khoảng 300 yêu cầu × 2 LLM:

- [ ] Dồn mẫu vào mức mơ hồ 2–3 và yêu cầu ghép; mức 1 chỉ dùng làm mốc so sánh.
- [ ] Chạy mô hình mở nhỏ (M1) bên cạnh mô hình mạnh (M2), báo kết quả riêng từng mô hình.
- [ ] Báo `μ` riêng cho từng loại lệnh DSL, không chỉ một con số chung.
- [ ] Đo riêng tỷ lệ lỗi không binding (kế hoạch không đổi dù lệnh sai), vì đây là phần tín hiệu solver phải bắt được.
- [ ] Dùng cận ở Mục 2.3 để tính trước tỷ lệ tự động hóa tối đa có thể đạt với mỗi `α`.
- [ ] Nếu `μ` chênh lệch lớn giữa các loại lệnh: thử hiệu chỉnh CRC theo loại lệnh [P22].

**Go** khi cả hai điều kiện sau đúng:

1. Ở mức mơ hồ 2–3, `μ` của ít nhất một LLM thực tế (ưu tiên mô hình mạnh) ≥ 3–5% và lớn hơn rõ các mức `α` dự kiến báo cáo, để việc kiểm soát không tầm thường.
2. Ít nhất một tín hiệu dựa trên solver có AUROC rõ ràng cao hơn verbalized confidence.

**Nếu không đạt:** chuyển trọng tâm sang LLM nhỏ chạy cục bộ (thực tế khi dữ liệu nhạy cảm) hoặc yêu cầu ghép phức tạp hơn. Nếu vẫn thất bại, chuyển sang hướng dự phòng: *Fit Is Not Enough: Decision Validity of LLM Synthetic Respondents for Last-Mile Delivery Service Design* (đánh giá người trả lời khảo sát giả lập bằng LLM theo chất lượng quyết định thiết kế dịch vụ, không chỉ độ khớp thị phần).

### 6.3. Kế hoạch 4 tuần

| Tuần | Việc | Sản phẩm |
|---|---|---|
| 1 (02–08/11) | Tải LMRC; dựng TSPTW OR-Tools; chốt DSL; pilot 300 yêu cầu theo checklist 6.2 | Báo cáo go/no-go (`μ` theo loại lệnh và mức mơ hồ) |
| 2 (09–15/11) | Sinh benchmark 3.000+ yêu cầu; kiểm duyệt; cài các tín hiệu (ưu tiên tín hiệu solver) | Benchmark v1, nhãn tác hại |
| 3 (16–22/11) | CRC chung và theo loại lệnh; 100 split theo tuyến; thí nghiệm shift theo trạm; ablation tín hiệu | Bảng và hình chính |
| 4 (23–30/11) | Viết paper (≤ 8 trang, double-blind); phát hành code và benchmark | Bản nộp |

### 6.4. Việc còn phải làm trước khi viết claim tính mới

- Đã đọc chọn lọc 04/11/2026: [P3], [P4], [P7], [P8], [P9], [P10], [P14]. Các paper lý thuyết (CRC, LTT, selective classification, ACI, self-consistency) là công cụ chuẩn, không cần đọc lại.
- [ ] Đọc toàn văn ConformalNL2LTL [P24] trước khi trích chi tiết.
- [ ] Đối chiếu bản NeurIPS 2026 camera-ready của [P4]: câu "validator does not perform a separate semantic check" (tr.52 bản v2) và Table 8.4. Đoạn văn tr.35 bản v2 ghi 96,7/93,3/93,3% trong khi Table 8.4 ghi 96,7% cho cả ba model; trích theo bảng.
- [ ] Theo dõi [P2] v2 (có thể bổ sung trích dẫn vào §VIII-B).
- [ ] Tìm thêm trên IEEE Xplore và ACM DL với cụm "LLM" + "dispatch" + "re-optimization".

### 6.5. Câu hỏi mở

Đã trả lời 07/11/2026: **cắt LTT**; paper chỉ kiểm soát rủi ro kết hợp, rủi ro có điều kiện chỉ ghi trong `runs/`.

---

## 7. Tính phù hợp

- **Với logistics và last-mile:** sửa kế hoạch trong ngày là thao tác hằng ngày của điều phối viên. Một lệnh sai được tự động thực thi gây hậu quả trực tiếp và đo được: giao sai khung giờ, giao sai thứ tự ưu tiên (bệnh viện, nhà thuốc), tăng km và phút trễ. Đề tài dùng tuyến thực của Amazon thay vì instance tổng hợp, đúng với lời kêu gọi đánh giá trên dữ liệu vận hành của survey [P2, §VIII-C].
- **Với IEEE MOST (mobility, operations, services, technology):** đề tài nằm ở giao điểm của logistics, last-mile delivery, ứng dụng LLM, định lượng bất định, decision intelligence và tối ưu vận hành.
- **Với vai trò của AI:** LLM làm phần mà ML truyền thống không làm được (hiểu yêu cầu tự do). UQ được dùng để **quyết định có tin LLM hay không**, không thay thế mô hình.
- **Về hướng đi (ghi chú nội bộ, không đưa vào paper):** nhóm chuyển từ hướng online conformal cho dự báo ETA (đã bão hòa) sang một đối tượng rủi ro mới là lỗi dịch của LLM; kiến thức CRC/ACI được dùng lại làm công cụ.

---

## 8. Từ khóa

- **Chính:** LLM-assisted dispatching; natural-language route editing; last-mile delivery; route re-optimization; conformal risk control; selective execution / abstention; human-in-the-loop optimization.
- **Phương pháp:** solver-grounded verification; constraint probing; non-binding constraint errors; stratified conformal risk control; risk-controlled agents; Learn-then-Test; selective classification; risk–coverage; self-consistency; verbalized confidence; distribution shift; exchangeability.
- **Miền và dữ liệu:** TSPTW; vehicle routing with time windows; Amazon Last Mile Routing Research Challenge; dispatcher; plan stability.
- **Gợi ý chuỗi tìm kiếm:** `("large language model" OR LLM) AND (dispatch* OR "route re-optimization" OR "re-planning") AND (verification OR "risk control" OR abstention)`; `"conformal risk control" AND (optimization OR planning OR agent) AND LLM`; `"natural language" AND "vehicle routing" AND (constraint OR edit)`.

---

## 9. Tổng quan tài liệu (24 paper)

### 9.1. Cách xác minh

- P1–P20 đã được tải PDF (lưu trong `../reference-documents/`) và đọc trực tiếp ngày 01/11/2026; ngày 04/11/2026 đọc lại chọn lọc P3, P4, P7, P8, P9, P10, P14 và bổ sung P21–P24 qua tra cứu web (P24 mới đọc tóm tắt, chưa đọc toàn văn). Tiêu đề, tác giả và phiên bản được đối chiếu qua arXiv API. Số trang là **số trang của file PDF tại link đã ghi** (phiên bản ghi trong ngoặc), không phải số trang in của tạp chí.
- **Không PDF nào có đánh số dòng** (các bản arXiv và proceedings đều không bật line numbers). Vì vậy vị trí được ghi theo trang, mục, đoạn, phương trình hoặc bảng, kèm một cụm trích nguyên văn để tìm nhanh bằng Ctrl+F.
- Venue chỉ ghi khi đã xác minh. Các bài ghi "preprint" là chưa qua phản biện (hoặc chưa xác minh được venue), nên trích dẫn thận trọng.

### 9.2. Bảng tài liệu

| # | Nguồn paper (link tải) | Title | Nội dung tổng quan | Vấn đề cần tìm hiểu (vị trí đọc) |
|---|---|---|---|---|
| P1 | [arXiv PDF 2307.03875 (v2)](https://arxiv.org/pdf/2307.03875) — Li, Mellou, Zhang, Pathuri, Menache, 2023 (preprint) | Large Language Models for Supply Chain Optimization | OptiGuide: LLM trả lời câu hỏi what-if trong chuỗi cung ứng bằng cách sinh code sửa mô hình Gurobi (`m.addConstr`) rồi giải lại. Safeguard kiểm tra code và tự debug. Đạt khoảng 93% với GPT-4. | **tr.17, §6.1**, đoạn "Users need to be specific" (ví dụ "earlier" mơ hồ dẫn tới code sai) và đoạn "Undetected mistakes" (*"runs smoothly, but it may be totally wrong"*): bằng chứng gốc cho lỗi ngữ nghĩa im lặng. **tr.17, §6.2**, câu cuối: tối ưu tương tác *"will require designing more comprehensive safeguards"*: động lực. **tr.8**, đoạn cuối (safeguard chỉ là *"quality control checkpoint"* kiểm tra code và tự debug): cơ sở cho baseline "chỉ kiểm tra thực thi/khả thi". |
| P2 | [arXiv PDF 2607.00604 (v1)](https://arxiv.org/pdf/2607.00604) — Xiu, Shen, Zhu, Liu, 2026 (preprint, ghi "working in process"; kiểm tra 04/11/2026 vẫn là v1, nên theo dõi v2) | Vehicle Routing Problem Meets Large Language Models: An Overview and Perspectives | Survey phân loại vai trò của LLM trong VRP: modeler, designer, coordinator. Tổng hợp benchmark và hướng mở. | **tr.13, cột phải, §VIII-A**: *"final route cost alone cannot show whether an LLM has understood the constraints"*: biện minh cho nhãn tác hại mức kế hoạch. **tr.13 (cuối cột phải) → tr.14 (đoạn đầu cột trái), §VIII-B "Human-in-the-Loop Dispatching"**: *"Plans may be revised repeatedly during execution"*; LLM như *"an interaction layer between dispatchers and optimization solvers"*. Đoạn này **không trích công trình nào**, là bằng chứng gap mạnh nhất. **tr.14, cột trái, §VIII-C**: cần ghi *"constraint violations, repair traces, and failure reasons"*. **tr.9, bảng dataset, dòng "Amazon Last-Mile"**: xác nhận 9.184 route (6.112/3.072). |
| P3 | [arXiv PDF 2606.04816 (v2)](https://arxiv.org/pdf/2606.04816) — Luo, He, Geng, Shi, Mei, 2026, Findings of EMNLP 2026 (v2 tháng 10/2026; chưa thấy code hay VRPBench công khai) | Beyond Objective Equivalence: Constraint Injection for LLM-Based Optimization Modeling on Vehicle Routing Problems | Chỉ ra trùng giá trị mục tiêu không bảo đảm đúng ràng buộc. Tiêm nghiệm khả thi và nghiệm vi phạm đúng một ràng buộc để phát hiện *spurious over-constraint* và *silent constraint omission*. VRPCoder-RL đạt 93% Pass@1 trên VRPBench. | **tr.2, cột trái, §1, đoạn 2**: *"objective equivalence does not guarantee constraint fidelity… non-binding on the tested instance"*: cơ sở lý thuyết cho tín hiệu probe binding. **tr.5, "Stage 3: Dual-Verified Rejection Sampling", Eq. (9)**: kiểm chứng so với ground-truth `C_con`, tức **cần gold**, không dùng được lúc triển khai. Đây là lý do đề tài phải thiết kế probe không cần gold. **tr.9, Table 2 / §5.3 Ablation**: Pass@1 giảm 93,00 → 89,00 khi bỏ injection. **tr.9–10, Limitations**: chỉ cô lập từng họ ràng buộc nên có thể bỏ sót lỗi do tương tác nhiều ràng buộc, liên quan đến yêu cầu ghép (mức mơ hồ 3). |
| P4 | [arXiv PDF 2605.18692 (v2)](https://arxiv.org/pdf/2605.18692); [NeurIPS 2026](https://neurips.cc/virtual/2026/171811) — Ye, Deza, Mohan, Er Raqabi, Van Hentenryck, NeurIPS 2026 (trích theo bản NeurIPS) | Democratizing Large-Scale Re-Optimization with LLM-Guided Model Patches | ReOpt-LLM: LLM dịch prompt thành patch có cấu trúc cho mô hình đã triển khai, chọn kỹ thuật tái tối ưu (warm-start…), validator giải lại và giữ nghiệm gần kế hoạch cũ. Hai case: OCP (chuỗi cung ứng) và xếp lịch thi Cornell. Abstract bản NeurIPS mô tả LLM chọn kỹ thuật từ một danh sách chiến lược cho trước, còn solver chịu trách nhiệm về khả thi và chất lượng nghiệm. **Va chạm gần nhất về phía tái tối ưu.** | **tr.1, Abstract**: phạm vi trùng một phần, nên phải trích và định vị. **tr.29, §7.2**: 5 instance × 6 lớp prompt cho mỗi biến thể, quy mô nhỏ. **tr.30, Table 7.1**: định nghĩa *update correctness* và *prompt satisfaction*, để so với loss tác hại của đề tài. **tr.35, Table 8.4**: *update correctness* 100% với cả gpt-4.1-mini, gpt-4.1 và gpt-5 trên 30 case OCP; final success 96,7% cho cả ba, lỗi duy nhất ở case OCP5–P1. Đoạn văn cùng trang ghi 96,7/93,3/93,3%, nên trích theo bảng. Đây là cảnh báo chính cho rủi ro tỷ lệ lỗi thấp (go/no-go). **tr.49**: trường `confidence` chỉ là khóa tùy chọn trong JSON chọn chiến lược. **tr.52, Appendix A.2**: *"The validator does not perform a separate semantic check on the LLM's intent"*, bằng chứng trực tiếp cho gap. *Số trang theo arXiv v2; cần đối chiếu lại với bản NeurIPS camera-ready.* |
| P5 | [ICLR 2025 PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/73d6c3e4b214deebbbf8256e26d2cf45-Paper-Conference.pdf) — Jiang, Wu, Zhang, Zhang, ICLR 2025 | DRoC: Elevating Large Language Models for Complex Vehicle Routing via Decomposed Retrieval of Constraints | Phân rã ràng buộc VRP, truy xuất tài liệu cho từng ràng buộc, kết hợp với tri thức nội tại của LLM để sinh chương trình OR-Tools/Gurobi. Đánh giá trên 48 biến thể VRP. | **tr.7, §5**: định nghĩa Accuracy Rate (*"successful programs that result in the optimal solution"*); **Table 1** (gpt-4o: 20,83% → 45,83%). **tr.17, Appendix B, đoạn cuối**: *"A program is deemed correct when its generated solve function yields the same value as the optimal solution"*, tức chấm theo trùng giá trị mục tiêu. Đối chiếu với [P3] để lập luận rằng tiêu chí này bỏ lọt lỗi không binding, và vì vậy đề tài dùng nhãn tác hại mức kế hoạch. Cũng là tiền lệ dùng OR-Tools. |
| P6 | [arXiv PDF 2502.15359 (v3)](https://arxiv.org/pdf/2502.15359) — Li, Liu, Wang, Tong, Han, Yuan, Zhang, 2025 (preprint, venue chưa xác minh) | ARS: Automatic Routing Solver with Large Language Models | LLM sinh heuristic có nhận biết ràng buộc từ mô tả ngôn ngữ, dựa trên cơ sở dữ liệu ràng buộc mẫu. Giới thiệu RoutBench gồm 1.000 biến thể VRP từ 24 thuộc tính. | **tr.3, §3.1**: mỗi ràng buộc gồm mô tả `I_k` và *"constraint feasibility checking program"* `C_k`: mẫu thiết kế bộ kiểm tra cho từng loại lệnh DSL. **tr.6, §4**: *"validation code, used to confirm whether a solution adheres to user requirements"*. **tr.8, §5.1 (đoạn ngay dưới Table 3)**: Success Rate là tỷ lệ nghiệm qua validation, tức chỉ kiểm tra khả thi so với mô tả đã đúng, không xét trường hợp LLM hiểu sai ý. |
| P7 | [arXiv PDF 2501.08406 (v2)](https://arxiv.org/pdf/2501.08406); bản tạp chí: [DOI 10.1287/ijds.2025.0074](https://doi.org/10.1287/ijds.2025.0074) — Chen, Constante-Flores, Mantri, Kompalli, Ahluwalia, Li, INFORMS J. Data Science 2025 | OptiChat: Bridging Optimization Models and Practitioners with Large Language Models | Hệ đối thoại giúp người dùng hiểu mô hình tối ưu: giải thích, chẩn đoán không khả thi, phân tích độ nhạy, đánh giá chỉnh sửa, trả lời why-not bằng counterfactual. Dùng function call cộng sinh code. | **tr.9, §3.1, đoạn counterfactual**: thêm ràng buộc `x1 = 1` rồi giải lại để so sánh, kỹ thuật gần với probe của đề tài. **tr.14, §4.2.2**: why-not chỉ đạt 78,4% (o3), 62,2% (GPT-4.1), 54,1% (GPT-4o), là bằng chứng về tỷ lệ lỗi khi LLM sinh ràng buộc. **tr.15, §4.2.3 "Failure Analysis"**: *logic errors*, tức tên hoặc chỉ số hợp lệ, *"not a syntax error, but fail to accurately capture the user's intent"*, đúng loại lỗi im lặng; chiếm 65,0% lỗi của o3. Mô hình càng mạnh thì lỗi còn lại càng là lỗi ngữ nghĩa. **Lưu ý khi trích:** 65% là tỷ lệ *trong số các lỗi*; độ chính xác tổng thể vẫn trên 80% ở phần lớn loại truy vấn, nên không dùng con số này để gợi ý LLM hay sai. *Số trang theo bản arXiv v2, có thể khác bản tạp chí.* |
| P8 | [arXiv PDF 2312.06908 (v3)](https://arxiv.org/pdf/2312.06908) — Lawless et al., ACM Trans. Interact. Intell. Syst. 14(3), Art. 22, 2024 | "I Want It That Way": Enabling Interactive Decision Support Using Large Language Models and Constraint Programming | MeetMate: LLM cộng Constraint Programming cho xếp lịch họp tương tác. LLM dịch sở thích thành hàm ràng buộc Python; có Information Checker làm safeguard. | **tr.11, §4, đoạn "Information Checker"**: safeguard chỉ kiểm tra hệ thống *"has sufficient information"*, không kiểm tra dịch đúng ý. **tr.18, §5.3**: precision/recall của code ràng buộc (> 90%); tác giả phải đánh giá trên hai tập thời gian vì lỗi *"may not appear over a small time horizon"*. Đây là cùng hiện tượng ràng buộc không binding, và là tiền lệ cho tín hiệu probe binding. **Table 1**: code biên dịch đúng > 95%. **User study, Table 2**: 14 lỗi, phần lớn ở Coder, trong đó có lỗi *đảo dấu bất đẳng thức* (*"meeting needs to start after 11am"*), trùng với ví dụ "sau 15h → trước 15h" của đề tài; lỗi hiểu khác "buổi chiều bắt đầu lúc nào" là bằng chứng cho mức mơ hồ 2. Nên trích ở Mục 1.2 và 4.4. **tr.15, §4.4 System Limitations**. |
| P9 | [arXiv PDF 2604.02666 (v1)](https://arxiv.org/pdf/2604.02666) — Drossman, Jacquillat, Martin, 2026 (preprint) | Let's Have a Conversation: Designing and Evaluating LLM Agents for Interactive Optimization | Đánh giá optimization agent qua hội thoại với *decision agents* mô phỏng stakeholder có hàm utility ẩn. Case xếp giờ học SFUSD, hàng nghìn hội thoại. Agent có công cụ cấu trúc tốt hơn chatbot đa dụng. | **tr.1, Abstract**: dùng agent có utility ẩn để sinh hội thoại có ground truth, để tham khảo cách làm benchmark tái lập và quy mô lớn. **tr.6, đoạn "Our second contribution…"**: chatbot đa dụng mắc *"silent modeling errors through free-form code"*, ủng hộ DSL thay code tự do. **tr.25–26**: tác giả nói code-based agent có thể khiến hệ thống *"fails silently"* và chưa rõ safeguard có chặn được hết không, là bằng chứng gap. Hội thoại cho kết quả tốt hơn hẳn one-shot, ủng hộ giá trị của việc hỏi lại người. Bộ mô phỏng stakeholder có utility ẩn có thể dùng để mô phỏng điều phối viên trả lời câu hỏi xác nhận (mở rộng). Bài **không** có cơ chế từ chối có bảo đảm. |
| P10 | [arXiv PDF 2609.19654 (v1)](https://arxiv.org/pdf/2609.19654) — Yuan et al., 2026 (preprint) | Replan, Repair, or Edit? A Unified Empirical Evaluation of Travel Agents for Itinerary Revision under Resource Disruptions | So sánh replan đầy đủ (LLM–Z3), plan repair phân cấp và LLM local revision khi sửa lịch trình du lịch bị gián đoạn. Đo hiệu quả, độ ổn định kế hoạch và chi phí. | **tr.4, §2.3 "Plan Stability"**: logical edit `d(P, P′)` đếm thay đổi ngữ nghĩa, *Preservation* là tỷ lệ slot giữ nguyên. Dùng được ngay cho tín hiệu "độ thay đổi kế hoạch so với phạm vi yêu cầu" (vừa là tín hiệu rủi ro, vừa là chỉ số độ lệch). **tr.3, danh sách đóng góp, mục 3**: có *"correct refusal"*, nhưng là từ chối khi bài toán không khả thi, khác với từ chối vì nghi LLM hiểu sai. Gián đoạn ở đây đến từ môi trường, không từ yêu cầu ngôn ngữ của người. |
| P11 | [arXiv PDF 2208.02814 (v4)](https://arxiv.org/pdf/2208.02814) — Angelopoulos, Bates, Fisch, Lei, Schuster, ICLR 2024 | Conformal Risk Control | Mở rộng conformal prediction để kiểm soát kỳ vọng của một loss đơn điệu bất kỳ. | **tr.2, §1**: loss phải *non-increasing* theo `λ` và bị chặn bởi `B`. **tr.3, §2.1, Theorem 1**: `E[L_{n+1}(λ̂)] ≤ α` khi loss đơn điệu, liên tục phải và hoán đổi được, dùng cho rủi ro kết hợp `E[1{thực thi} · h]`. **tr.5, Proposition 1**: với loss không đơn điệu, rủi ro có thể tiến gần `B`, nên **không** dùng CRC cho `P(h \| thực thi)`. |
| P12 | [arXiv PDF 2110.01052 (v5)](https://arxiv.org/pdf/2110.01052) — Angelopoulos, Bates, Candès, Jordan, Lei (arXiv; venue chưa xác minh trong đợt này) | Learn then Test: Calibrating Predictive Algorithms to Achieve Risk Control | Biến việc chọn tham số thành kiểm định đa giả thuyết có kiểm soát FWER. Kiểm soát được cả rủi ro không đơn điệu với bảo đảm `(α, δ)`. | **tr.3, §2.1** (các bước LTT) **và Theorem 1**: bảo đảm qua thủ tục kiểm soát FWER. **tr.5, §2.3.1, Algorithm 1 (fixed sequence testing)**: phù hợp với chuỗi ngưỡng có thứ tự tự nhiên. **tr.8, §3.2 "Selective Classification with Accuracy Control"**: rủi ro là *"the error conditionally on predicting"*, dùng cận binomial chính xác. Đây là **khuôn mẫu trực tiếp** cho `P(h = 1 \| s ≤ λ) ≤ α`. |
| P13 | [arXiv PDF 2307.01928 (v2)](https://arxiv.org/pdf/2307.01928) — Ren et al., CoRL 2023 | Robots That Ask For Help: Uncertainty Alignment for Large Language Model Planners | KnowNo: LLM planner sinh các phương án dạng trắc nghiệm, conformal prediction tạo tập dự đoán; nếu tập có nhiều hơn một phần tử thì robot hỏi người. | **tr.3, §2, các bước 1–3**: *"If the prediction set is a non-singleton, the robot leverages help from a human"*. Đây là "conformal ask-for-help" đã có, nên phải trích để không claim trùng. **tr.4, §3.1**: bảo đảm là *"marginal guarantee"*. **tr.9, §6, đoạn "Limitations and future work"**: giả định hành động LLM đề xuất *"can be executed successfully"*. Khác với đề tài: lệnh thực thi thành công vẫn có thể gây hại vận hành. |
| P14 | [arXiv PDF 2405.01563 (v1)](https://arxiv.org/pdf/2405.01563) — Abbasi Yadkori et al., 2024 (preprint) | Mitigating LLM Hallucinations via Conformal Abstention | Dùng LLM tự đánh giá độ tương đồng giữa các câu trả lời lấy mẫu làm điểm tin cậy, rồi dùng conformal/risk control để chọn ngưỡng từ chối sao cho tỷ lệ hallucination bị chặn. | **tr.3, Eq. (1)–(2)**: loss `(1 − a_λ)(1 − m)` ("không từ chối và sai"), tối thiểu tỷ lệ từ chối sao cho `R(λ) ≤ α`. **Về hình thức gần như trùng rủi ro kết hợp của đề tài** (CORA [P21] làm điểm trùng này nặng hơn), nên không được claim mới ở công thức rủi ro; khác biệt phải nằm ở loss tác hại và tín hiệu solver. **tr.3, §2.1**: điểm tính từ k mẫu, là baseline "chỉ self-consistency". **tr.3**: giả định exchangeable, đối chiếu với RQ3. |
| P15 | [arXiv PDF 2402.10978 (v1)](https://arxiv.org/pdf/2402.10978) — Mohri, Hashimoto, ICML 2024 | Language Models with Conformal Factuality Guarantees | Chứng minh conformal prediction cho LM tương đương thuật toán back-off: tách đầu ra thành sub-claim, chấm điểm, loại dần sub-claim kém chắc chắn để đạt bảo đảm đúng. | **tr.5, định nghĩa "α-conformally factual"**: cách phát biểu bảo đảm cho đầu ra có cấu trúc. **tr.13, Limitations**: *"the coverage guarantee is not conditional"*, minh họa giới hạn marginal mà đề tài phải nêu. Tham khảo khi phân tích yêu cầu ghép (lệnh gồm nhiều thành phần). |
| P16 | [arXiv PDF 1705.08500 (v2)](https://arxiv.org/pdf/1705.08500) — Geifman, El-Yaniv, NeurIPS 2017 | Selective Classification for Deep Neural Networks | Định nghĩa selective risk, coverage, đường risk–coverage; đề xuất SGR để chọn ngưỡng có cận rủi ro có điều kiện với xác suất `1 − δ`. | **tr.3, §2**: định nghĩa coverage, selective risk và *"risk-coverage curve"*, dùng cho chỉ số coverage, đường risk–coverage và AURC. **tr.4, §3, Algorithm 1 (SGR)** và **tr.5, Theorem 3.2**: cận rủi ro có điều kiện dưới giả định i.i.d., là baseline hoặc phương án thay thế LTT cho `P(h \| thực thi)`. |
| P17 | [arXiv PDF 2106.00170 (v3)](https://arxiv.org/pdf/2106.00170) — Gibbs, Candès, NeurIPS 2021 | Adaptive Conformal Inference Under Distribution Shift | ACI: cập nhật online mức `α_t` theo lỗi quan sát được, giữ tần suất lỗi dài hạn đúng `α` mà không cần exchangeability. | **tr.3, §2, Eq. (2)**: `α_{t+1} = α_t + γ(α − err_t)`. **tr.6, §4, Proposition 4.1**: `lim (1/T) Σ err_t = α`. Cơ sở cho phần mở rộng online và phân tích khi exchangeability bị phá. Lưu ý ACI cần phản hồi ở mọi bước; khi người chỉ kiểm tra ngẫu nhiên thì cần biến thể cho phản hồi gián đoạn (chỉ liên quan phần mở rộng). |
| P18 | [arXiv PDF 2203.11171 (v4)](https://arxiv.org/pdf/2203.11171) — Wang et al., ICLR 2023 | Self-Consistency Improves Chain of Thought Reasoning in Language Models | Lấy mẫu nhiều chuỗi suy luận rồi bỏ phiếu đa số cho đáp án cuối, cải thiện độ chính xác suy luận. | **tr.3, §2** (bỏ phiếu đa số; Table 1, dòng *"Unweighted sum (majority vote)"*). **tr.8, §3.5, đoạn "Self-Consistency Improves Robustness to Imperfect Prompts" và Figure 5**: tỷ lệ mẫu đồng thuận *"is highly correlated with accuracy"*, có thể dùng làm *"uncertainty estimate"*. Cơ sở cho tín hiệu đồng thuận; với DSL cần so khớp lệnh theo ngữ nghĩa (JSON chuẩn hóa) thay vì so chuỗi. |
| P19 | [arXiv PDF 2306.13063 (v2)](https://arxiv.org/pdf/2306.13063) — Xiong et al., ICLR 2024 | Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs | Đánh giá có hệ thống các cách khai thác độ tự tin black-box: verbalized confidence, lấy mẫu, đo đồng thuận. | **tr.1, Abstract** và **tr.2, §1, đoạn tóm tắt quan sát**: LLM tự khai độ tự tin bị *overconfident*, giá trị tập trung ở 80–100%; AUROC phát hiện lỗi chỉ khoảng 0,522 → 0,605 (so white-box). Cơ sở cho baseline verbalized confidence và log-prob, và cho giả thuyết H2 rằng tín hiệu solver tốt hơn. |
| P20 | [PDF (Amazon Science)](https://cdn.amazon.science/1f/02/349d1f594f8d8f97b21ebc02c7b2/2021-amazon-last-mile-routing-research-challenge-data-set.pdf); [DOI 10.1287/trsc.2022.1173](https://doi.org/10.1287/trsc.2022.1173) — Merchán, Arora, Pachon, Konduri, Winkenbach, Parks, Noszek, Transportation Science, 2022 | 2021 Amazon Last Mile Routing Research Challenge: Data Set | Mô tả bộ dữ liệu 9.184 tuyến giao hàng thực của tài xế Amazon, với đặc trưng ở mức tuyến, điểm dừng và gói hàng. Dữ liệu ẩn danh, công khai trên AWS Open Data. | **tr.3, §2 và Table 1**: các trường dữ liệu (observed sequence, zone ID, time window, planned service time, transit times); 6.112 route huấn luyện cộng *"an additional 3,072"* route đánh giá. **tr.4, Table 2**: trung bình 148 điểm dừng, 238,5 gói, chỉ 18,6 gói có khung giờ (P10 = 2), tức khung giờ thưa, phải tổng hợp yêu cầu `set_time_window`. **tr.4, mục "Transit times"**: thời gian trung bình giữa từng cặp điểm dừng trong tuyến, chỉ có nội tuyến, nên MVP giới hạn ở một tuyến. *Số trang theo file PDF 5 trang (trang 1 là trang bìa INFORMS).* |
| P21 | [arXiv PDF 2604.09155](https://arxiv.org/pdf/2604.09155) — Feng et al., HKU, 2026 (preprint) | CORA: Conformal Risk-Controlled Agents for Safeguarded Mobile GUI Automation | Agent GUI di động. Guardian (VLM fine-tune) chấm rủi ro từng hành động; CRC chọn ngưỡng execute/abstain theo ngân sách `α`; hành động bị chặn chuyển cho Diagnostician (confirm/reflect/abort). **Va chạm gần nhất về khung kiểm soát rủi ro.** | **Eq. (3)**: loss "thực thi ∧ gây hại", cùng dạng rủi ro kết hợp của đề tài. Báo cáo cả HR (rủi ro kết hợp) lẫn mHR (rủi ro có điều kiện); dùng weighted CRC cho covariate shift; tách split theo khối vì phụ thuộc tuần tự. Khác đề tài: miền GUI, không phải tối ưu; guardian là mô hình học, cần nhãn để train; nhãn gây hại gán theo bước, không ở mức kế hoạch; không có tín hiệu từ solver. Trích trong Related Work và Mục 5. |
| P22 | [arXiv HTML 2607.24343 (v1)](https://arxiv.org/html/2607.24343v1) — Rahman et al., 2026 (preprint) | Beyond Aggregate Risk: Role-Stratified Conformal Risk Control for LLM Tool Calls | CRC riêng cho từng vai trò ngữ nghĩa của đối số trong tool call (target, credential, content…). | Chứng minh: muốn bảo đảm cho một vai trò có tần suất `p_r` bằng kiểm soát tổng hợp thì ngân sách phải co còn `α · p_r`; có báo cáo compliance thực nghiệm dưới frozen shift. Lệnh DSL của đề tài cũng là tool call có cấu trúc, nên là cơ sở cho hiệu chỉnh theo loại lệnh. Khác đề tài: rủi ro là prompt injection, không phải dịch sai ý; không có solver. |
| P23 | [arXiv PDF 2606.29054](https://arxiv.org/pdf/2606.29054) — 2026 (preprint) | When Can Conformal Risk Control Certify LLM Outputs? | Điều kiện để CRC có ích cho đầu ra LLM. | Khi tỷ lệ lỗi gốc `μ > α`, mọi phương pháp hợp lệ phải từ chối ít nhất `(μ − α)/(1 − α)` mẫu. Dùng làm công cụ tính tỷ lệ tự động hóa tối đa và tiêu chí go/no-go (Mục 2.3, 6.2). |
| P24 | arXiv 2504.21022, 2025 (preprint) | ConformalNL2LTL | Conformal cho việc dịch ngôn ngữ tự nhiên sang logic thời gian (LTL) cho robot, hỏi người khi không chắc. | Cùng ý tưởng "dịch NL → đặc tả hình thức + conformal + hỏi người"; khác ở chỗ là đặc tả LTL cho robot, không phải chỉnh sửa kế hoạch tối ưu. **Mới đọc tóm tắt, cần đọc toàn văn trước khi trích chi tiết.** |

### 9.3. Phân tích phê phán

**(a) Vấn đề đã được giải quyết.** Cơ chế dịch ngôn ngữ thành chỉnh sửa mô hình đã có và chạy tốt trên tập nhỏ: OptiGuide khoảng 93% [P1], ReOpt-LLM update correctness 100% và final success 96,7% [P4], MeetMate precision/recall > 90% [P8]. Phía thống kê, các bảo đảm phân phối tự do cho việc từ chối hoặc hỏi người đã hoàn chỉnh về lý thuyết [P11]–[P14], [P16], và đã được áp cho việc chặn hành động gây hại của agent [P21], [P22].

**(b) Các phương pháp đã đề xuất.** Có ba cách kiểm chứng:
1. **Kiểm tra thực thi hoặc khả thi:** [P1], [P4], [P6].
2. **So với đáp án chuẩn:** trùng giá trị mục tiêu [P5], hoặc tiêm nghiệm so với ground-truth [P3].
3. **Bất định từ chính LLM:** đồng thuận [P14], [P18], độ tự tin tự khai [P19].
4. **Mô hình chấm rủi ro theo hành động:** guardian học có giám sát [P21].

Cách 1 không bắt được lỗi ngữ nghĩa. Cách 2 cần gold nên không dùng được lúc triển khai. Cách 3 và 4 không dùng thông tin từ solver, nên khó bắt lỗi chỉ lộ ra ở mức kế hoạch.

**(c) Hạn chế còn lại liên quan trực tiếp đến đề tài.**
- Lỗi "đúng cú pháp, sai ý" được chính các tác giả thừa nhận nhưng chưa có cơ chế xử lý [P1, tr.17]; [P4, tr.52]; [P7, tr.15]; [P8, Table 2]; [P9, tr.25–26].
- Lỗi do ràng buộc không binding qua mặt các kiểm tra theo giá trị mục tiêu [P3, tr.2]; [P5, tr.17]; [P8, tr.18].
- Chưa có công trình nào cho lớp tương tác điều phối viên ↔ solver trong định tuyến [P2, tr.13–14].
- Các bảo đảm conformal hiện có là marginal và giả định exchangeable [P13], [P15], [P17]; một ngân sách `α` chung có thể che giấu vi phạm ở nhóm hiếm [P22].

**(d) Đề tài khác ở đâu.** Đề tài ghép hai nửa còn rời nhau: **tín hiệu từ solver** (ý tưởng probe của [P3], [P7], [P8], nhưng bỏ phụ thuộc vào gold) và **bảo đảm thống kê** (CRC/LTT [P11], [P12], dùng như công cụ). Ghép như vậy trên một **đối tượng rủi ro mới**: lệnh sửa kế hoạch tuyến đang chạy được thực thi nhưng gây hại vận hành, với tác hại chỉ nhìn thấy ở mức kế hoạch. Chi tiết ở Mục 5.3.

**(e) Đóng góp thực sự và bằng chứng.** Đóng góp nằm ở **mức bài toán** và ở **thiết kế điểm rủi ro đặc thù miền từ phản hồi solver**; phần CRC chỉ là công cụ đánh giá. Bằng chứng cho tính mới hiện mới là bằng chứng về **gap** (các trích dẫn tường minh ở trên). Bằng chứng về **giá trị** của đóng góp (H1–H3) chỉ có sau thực nghiệm. Điểm cần cảnh giác nhất: CORA [P21] đã làm khung CRC chặn hành động "thực thi ∧ gây hại", kèm HR/mHR và weighted CRC; dạng rủi ro kết hợp gần như trùng [P14, Eq. (1)]; cơ chế hỏi người trùng [P13]. Vì vậy phần mới phải được chứng minh bằng ablation tín hiệu solver và bằng định nghĩa tác hại mức kế hoạch.

---

## 10. Bản nháp related work (tiếng Anh)

Dùng cho mục Related Work của paper. Mã [P#] cần thay theo file `.bib`.

> **Risk-controlled execution of LLM actions.** Conformal risk control (CRC) [P11] and Learn-then-Test [P12] provide distribution-free bounds on expected loss and have been used to let LLM systems abstain or ask for help: KnowNo asks a human when the conformal prediction set over candidate plans is not a singleton [P13], and conformal abstention bounds the rate of answers that are both emitted and wrong [P14]. Closest to our setting, CORA calibrates an execute/abstain threshold on a learned, action-conditional risk score so that the rate of executed harmful GUI actions stays below a user-set budget, and adds weighted calibration for covariate shift [P21]. Role-stratified CRC further shows that a single action-level budget can hide violations concentrated in rare argument roles of structured tool calls [P22]. These works control risk over actions whose harm is judged directly from the action and its context. In route re-planning, by contrast, a semantically wrong edit can be syntactically valid, solver-feasible, and even leave the plan unchanged when the mistranslated constraint is non-binding; its harm is visible only at the level of the resulting plan. We therefore define harm on the re-optimized plan and build risk scores from solver feedback that require no gold edit at deployment, and we use CRC/LTT as calibration tools rather than as a contribution.

> **LLM-guided re-optimization.** ReOpt-LLM translates user prompts into typed patches of a deployed MIP and re-solves with warm starts [P4]; its validator checks feasibility but explicitly performs no separate semantic check of intent. Constraint injection exposes over-constraints and omissions that survive objective-equivalence checks, but its verifier needs the ground-truth model [P3]. MeetMate reports LLM-coded scheduling constraints with inverted inequalities that only surface over a longer horizon [P8]. Our probes build on these observations without access to gold.
