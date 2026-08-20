# 02 - Continuous batching under load (u50)

Host `Linux-x86_64` · `--parallel 4` · 30 samples over
60s at 2.0s intervals · raw CSV: `02-server-metrics-u50.csv`

| Gauge | Peak observed |
|:--|--:|
| `n_busy_slots_per_decode` (avg/decode) | 3.98 of 4 slots (99%) |
| `requests_processing` | 4 |
| `requests_deferred` | 45 |
| `kv_cache_usage_ratio` | n/a — not exported by llama.cpp `b10488` |
| `tokens_predicted_total` (final) | 16320 |

Highest sampled value was **3.98 of 4** slots. Note this gauge is llama.cpp's *average* busy slots per decode step, so the number below is the highest average we sampled, not an instantaneous maximum batch width. A peak near 1 means
requests were served one at a time -- either the load was too light to overlap, or
they arrived too far apart. A peak approaching `--parallel` means the scheduler was
genuinely packing concurrent requests into shared decode steps.
`requests_deferred` went above zero: more requests arrived than there were slots, so some waited. That wait is the queue time in your P95.

### Analysis & Continuous Batching Evidence

- **Peak Batch Width**: The peak sampled `n_busy_slots_per_decode` was **3.98 of 4 slots (99.5%)**. This proves that `llama-server`'s continuous batching scheduler was actively multiplexing up to 4 concurrent decode sequences into a single parallel matrix-vector execution step.
- **Queueing & Saturation Impact**: During peak load, `requests_deferred` reached **45 requests**, meaning 45 client requests were waiting in the HTTP request queue because all 4 execution slots were fully occupied (`requests_processing = 4`). This queue delay is the primary contributor to the sharp escalation in P95/P99 latencies observed under 50 users.

