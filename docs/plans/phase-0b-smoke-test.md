# Phase 0b — Kiểm tra nhanh: LLM có dịch sai đủ nhiều không? (06–07/11)

> Xem `00-README.md` cho Global Constraints. Làm **ngay sau Task 0.3** (khi đã gọi được M1, M2). Không phụ thuộc Phase 1.
> Người phụ trách: **A**. Thời gian: ~2–3 giờ. Chi phí API: dưới 1 USD.

**Goal:** Trong một buổi, biết sơ bộ M1 và M2 có dịch sai yêu cầu sửa tuyến đủ thường xuyên không, **trước khi** đầu tư vào solver, benchmark và tín hiệu.

**Spec:** `docs/03-experiments/13-experiment-protocol.md` §3 (pilot E0), `docs/02-specs/06-edit-dsl.md`, `docs/02-specs/10-llm-translation.md` §3

## Vấn đề cần giải quyết

Rủi ro lớn nhất của đề tài: **LLM gần như không dịch sai**. Khi đó lớp kiểm soát rủi ro không có việc gì làm và paper không viết được. Pilot E0 (10/11) sẽ trả lời chắc chắn, nhưng tới lúc đó đã tốn 4–5 ngày làm solver và benchmark.

Kiểm tra nhanh này **không cần solver, không cần benchmark, không cần đo tín hiệu**. Chỉ cần: viết tay khoảng 50 câu có đáp án, gọi 2 mô hình dịch, rồi đọc bằng mắt. Nó cho biết sớm 3–4 ngày rằng nên đi tiếp hay báo động.

Đây **không** phải kết quả cho paper: số câu ít, do A tự viết, và chấm bằng mắt. Nó chỉ là tín hiệu sớm.

---

### Step 1 [HUMAN] [A] — Soạn 2 tuyến mẫu (~20 phút)

**Files:** Create `data/smoke/routes.md` (thư mục `data/` không commit)

- [ ] **Tuyến R1:** tuyến 8 điểm trong `docs/MoTaCuTheThucNghiem.md` §3 (Minh Chau Pharmacy … Sunrise Gym, lúc 13:00, ca kết thúc 17:30).
- [ ] **Tuyến R2:** tự soạn ~15 điểm, có các trường hợp dễ nhầm:
  - 2 điểm cùng loại (ví dụ 2 nhà thuốc: "Oak Pharmacy", "Elm Pharmacy");
  - 2 tên gần giống nhau ("Oak Clinic" và "Oak Pharmacy");
  - 3–4 khu (A–D);
  - 1–2 điểm đã có khung giờ.
- [ ] Viết mỗi tuyến dưới dạng bảng giống phần LLM sẽ thấy: `#`, tên, loại, khu, giờ dự kiến, khung giờ; thêm dòng `Current time`, `Shift ends`.

### Step 2 [HUMAN] [A] — Viết ~50 câu yêu cầu kèm đáp án (~60 phút)

**Files:** Create `data/smoke/items.jsonl` (mỗi dòng: `id`, `route`, `q`, `gold` dạng JSON theo DSL, `kind`)

Phân bổ:

| Nhóm | Số câu | Ví dụ |
|---|---|---|
| Từ chỉ chiều thời gian dễ nhầm ("until", "not before", "by", "no later than", "after", "from … on") | 12 | "Don't send anyone to the hospital until 3." → `set_time_window(An Binh Hospital, 15:00, null)` |
| Gọi điểm gián tiếp (theo loại, khu, vị trí) | 10 | "The clinic needs its drop before the school." → `precedence(Hoa Sen Clinic, Nguyen Du School)` |
| Tên dễ nhầm (R2) | 6 | "Oak Clinic cancelled." → `remove_stop(Oak Clinic)` (không phải Oak Pharmacy) |
| Giờ tương đối ("in two hours", "half four", "end of lunch") | 6 | "Gym can't take it for another hour and a half." (13:00) → `set_time_window(Sunrise Gym, 14:30, null)` |
| Câu ghép 2–3 yêu cầu | 10 | "Thanh Cong cancelled, and the driver has to be back by 4:45." → `remove_stop(Thanh Cong Shop)` + `driver_end_time(16:45)` |
| Ẩn ý (nêu lý do thay vì nói thẳng) | 6 | "Maple St customer won't be home after 4." → `set_time_window(12 Maple St, null, 16:00)` |

Nguyên tắc khi viết:
- [ ] Viết như điều phối viên bận rộn: ngắn, tự nhiên, có thể viết tắt. **Không** cố tình viết câu sai ngữ pháp hay đánh đố vô lý.
- [ ] Mỗi câu chỉ có **một cách hiểu hợp lý**. Nếu chính A phải phân vân thì sửa câu hoặc bỏ câu đó.
- [ ] Ghi đáp án **trước khi** gọi LLM, và không sửa đáp án sau khi đã xem kết quả.
- [ ] Không đưa 50 câu này vào bất kỳ bộ benchmark nào, và B không đọc chúng (quy tắc "mù template", `00-README.md`).

