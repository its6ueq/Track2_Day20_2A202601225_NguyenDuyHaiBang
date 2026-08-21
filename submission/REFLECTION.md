# Reflection — Day 20 Lab (Personal Report)

> **Đây là báo cáo cá nhân.** Số liệu của bạn **không** so sánh được với bạn cùng lớp
> — chỉ so **before vs after trên chính máy bạn**. Rubric chấm độ rõ ràng của setup,
> đo lường và **lập luận**, không chấm tốc độ tuyệt đối.

**Họ Tên:** Nguyễn Duy Hải Bằng
**Mã sinh viên (MSSV):** 2A202601225
**Cohort:** A20-K3
**Ngày submit:** 2026-08-21

---

## 1. Hardware & runtime  *(rubric 1, 2 — 10 điểm)*

> Từ `make probe`. Paste output hoặc điền tay.

- **OS:** Linux (x86_64)
- **CPU:** AMD Ryzen 9 8940HX with Radeon Graphics
- **Cores:** 16 physical / 32 logical
- **CPU extensions:** AVX2, AVX-512
- **RAM:** 14.9 GB
- **Accelerator:** Vulkan
- **llama.cpp asset đã tải:** b10488
- **Model đã dùng:** Gemma 4 E2B (`LAB_MODEL=gemma4-e2b`)
- **Quantization:** UD-Q4_K_XL + UD-Q2_K_XL (từ `models/active.json`)

**Chạy ở đâu:** laptop của tôi
_(Nếu dùng cloud fallback: nói rõ vì sao — RAM < 8 GB, setup fail, v.v. Không mất điểm.)_

**Setup story** (≤ 80 chữ): Quá trình setup tự động nhận diện phần cứng Linux AMD Ryzen 9 (16 nhân vật lý) và GPU Vulkan backend. Đã tự động tải runtime llama.cpp release b10488 cùng 2 file GGUF Gemma 4 E2B (2.97GB Q4 và 2.24GB Q2). Hệ thống không cài `make` mặc định nên các lệnh được thực thi qua Python script tương đương trong `.venv`.

---

## 2. Đo lường  *(rubric 3, 4, 5 — 20 điểm)*

> Paste bảng từ `benchmarks/01-quickstart-results.md` (`make bench` tự sinh).

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 4100 | 139 / 148 | 12.7 / 12.9 | 938 / 959 / 959 | 78.8 |
| UD-Q2_K_XL | 2.24 | 5074 | 152 / 164 | 14.9 / 15.0 | 1091 / 1107 / 1107 | 67.3 |

**Quan sát** (≤ 60 chữ): Q4_K_XL nhanh hơn Q2_K_XL **1.17×** (78.8 vs 67.3 tok/s), TPOT 12.7 vs 14.9 ms. Q2 không đáng dùng: RAM 14.9 GB dư nên tiết kiệm 0.73 GB không mua được gì, còn dequantize 2-bit tốn thêm compute mỗi decode step. Giảm bit chỉ nhanh hơn khi bị chặn bởi bandwidth — máy này bị chặn bởi compute.

---

## 3. Serving under load  *(rubric 8, 9, 10 — 20 điểm)*

> Từ `benchmarks/02-server-results.md` (`make load-report`).

| Users | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|
| 10 | 2.80 | 2500 | 4300 | 5000 | 7.4 | 0.0% |
| 50 | 2.97 | 15000 | 17000 | 18000 | 40.8 | 0.0% |

- **Offered load tăng 5×, throughput thực tăng:** 1.06× (21% của mức tăng lý tưởng)
- **P95 tăng:** 3.95× (4.3 s → 17 s)
- **Effective concurrency ở 50 users:** 40.8 so với `--parallel` = 4 slots (occupancy/slot = 10.19)

**Peak `llamacpp:n_busy_slots_per_decode`** (từ `make metrics` khi `make load-50` đang chạy): 3.94 / 4 slots (98%); `requests_deferred` peak 46. Tính lại theo cửa sổ 60 s từ CSV: 9220 token / 2367 decode step = **3.90 token mỗi step** — hai cách đo độc lập cùng cho ra batch gần như luôn đầy 4.

