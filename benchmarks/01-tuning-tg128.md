# 01 - Tune: thread-count sweep

Model `gemma-4-E2B-it-UD-Q4_K_XL.gguf` · host `Linux-x86_64` · llama.cpp `b10488`
CPU: **16 physical · 32 logical** cores · `ngl=99` · metric `tg128`

| threads (-t) | tg128 (tok/s) | vs best |
|:--|--:|--:|
| 1 | 57.5 | 100% |
| 8 | 53.1 | 92% |
| 16 | 22.6 | 39% |
| 32 | 22.9 | 40% |
| 64 | 22.0 | 38% |

**Best**: `-t 1` at 57.5 tok/s
**Slowest tested**: `-t 64` at 22.0 tok/s (2.62x spread)
**Against the physical-core default** (`-t 16`, 22.6 tok/s): 2.55x

Use this in your run:

```bash
LAB_N_THREADS=1 make bench
```

### Analysis & Mechanical Explanation

- **Knee & Optimal Thread Count**: The peak performance sits at `-t 1` (**57.5 tok/s**), maintaining high throughput at `-t 8` (**53.1 tok/s**), but precipitously drops at `-t 16` (**22.6 tok/s**, a 2.55× throughput reduction).
- **Physical vs Logical Cores Breakdown**: On this 16 physical / 32 logical core AMD Ryzen 9 8940HX processor, token generation (decode stage) for a small ~2.97 GB model is severely memory-bandwidth bound. A single core (or small cluster of cores) is already capable of fully saturating the system's memory bandwidth bus for sequential matrix-vector multiplications.
- **Barrier Synchronization & Cache Thrashing Penalty**: Spreading the workload across 16+ threads forces llama.cpp to perform OpenMP thread synchronization barriers at every single layer of the neural network. Inter-core communication across different Core Complex Dies (CCDs/CCXs), combined with L3 cache line bouncing and context switching overhead, creates a massive thread synchronization penalty that destroys decode throughput (dropping from 57.5 tok/s down to 22.0-22.9 tok/s).
- **Practical Recommendation**: For single-sequence inference on low-parameter models on this hardware, setting `LAB_N_THREADS=1` yields a **2.55× speedup** over the naive physical core default (`-t 16`).

