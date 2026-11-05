Các ghi chú trong quá trình làm 

> AI Agents không cần đọc file này trong quá trình thực thi 

Link template các hội nghị IEEE: [www.ieee.org/conferences/publishing/templates](https://www.ieee.org/conferences/publishing/templates)

## Smoke test (Phase 0b) và bộ human (E6) khác nhau thế nào

| | Smoke test (Phase 0b) | Bộ human E6 (Phase 3, spec 08 §9) |
|---|---|---|
| Tình huống | A **tự nghĩ** | **Có sẵn trên thẻ**, máy sinh từ mẫu tình huống do A soạn (6–8 mẫu/lệnh) |
| Câu | A tự viết | Người viết (B, C) tự viết cả câu từ đầu, **không điền vào chỗ trống** |
| Đáp án (gold) | A tự viết, trước khi gọi LLM | Máy bốc sẵn và giữ kín, người viết không thấy |
| Tính khả thi | A ước lượng bằng mắt (giờ trong ca, khung không quá hẹp) | Máy kiểm tra bằng solver trước khi tạo thẻ |
| Kiểm tra | `smoke_translate.py prepare` (định dạng) | A đọc câu (không xem thẻ), đánh dấu câu có khớp thẻ không; giữ câu "yes" |

- Thẻ tình huống = bảng tuyến + điểm được đánh dấu + mô tả chuyện xảy ra ngoài đời (có thể tiếng Việt). Không có câu tiếng Anh, không lộ đáp án.
- Lý do không dùng câu khung để điền: câu sẽ mang khuôn của máy, mất thứ cần đo là ngôn ngữ thật của con người.
- Khi tự nghĩ tình huống ở smoke test: viết tự nhiên như người khác sẽ viết, không viết theo kiểu đã biết trước LLM sẽ dịch thế nào.
