# 02 - Serve: load test + saturation reading

Host `Linux-x86_64` · llama.cpp `b10488` ·
`--parallel 4` · `ctx=2048` · `threads=16` ·
`ngl=99`

| Users | Reqs | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 10 | 165 | 2.80 | 2500 | 4300 | 5000 | 7.4 | 0.0% |
| 50 | 175 | 2.97 | 15000 | 17000 | 18000 | 40.8 | 0.0% |

*Effective concurrency = RPS x average latency (Little's Law) -- how many requests were
really in flight, regardless of how many users locust simulated. It counts queued requests
too, so the occupancy/slot ratio can legitimately exceed 1.0; it is occupancy, not
utilisation. For true slot utilisation use the server's own gauges (`make metrics`).*

## What these two runs say

| Going from 10 to 50 users | |
|:--|--:|
| Offered load | 5x |
| Throughput actually delivered | **1.06x** (21% of linear) |
| P95 latency | **3.95x** |
| Effective concurrency at 50 users | 40.8 vs `--parallel 4` slots (occupancy/slot ratio 10.19) |

**Saturated.** Throughput delivered only 1.06x for 5x the offered load, and effective concurrency (40.8) is at or above all 4 decode slots. Saturation sets in somewhere at or below 50 users; the load you added beyond that point became queue time rather than throughput.

Throughput moved 1.06x while P95 moved 3.95x. That gap is the goodput argument: past saturation you buy throughput by spending latency, and if your SLO is a P95 target then the requests you added are no longer being served within it. (This lab does not fix an SLO number for you -- pick one in your write-up and state how much goodput you keep at it.)

## Your reading

**Server bão hòa ở khoảng 10 users, chắc chắn dưới 50.** Con số thuyết phục tôi: offered load tăng **5x** nhưng throughput chỉ tăng **1.06x** (2.80 -> 2.97 RPS, tức 21% mức tăng lý tưởng), trong khi P95 tăng **3.95x** (4.3 s -> 17 s). Throughput đứng yên trong khi latency tăng gần tuyến tính theo số user = mọi user thêm vào chỉ biến thành queue time, không thành công việc.

Bằng chứng phía server khớp đúng (`02-server-batching-u50.md`): `n_busy_slots_per_decode` đạt **3.94 / 4 slots (98%)** và `requests_deferred` lên tới **46**. Cả 4 decode slot đã đầy gần như liên tục, phần còn lại xếp hàng. Effective concurrency 40.8 so với 4 slot (occupancy/slot = 10.19) nói cùng một điều từ phía client: ở 50 users, khoảng 90% thời gian sống của một request là chờ, không phải decode.

**Goodput@SLO.** Chọn SLO E2E P95 <= 5 s: ở 10 users P95 = 4.3 s nên gần như toàn bộ 2.80 RPS đạt SLO; ở 50 users P95 = 17 s và ngay cả P50 đã là 15 s, nên goodput sụp về **~0 RPS** dù throughput thô vẫn 2.97 RPS. Cùng một server, throughput tăng nhẹ mà goodput mất sạch — đó là lý do phải đo goodput chứ không phải RPS.

**Knob tôi đổi trước tiên: chặn concurrency ở đầu vào (admission control / bounded queue ~10-12 request in-flight, vượt thì fail fast), không phải tăng `--parallel`.** Lý do: 4 slot đã ở 98% occupancy nên phần cứng không còn dư để khai thác; và `--ctx-size 2048` là context *tổng*, llama-server chia cho `--parallel` (log khởi động: `n_slots = 4, n_ctx_slot = 512`), nên nâng lên `--parallel 8` sẽ cắt còn 256 token/slot — không đủ cho request `long-rag`, trừ khi tôi nâng `--ctx-size` lên 4096 và trả thêm KV cache. Thêm slot chỉ chia lại cùng một lượng bandwidth/compute cho nhiều stream hơn: tổng tok/s gần như không đổi, TPOT mỗi request xấu hơn, P95 không cải thiện. Chặn ở đầu vào thì phần request được nhận giữ được P95 dưới SLO -> goodput tăng ngay dù throughput thô không đổi. Sau đó mới tới các knob thực sự thêm capacity: prefix caching cho phần context RAG lặp lại (giảm 2834 prefill token đã đo trong cửa sổ 60 s), giảm `max_tokens`, hoặc dùng quant/model nhanh hơn.

*Ghi chú đọc số:* bảng trên lấy từ `locust-*_stats.csv`; ảnh chụp terminal (`submission/screenshots/04`, `05`) hiện tổng cao hơn vài request (168 và 179 so với 165 và 175) vì locust ghi CSV ngay trước khi các request cuối còn in-flight kịp hoàn tất. Các cột percentile 50/95/99% của hai nguồn trùng khớp tuyệt đối.
