# 01 - Tune: thread-count sweep

Model `gemma-4-E2B-it-UD-Q4_K_XL.gguf` · host `Linux-x86_64` · llama.cpp `b10488`
CPU: **16 physical · 32 logical** cores · `ngl=99` · metric `tg128`

| threads (-t) | tg128 (tok/s) | vs best |
|:--|--:|--:|
| 1 | 45.8 | 100% |
| 8 | 45.4 | 99% |
| 16 | 44.9 | 98% |
| 32 | 43.1 | 94% |
| 64 | 44.7 | 98% |

**Best**: `-t 1` at 45.8 tok/s
**Slowest tested**: `-t 32` at 43.1 tok/s (1.06x spread)
**Against the physical-core default** (`-t 16`, 44.9 tok/s): 1.02x

Use this in your run:

```bash
LAB_N_THREADS=1 make bench
```

## Your explanation

**Không có knee — curve phẳng.** 45.8 (`-t 1`) / 45.4 (`-t 8`) / 44.9 (`-t 16`) / 43.1 (`-t 32`) / 44.7 (`-t 64`) tok/s: spread chỉ **1.06x**, và so với default physical-core (`-t 16`) thì `-t 1` chỉ hơn **1.02x**. Đây là kết quả trái với hình dạng lab mô tả (leo tới số core vật lý rồi tụt), và nó trái vì một lý do đơn giản.

**Vì sao phẳng:** với `-ngl 99`, toàn bộ layer của model nằm trên iGPU (backend Vulkan) — decode chạy trên GPU, không trên CPU. `-t` chỉ điều khiển số thread CPU cho phần việc còn lại (sampling, vài op không offload, điều phối). Không còn matmul lớn nào trên CPU để chia cho 16-64 thread, nên cũng không có OpenMP barrier hay tranh chấp memory channel đáng kể: thêm thread không giúp gì, và cũng không phá gì. Hình dạng "knee ở physical cores" là hiện tượng của **CPU inference**; ở đây nó không có cơ hội xuất hiện.

Bằng chứng cho cách đọc đó nằm ở sweep `-ngl` (`bonus-gpu-offload-sweep.md`): `-ngl 0` (CPU thuần) chỉ 6.8 tok/s, `-ngl 99` là 38.7 tok/s — **5.73x**. Trên máy này, biến số quyết định là *ai chạy layer*, không phải *bao nhiêu thread*.

**Độ nhiễu của máy này (đọc kèm trước khi tin bất kỳ before/after nào).** Cùng một cấu hình `-t 16 -ngl 99` đo 3 lần trong ~15 phút cho 39.9 / 44.9 / 38.7 tok/s, tức nhiễu khoảng **+-8%** (máy đang dùng swap, và iGPU chia nhiệt/điện với CPU). Vì vậy mọi khác biệt dưới ~1.15x trên máy này là không kết luận được — và 1.06x của toàn bộ thread sweep nằm dưới ngưỡng đó.

**Đính chính một số liệu cũ.** Lần chạy sweep trước (commit `9061193`) báo `-t 16` = 22.6 và `-t 1` = 57.5 tok/s, tức "2.55x speedup nhờ giảm thread". Chạy lại đúng lệnh đó trên cùng máy **không tái lập được**: curve phẳng như bảng trên. Lần đo cũ diễn ra khi máy đã cạn RAM (swap 8/8 GB đầy, ~1.5 GB available) nên throughput bị swap thrashing chi phối — 2.55x là artifact của tình trạng bộ nhớ, không phải hiệu ứng thread. Số trong bảng này là số đo lại sau khi giải phóng RAM. Bài học đo lường thật của bước này: kiểm tra `free -h` (và nhiệt) *trước* khi tin một before/after, vì một máy đang swap sẽ sinh ra "kết quả tuning" nghe rất hợp lý mà hoàn toàn sai.
