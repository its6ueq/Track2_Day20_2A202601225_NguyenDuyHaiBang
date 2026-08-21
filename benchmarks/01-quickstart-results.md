# 01 - Measure: latency baseline

Model `Gemma 4 E2B` · host `Linux-x86_64` · llama.cpp `b10488`
Settings: `threads=16` `ngl=99` `ctx=2048`
`max_tokens=64` · warm-up discarded
Completed requests: `UD-Q4_K_XL` 10/10 · `UD-Q2_K_XL` 10/10

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 4100 | 139 / 148 | 12.7 / 12.9 | 938 / 959 / 959 | 78.8 |
| UD-Q2_K_XL | 2.24 | 5074 | 152 / 164 | 14.9 / 15.0 | 1091 / 1107 / 1107 | 67.3 |

- **TTFT** = prefill. Short prompts keep it small; long-context RAG is where it explodes.
- **TPOT** = per-output-token decode cost, bounded by memory bandwidth. `decode tok/s = 1000 / TPOT_p50`.
- `UD-Q2_K_XL` decodes **1.17x SLOWER** than `UD-Q4_K_XL` here, despite being 0.73 GB smaller. That is a real result, not a mistake: fewer bits only buys speed when decode is limited by memory bandwidth. On a machine that is compute-limited instead — few cores, no GPU offload — the extra dequantization work of a heavily-quantized format can cost more than the bytes it saves. Say which case yours is.

## Your observation

**Không đáng.** `UD-Q2_K_XL` nhỏ hơn 0.73 GB (2.24 vs 2.97 GB) nhưng decode **chậm hơn 1.17x** (67.3 vs 78.8 tok/s): TPOT P50 tăng 12.7 -> 14.9 ms và E2E P50 tăng 938 -> 1091 ms. TTFT gần như không đổi (139 vs 152 ms) vì prompt ở đây quá ngắn để prefill lộ ra khác biệt — toàn bộ thiệt hại nằm ở decode.

Máy này không bị chặn bởi dung lượng bộ nhớ: RAM 14.9 GB, model Q4 chỉ 2.97 GB, nên 0.73 GB tiết kiệm được không mua thêm được slot hay context nào. Đổi lại, mỗi decode step phải dequantize weight 2-bit — Q2_K dùng super-block với nhiều scale/min hơn trên mỗi weight so với Q4_K — và phần compute thêm đó đắt hơn số byte đọc ít đi. Đây đúng là trường hợp thứ hai mà ghi chú trên nói tới: giảm bit chỉ tăng tốc khi decode bị chặn bởi memory bandwidth, còn khi đã bị chặn bởi compute thì giảm bit làm chậm đi.

Quyết định: giữ `UD-Q4_K_XL`. `UD-Q2_K_XL` chỉ hợp lý nếu tôi bị chặn cứng bởi dung lượng (model không nạp nổi, hoặc cần thêm KV cache cho context dài), chứ không phải để đổi lấy tốc độ — ở đây nó thua trên cả hai mặt tốc độ và chất lượng.