**Saturation reading** (≤ 80 chữ): Bão hòa ở khoảng 10 users, chắc chắn dưới 50. Load ×5 nhưng RPS chỉ ×1.06 trong khi P95 ×3.95; slot đã 98% đầy và `requests_deferred` = 46, nên phần tăng thêm là queue time. Với SLO P95 ≤ 5 s: goodput 2.80 RPS ở 10 users, **~0 ở 50 users** (P50 đã 15 s). Việc tôi làm trước tiên là **chặn concurrency ở đầu vào (~10–12 in-flight, fail fast phần vượt)**, không phải tăng `--parallel`: `--ctx-size 2048` bị chia cho `--parallel` (log server: `n_ctx_slot = 512`), nên 8 slot còn 256 token/slot — không đủ cho request `long-rag`. Thêm slot chỉ chia lại cùng một lượng compute; chặn đầu vào mới cứu được P95. Sau đó mới tới prefix caching cho context RAG lặp lại.

---

## 4. Integration  *(rubric 12, 13 — 15 điểm)*

> Từ `make pipeline`. Nói thật cái nào real, cái nào stub — stub **không** mất điểm.

| Day | Piece | Real hay stub? |
|---|---|---|
| N16 Cloud/IaC | Doc Ingestion & Chunking | **stub** — `TOY_DOCS`, 6 doc hard-code trong `pipeline.py`, không có ingestion/chunking thật |
| N17 Data pipeline | Embedding Generation | stub — không chạy `--embed-url`, rơi về keyword fallback (0.0 ms) |
| N18 Lakehouse | Vector Index & Retrieval | stub — keyword overlap scoring trên list in-memory |
| N19 Vector + features | Prompt Construction | real (code `build_prompt()` chạy thật) nhưng context đầu vào lấy từ stub N16/N18 |
| N20 Serving | llama-server | real — HTTP `/v1/chat/completions` tới llama-server b10488 |

**Latency split** (mean của 3 query, từ output của `pipeline.py`):

- embed: 0.0 ms
- retrieve: 0.0 ms
- llm: 17083.5 ms
- **stage chiếm nhiều nhất:** llm (100% của total)

**Reflection** (≤ 60 chữ): Bottleneck nằm 100% ở stage LLM Generation (17.08s), hoàn toàn khớp với kỳ vọng khi suy luận LLM trên CPU. Để giảm 2× latency pipeline, tôi sẽ áp dụng Prompt Caching (Prefix Caching) để lưu cache KV state của tài liệu RAG, giảm 80-90% TTFT prefill.

---

## 5. The single change that mattered most  *(rubric 11 — 10 điểm)*

> **Phần quan trọng nhất của report.** Không cần bonus track: `make tune` đã cho bạn
> một before/after thật (`benchmarks/01-tuning-tg128.md`). Đổi quantization,
> `LAB_N_CTX`, hay `--parallel` rồi đo lại cũng được.

**Change:** Bật GPU offload — `-ngl 0` (CPU thuần) → `-ngl 99` (toàn bộ layer lên iGPU Vulkan). Đo bằng `llama-bench` metric `tg128`, cùng máy, cùng build, cách nhau vài phút (`benchmarks/bonus-gpu-offload-sweep.md`).

```
before:   6.8 tok/s  (-ngl 0,  CPU thuần, -t 16)
after:   38.7 tok/s  (-ngl 99, toàn bộ layer trên iGPU, -t 16)
speedup: 5.73×
```

Curve tăng đơn điệu, không có đỉnh ở partial offload: 6.8 → 8.6 (`-ngl 8`) → 11.5 (16) → 18.2 (24) → 25.8 (32) → 38.7 (99).

**Tại sao nó work** (1–2 đoạn — đây là phần grader đọc kỹ nhất):

Máy này là AMD Ryzen 9 8940HX với iGPU Radeon, tức **GPU dùng chung chính bus DDR5 với CPU** — không có VRAM rời. Vì thế điều mà offload mua được **không phải băng thông**: weight vẫn đi qua đúng một bus đó, với đúng băng thông đó. Cái được mua là **compute**. Mỗi decode step phải dequantize khối Q4_K rồi nhân matrix-vector; iGPU có nhiều đơn vị nhân-tích-luỹ song song hơn hẳn và làm phần dequantize trong shader rẻ hơn so với thực thi trên core CPU. Mỗi layer đẩy sang GPU lấy bớt một phần công việc đó khỏi CPU, nên throughput tăng gần tỉ lệ với số layer đã chuyển — chính là hình dạng mượt, không bậc thang, của sweep. Nó cũng giải thích vì sao không có đỉnh ở partial: model Q4 chỉ 2.95 GiB, nằm trọn trong vùng nhớ iGPU dùng được, nên không có gì "hết chỗ" để bắt curve gãy.

