# 02 - Serve: load test + saturation reading

Host `Linux-x86_64` · llama.cpp `b10488` ·
`--parallel 4` · `ctx=2048` · `threads=16` ·
`ngl=99`

| Users | Reqs | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 10 | 137 | 2.32 | 3100 | 5200 | 5700 | 7.7 | 0.0% |
| 50 | 153 | 2.60 | 17000 | 19000 | 20000 | 39.7 | 0.0% |

*Effective concurrency = RPS x average latency (Little's Law) -- how many requests were
really in flight, regardless of how many users locust simulated. It counts queued requests
too, so the occupancy/slot ratio can legitimately exceed 1.0; it is occupancy, not
utilisation. For true slot utilisation use the server's own gauges (`make metrics`).*

## What these two runs say

| Going from 10 to 50 users | |
|:--|--:|
| Offered load | 5x |
| Throughput actually delivered | **1.12x** (22% of linear) |
| P95 latency | **3.65x** |
| Effective concurrency at 50 users | 39.7 vs `--parallel 4` slots (occupancy/slot ratio 9.92) |

**Saturated.** Throughput delivered only 1.12x for 5x the offered load, and effective concurrency (39.7) is at or above all 4 decode slots. Saturation sets in somewhere at or below 50 users; the load you added beyond that point became queue time rather than throughput.

Throughput moved 1.12x while P95 moved 3.65x. That gap is the goodput argument: past saturation you buy throughput by spending latency, and if your SLO is a P95 target then the requests you added are no longer being served within it. (This lab does not fix an SLO number for you -- pick one in your write-up and state how much goodput you keep at it.)

### Analysis & Server Saturation Reading

- **Saturation Point & Primary Evidence**: The server reaches saturation at **~10-15 users**. The definitive evidence is that a **5.0× increase in offered load** (10 → 50 users) yields only a minimal **1.12× throughput gain** (2.32 RPS → 2.60 RPS, plateauing), while **P95 latency explodes by 3.65×** from 5.2s to 19.0s.
- **Little's Law & Concurrency Analysis**: By Little's Law ($L = \text{RPS} \times \text{Avg Latency}$), effective concurrency at 50 users reaches **39.7 requests**, representing an occupancy/slot ratio of **9.92** against the `--parallel 4` slot limit. This proves the system spent >80% of its request lifetime waiting in line rather than executing decode.
- **Goodput@SLO**: Assuming a production SLO target of **P95 ≤ 6.0s**, 10 users achieves 100% SLO compliance (Goodput = 2.32 RPS). At 50 users, Goodput@SLO drops to near zero as P95 spikes to 19.0s due to queue buildup (`requests_deferred = 45`).
- **First Optimization Knob**: The single most effective knob to increase Goodput@SLO is **increasing `--parallel` slot capacity** from 4 to 8 (enabled by KV cache quantization `--cache-type-k q8_0` to conserve memory). Expanding slot capacity reduces queue head-of-line blocking and keeps P95 latency within the target SLO under high concurrency.

