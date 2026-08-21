# 02 - Continuous batching under load (u50)

Host `Linux-x86_64` · `--parallel 4` · 30 samples over
60s at 2.0s intervals · raw CSV: `02-server-metrics-u50.csv`

| Gauge | Peak observed |
|:--|--:|
| `n_busy_slots_per_decode` (avg/decode) | 3.94 of 4 slots (98%) |
| `requests_processing` | 4 |
| `requests_deferred` | 46 |
| `kv_cache_usage_ratio` | n/a — not exported by llama.cpp `b10488` |
| `tokens_predicted_total` (final) | 18432 |

Highest sampled value was **3.94 of 4** slots. Note this gauge is llama.cpp's *average* busy slots per decode step, so the number below is the highest average we sampled, not an instantaneous maximum batch width. A peak near 1 means
requests were served one at a time -- either the load was too light to overlap, or
they arrived too far apart. A peak approaching `--parallel` means the scheduler was
genuinely packing concurrent requests into shared decode steps.
`requests_deferred` went above zero: more requests arrived than there were slots, so some waited. That wait is the queue time in your P95.

## Your observation

**Peak batch width = 3.94 / 4 slots (98%)**, `requests_processing` chạm đúng 4. Vì gauge này là *trung bình tích luỹ* từ lúc server khởi động (giá trị tăng đơn điệu 3.879 -> 3.939 qua 30 sample), tôi tính lại theo cửa sổ 60 s từ chính CSV: `tokens_predicted_total` +9220 token trong `n_decode_total` +2367 step = **3.90 token/step**. Hai cách đo độc lập cho cùng một kết luận: trong suốt bài load 50 users, mỗi decode step gần như luôn phục vụ đủ 4 request. Continuous batching hoạt động đúng như thiết kế.

**Nó không khớp với effective concurrency 40.8 trong `02-server-results.md`, và điều đó không mâu thuẫn** — hai số đo hai thứ khác nhau:

- **3.94 / 4 = utilisation**, đo bên trong server, chỉ tính request đang được decode. Trần cứng là `--parallel` = 4.
- **40.8 = occupancy** (Little's Law: RPS x latency trung bình), tính cả request đang nằm trong hàng đợi. Không có trần.

Hiệu ~37 request chính là hàng đợi, và `requests_deferred` peak **46** xác nhận trực tiếp: nhiều request đến hơn số slot nên phải chờ. Nói cách khác, ~90% thời gian sống của một request ở 50 users là queue time.

**Tin cả hai, nhưng dùng cho câu hỏi khác nhau.** Để quyết định tuning tôi tin gauge của server (3.94): nó không phụ thuộc vào việc client mô phỏng bao nhiêu user, và nó trả lời "phần cứng còn dư không?" — không, đã 98%, nên thêm slot không tạo ra thêm tok/s. Số 40.8 trả lời "user cảm nhận gì?" — chờ gấp ~10 lần số slot; nó là hệ quả của tải chào vào, không phải năng lực server.

**Batching mang lại bao nhiêu?** 9220 token trong 58.2 s = **158 tok/s tổng**, so với **78.8 tok/s** single-stream ở `01-quickstart-results.md` -> gộp được **~2.0x**, không phải 4x dù batch rộng gần 4. Mỗi stream vì thế chỉ còn ~40 tok/s (TPOT ~25 ms so với 12.7 ms khi chạy một mình). Đó là mức lời thật của continuous batching trên máy này: 4 slot đổi lấy 2x throughput và 2x TPOT mỗi request — phần "concurrency" còn lại (40.8 so với 4) hoàn toàn là xếp hàng, không phải công việc song song.