### Step 3 [CODE] [A] — Script gọi 2 mô hình (~30 phút)

**Files:** Create `scripts/smoke_translate.py`

**Interfaces:**
- Consumes: `configs/llm.yaml` và `.env` (Task 0.3); `data/smoke/routes.md`, `data/smoke/items.jsonl`.
- Produces: `data/smoke/outputs.jsonl` (mỗi dòng: `id`, `model`, `raw`, `parsed_ok`) và `data/smoke/review.md`.

- [ ] Dùng prompt theo spec 10 §3: hướng dẫn + danh sách lệnh DSL + bảng tuyến + câu yêu cầu; yêu cầu trả JSON kèm `confidence`.
- [ ] Gọi **M1 và M2**, mỗi câu 1 lần, `temperature = 0`.
- [ ] Ghi `review.md` thành bảng để đọc bằng mắt: `id` | câu | đáp án | M1 trả về | M2 trả về | hai cột trống `M1 đánh giá`, `M2 đánh giá`.
- [ ] Không cần cache, không cần test tự động: đây là script dùng một lần. Viết gọn, dưới 100 dòng.

### Step 4 [EXP] [A] — Chạy và chấm bằng mắt (~45 phút)

- [ ] Chạy `uv run python scripts/smoke_translate.py`.
- [ ] Với mỗi câu và mỗi mô hình, điền một nhãn:

| Nhãn | Nghĩa | Ví dụ |
|---|---|---|
| ✅ Đúng | Cùng nghĩa với đáp án (cách viết JSON khác nhau cũng được) | `deadline(Gym, 16:30)` so với đáp án `set_time_window(Gym, null, 16:30)` |
| 🟡 Sai nhưng vô hại | Khác đáp án nhưng gần như chắc không ảnh hưởng tuyến | "trước 17:30" thay vì "trước 17:00" khi điểm đang giao 16:35 |
| 🔴 Sai có hại | Kế hoạch sẽ làm sai ý người nói | Đảo chiều giờ, nhầm điểm, bỏ sót một yêu cầu trong câu ghép, thêm ràng buộc không ai yêu cầu |
| ⚪ Hỏng | JSON lỗi, lệnh không tồn tại, tên điểm không có | — |

- [ ] Với mỗi lỗi 🔴, ghi **loại lỗi** (đảo chiều / sai điểm / thiếu một phần / thừa ràng buộc / sai giá trị) và có làm **tuyến không đổi** không (giống ví dụ bệnh viện).
- [ ] Ghi thêm `confidence` LLM tự khai ở các câu 🔴: LLM có tự tin cao khi sai không?

### Step 5 [DECIDE] [A] — Đọc kết quả và quyết định (~15 phút)

Đếm số câu 🔴 trên ~50 câu, **riêng cho từng mô hình**:

| Kết quả | Ý nghĩa | Làm gì |
|---|---|---|
| M1 có **≥ 5 câu 🔴** và có lỗi đảo chiều hoặc sai điểm | ✅ Rủi ro chính có thật | Làm tiếp Phase 1 như kế hoạch |
| M1 có **1–4 câu 🔴** | ⚠️ Lỗi có nhưng ít | Làm tiếp, nhưng ghi chú cho Phase 2: tăng tỷ lệ câu ghép và câu gián tiếp; xem kỹ loại câu nào gây lỗi để đưa vào template |
| **Cả M1 và M2 gần như 0 câu 🔴** | 🛑 Báo động sớm | Dừng lại, báo GVHD ngay. Thử thêm 20 câu khó hơn trong 1 giờ; nếu vẫn 0 thì bàn chuyển sang hướng dự phòng (`MoTaDeTai.md` §6.2) trước khi làm Phase 1 |

Các quan sát khác cần ghi lại (dù kết quả thế nào):
- M2 có sai câu nào không? Nếu M2 gần như không sai, paper sẽ dựa chủ yếu vào M1 (đã có trong kế hoạch).
- Loại lỗi nào nhiều nhất? Điều này gợi ý tín hiệu nào quan trọng (ví dụ nhiều lỗi "tuyến không đổi" thì S1, S3 sẽ có giá trị).
- LLM có tự tin cao khi sai không? Nếu có, lý do cần lớp kiểm soát càng rõ.

### Step 6 — Ghi lại

- [ ] Viết 5–10 dòng tóm tắt vào `docs/CONTENT.md` §6: số câu 🔴 của M1, M2; loại lỗi chính; quyết định.
- [ ] Commit `scripts/smoke_translate.py` (dữ liệu trong `data/smoke/` không commit).
- [ ] Gửi tóm tắt cho GVHD nếu kết quả là ⚠️ hoặc 🛑.

## Kết thúc Phase 0b khi

- [ ] Có bảng `review.md` đã chấm đủ cho M1 và M2.
- [ ] Có quyết định: làm tiếp / làm tiếp có điều chỉnh / báo động.