Hai phép đo độc lập khác trong lab xác nhận cùng một chẩn đoán — **máy này compute-limited, không bandwidth-limited** — và đó là lý do tôi tin con số 5.73× này chứ không phải một artifact: (1) `UD-Q2_K_XL` đọc ít byte hơn 0.73 GB nhưng **chậm hơn 1.17×** vì thêm việc dequantize (§2); (2) thread sweep **phẳng, spread chỉ 1.06×** (`benchmarks/01-tuning-tg128.md`) vì khi layer đã nằm trên GPU thì CPU thread không còn matmul nào để chia. Cả ba đều chỉ về compute. Thực tế đây cũng là knob duy nhất tôi đo được có tác động lớn hơn nhiễu của máy (±8%): 5.73× so với 1.17× của quantization và 1.06× của thread count.

---

## 6. Bonus  *(optional — tối đa 20 điểm)*

> Bỏ trống nếu không làm. Xem `bonus/README.md`. Đừng làm hết — **một** finding sâu
> ăn điểm hơn năm bảng nông.

**Đã làm:** `bonus/sweeps/gpu-offload-sweep.py` (→ `benchmarks/bonus-gpu-offload-sweep.md`), cộng với một finding về **độ tin cậy của phép đo** phát sinh khi tôi kiểm tra lại chính số liệu của mình.

**Numbers:**

```
GPU offload sweep (tg128, -t 16):
  -ngl  0 →  6.8 tok/s     -ngl 24 → 18.2 tok/s
  -ngl  8 →  8.6 tok/s     -ngl 32 → 25.8 tok/s
  -ngl 16 → 11.5 tok/s     -ngl 99 → 38.7 tok/s   (5.73× so với CPU thuần)

Cùng một cấu hình (-t 16 -ngl 99) đo 3 lần trong ~15 phút:
  39.9 / 44.9 / 38.7 tok/s   → nhiễu ±8%

Thread sweep, lần đo cũ (máy đang swap, ~1.5 GB available, swap 8/8 GB):
  -t 16 → 22.6 tok/s   -t 1 → 57.5 tok/s   ("2.55×")
Thread sweep, đo lại sau khi giải phóng RAM:
  -t 1 → 45.8   -t 8 → 45.4   -t 16 → 44.9   -t 32 → 43.1   -t 64 → 44.7   (spread 1.06×)
```

**Điều này nói lên gì mà deck chưa nói:**

Deck dạy cách *đo* TTFT/TPOT/goodput, nhưng không nói rằng **một máy đang thiếu RAM sẽ sinh ra kết quả tuning nghe rất hợp lý mà hoàn toàn sai**. Bản nộp trước của tôi kết luận "giảm `-t 16` xuống `-t 1` cho 2.55× vì OpenMP barrier và L3 cache-line bouncing" — một lời giải thích đúng sách vở, khớp với hình dạng curve mà lab dự đoán, và **không tái lập được**. Khi chạy lại đúng lệnh đó sau khi giải phóng RAM, curve phẳng (1.06×). Điều thực sự xảy ra ở lần đo cũ: swap đã đầy 8/8 GB, llama-server bị evict weight (RSS còn 154 MB) và tụt về ~1 tok/s, nên các điểm đo chỉ đang lấy mẫu mức độ thrashing tại thời điểm đó chứ không phải hiệu ứng của `-t`. Cùng nguyên nhân đó đã làm lần chạy `load-10` đầu tiên của tôi chỉ hoàn thành 4 request trong 60 s (0.13 RPS) trước khi tôi phát hiện và đo lại.

Ba hệ quả tôi rút ra, và đã áp dụng vào chính bản nộp này:

1. **Ghi lại trạng thái máy cùng với số liệu.** `free -h` và tình trạng nhiệt là *một phần* của phép đo, không phải bối cảnh bên lề. Một dòng "swap 8/8 GB" đủ để vô hiệu hóa cả bảng số.
2. **Đo nhiễu trước khi tin một tỉ lệ.** Cùng cấu hình lặp 3 lần cho ±8% trên máy này, nên mọi khác biệt dưới ~1.15× là không kết luận được. Theo ngưỡng đó: GPU offload (5.73×) là thật, quantization (1.17×) vừa đủ qua ngưỡng, thread count (1.06×) là nhiễu. Bản nộp cũ đã báo cáo nhiễu như thể là finding.
3. **Cảnh giác khi lời giải thích khớp quá đẹp.** Cơ chế OpenMP/CCX kia là thật *trong ngữ cảnh CPU inference*; nó chỉ không phải nguyên nhân của số liệu của tôi (`-ngl 99` = mọi layer trên GPU, CPU thread gần như không có matmul để chạy). Một cơ chế đúng vẫn có thể là lời giải thích sai cho một phép đo cụ thể.

