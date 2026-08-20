# 01 - Measure: latency baseline

Model `Gemma 4 E2B` · host `Linux-x86_64` · llama.cpp `b10488`
Settings: `threads=16` `ngl=99` `ctx=2048`
`max_tokens=64` · warm-up discarded
Completed requests: `UD-Q4_K_XL` 10/10 · `UD-Q2_K_XL` 10/10

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 9162 | 144 / 923 | 13.2 / 41.2 | 1053 / 2735 / 2735 | 75.6 |
| UD-Q2_K_XL | 2.24 | 12798 | 158 / 1465 | 16.4 / 45.1 | 1244 / 3008 / 3008 | 60.8 |

- **TTFT** = prefill. Short prompts keep it small; long-context RAG is where it explodes.
- **TPOT** = per-output-token decode cost, bounded by memory bandwidth. `decode tok/s = 1000 / TPOT_p50`.
- `UD-Q2_K_XL` decodes **1.24x SLOWER** than `UD-Q4_K_XL` here, despite being 0.73 GB smaller. That is a real result, not a mistake: fewer bits only buys speed when decode is limited by memory bandwidth. On a machine that is compute-limited instead — few cores, no GPU offload — the extra dequantization work of a heavily-quantized format can cost more than the bytes it saves. Say which case yours is.

### Analysis & Quantization Comparison

- **Speed & Latency**: `UD-Q4_K_XL` (4-bit) achieved a decode throughput of **75.6 tok/s** (TPOT P50 = 13.2 ms, TTFT P50 = 144 ms) whereas `UD-Q2_K_XL` (2-bit) achieved **60.8 tok/s** (TPOT P50 = 16.4 ms, TTFT P50 = 158 ms). `UD-Q4_K_XL` is **1.24× faster** in decode throughput than `UD-Q2_K_XL`.
- **Memory vs Compute Overhead**: Although `UD-Q2_K_XL` saves 0.73 GB of disk/RAM (2.24 GB vs 2.97 GB), the bit-unpacking and dequantization math for 2-bit quantized tensors introduces substantial CPU compute overhead. On this AMD Ryzen 9 8940HX system, the bottleneck shifts to compute dequantization rather than memory bandwidth alone.
- **Conclusion & Quality Judgment**: `UD-Q2_K_XL` is **not worth using** on this machine. Because system RAM (14.9 GB) is plentiful, the 0.73 GB memory savings provides no benefit, while `UD-Q4_K_XL` offers higher output quality, better reasoning retention, and 24% faster generation speed.