**Một câu hỏi tôi để mở, có ghi lại thay vì lấp liếm:** hai harness không khớp nhau về giá trị tuyệt đối. `llama-server` báo decode 78.8 tok/s (§2, và log của chính llama.cpp trong screenshot 03a: 13.21 ms/token = 75.68 tok/s), còn `llama-bench tg128` cùng model/`-ngl 99`/`-t 16` chỉ cho 38.7–45.8 tok/s. Khoảng cách ~1.75× này lớn hơn nhiễu ±8%, nên không phải nhiễu. Hai harness khác nhau ở nhiều điểm (server: 64 token sau prompt ngắn, có `--cont-batching`, 4 slot, `n_ctx_slot=512`, đo qua HTTP; llama-bench: 128 token từ context rỗng, một stream, không HTTP), và `-fa` mặc định `auto` ở cả hai nên flash-attention không phải nguyên nhân. Tôi **chưa** xác định được nguyên nhân, nên tôi không so tuyệt đối giữa hai harness ở bất kỳ đâu trong báo cáo này — mọi tỉ lệ before/after đều lấy trong cùng một harness và cùng một session. Để giải quyết, việc cần làm là chạy cả hai back-to-back với `-n` bằng nhau, `-fa on` cố định, `--parallel 1`, và power profile ghim cứng.

---

## 7. Điều làm bạn ngạc nhiên nhất  *(optional)*

Điều ngạc nhiên nhất là **finding lớn nhất của tôi bốc hơi khi tôi kiểm tra lại nó.** Tôi đã có một before/after 2.55× từ thread sweep, kèm một cơ chế giải thích nghe rất thuyết phục (OpenMP barrier, L3 cache-line bouncing giữa các CCD) và khớp đúng hình dạng curve mà lab dự đoán. Chạy lại đúng lệnh đó sau khi giải phóng RAM: curve phẳng, spread 1.06×. Toàn bộ "hiệu ứng" trước đó chỉ là máy đang swap thrashing.

Điều đáng ngạc nhiên thứ hai, và là lý do cái thứ nhất tồn tại được lâu như vậy: `-t` gần như **không có tác dụng gì** khi `-ngl 99`. Tôi vẫn ngầm nghĩ "nhiều core = nhanh hơn (hoặc chậm hơn)" trong khi mọi layer đã nằm trên iGPU và CPU chỉ còn sampling. Knob thật sự quan trọng là `-ngl` (5.73×) — thứ tôi ban đầu coi là mặc định hiển nhiên, không phải một quyết định tuning.

---

## 8. Self-check trước khi push

- [x] `hardware.json` committed
- [x] `models/active.json` committed
- [x] `benchmarks/01-quickstart-results.md` committed (`make bench`)
- [x] `benchmarks/01-tuning-tg128.md` committed (`make tune`)
- [x] `benchmarks/02-server-results.md` committed (`make load-report`)
- [x] `benchmarks/02-server-batching-u50.md` hoặc `-metrics-u50.csv` committed (`make metrics`)
- [x] `benchmarks/locust-10_stats.csv` + `locust-50_stats.csv` committed (`make load-10` / `load-50`)
- [x] `benchmarks/03-integration-results.md` committed (`make pipeline`)
- [x] `benchmarks/bonus-gpu-offload-sweep.md` committed (bonus §6)
- [x] Mọi section **"required — replace this line"** trong các file `benchmarks/*.md` đã được thay bằng nhận xét của bạn
- [x] 5 screenshots trong `submission/screenshots/`
- [x] `make verify` → **exit 0**
- [x] Repo GitHub ở chế độ **public**
- [x] Đã paste public URL vào VinUni LMS
- [x] **Không** commit `models/*.gguf` hay `runtime/` (đã có trong `.gitignore`)

**Quan trọng:** repo phải **public** đến khi điểm được công bố. Private → grader không xem được → 0 điểm.


