# Reflection — Day 20 Lab (Personal Report)

> **Đây là báo cáo cá nhân.** Số liệu của bạn **không** so sánh được với bạn cùng lớp
> — chỉ so **before vs after trên chính máy bạn**. Rubric chấm độ rõ ràng của setup,
> đo lường và **lập luận**, không chấm tốc độ tuyệt đối.

**Họ Tên:** Nguyễn Duy Hải Bằng
**Mã sinh viên (MSSV):** 2A202601225
**Cohort:** A20-K1
**Ngày submit:** 2026-08-20

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
| UD-Q4_K_XL | 2.97 | 9162 | 144 / 923 | 13.2 / 41.2 | 1053 / 2735 / 2735 | 75.6 |
| UD-Q2_K_XL | 2.24 | 12798 | 158 / 1465 | 16.4 / 45.1 | 1244 / 3008 / 3008 | 60.8 |

**Quan sát** (≤ 60 chữ): UD-Q4_K_XL nhanh hơn UD-Q2_K_XL 1.24× ở tốc độ decode (75.6 vs 60.8 tok/s). UD-Q2_K_XL KHÔNG đáng dùng: RAM 14.9GB dồi dào nên giảm 0.73GB không có tác dụng, trong khi phép giải nén 2-bit tốn thêm CPU compute làm chậm tốc độ và giảm chất lượng suy luận.

---

## 3. Serving under load  *(rubric 8, 9, 10 — 20 điểm)*

> Từ `benchmarks/02-server-results.md` (`make load-report`).

| Users | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|
| 10 | 2.32 | 3100 | 5200 | 5700 | 7.7 | 0.0% |
| 50 | 2.60 | 17000 | 19000 | 20000 | 39.7 | 0.0% |

- **Offered load tăng 5×, throughput thực tăng:** 1.12×
- **P95 tăng:** 3.65×
- **Effective concurrency ở 50 users:** 39.7 so với `--parallel` = 4 slots

**Peak `llamacpp:n_busy_slots_per_decode`** (từ `make metrics` khi `make load-50` đang chạy): 3.98 / 4 slots

**Saturation reading** (≤ 80 chữ): Server bão hòa ở mức 10-15 users. Bằng chứng: Load tăng 5× nhưng RPS chỉ tăng 1.12× (plateau) trong khi P95 tăng 3.65× (5.2s → 19s). Latency tăng hoàn toàn là Queue Time (`requests_deferred = 45`). Để nâng Goodput@SLO, tôi sẽ tăng `--parallel` từ 4 lên 8 slots (kết hợp cache quant `q8_0`) để giảm xếp hàng.

---

## 4. Integration  *(rubric 12, 13 — 15 điểm)*

> Từ `make pipeline`. Nói thật cái nào real, cái nào stub — stub **không** mất điểm.

| Day | Piece | Real hay stub? |
|---|---|---|
| N16 Cloud/IaC | Doc Ingestion & Chunking | real |
| N17 Data pipeline | Embedding Generation | stub |
| N18 Lakehouse | Vector Index & Retrieval | stub |
| N19 Vector + features | Prompt Construction | real |
| N20 Serving | llama-server | real |

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

**Change:** Tối ưu hóa số luồng tính toán CPU (`-t 16` hạ xuống `-t 1` hoặc `-t 4` cho llama-server)

```
before:  22.6 tok/s (-t 16 physical cores default)
after:   57.5 tok/s (-t 1 tuned)
speedup: 2.55×
```

**Tại sao nó work** (1–2 đoạn — đây là phần grader đọc kỹ nhất):

Trên bộ xử lý AMD Ryzen 9 8940HX (16 nhân vật lý / 32 nhân logic), quá trình sinh token (decode phase) cho mô hình nhỏ Gemma 4 E2B (~2.97 GB) bị giới hạn hoàn toàn bởi băng thông bộ nhớ (Memory Bandwidth Bound). Một nhân CPU duy nhất đã đủ khả năng làm bão hòa bus băng thông RAM của hệ thống.

Khi để default `-t 16`, llama.cpp buộc phải thực thi các điểm đồng bộ luồng (OpenMP thread barriers) ở từng layer matrix-vector multiplication. Việc truyền dữ liệu giữa các nhân thuộc các CCX/CCD khác nhau gây ra hiện tượng L3 cache line bouncing, trễ đồng bộ hàng chờ luồng và context switching overhead. Bằng cách hạ số luồng xuống `-t 1` hoặc `-t 4`, loại bỏ được chi phí đồng bộ luồng vô ích, giúp băng thông RAM được khai thác tối đa và mang lại gia tăng tốc độ tới 2.55×.

---

## 6. Bonus  *(optional — tối đa 20 điểm)*

> Bỏ trống nếu không làm. Xem `bonus/README.md`. Đừng làm hết — **một** finding sâu
> ăn điểm hơn năm bảng nông.

**Đã làm:** _(để trống nếu không làm)_

**Numbers:**

```
before:  0
after:   0
speedup: 1.0x
```

**Điều này nói lên gì mà deck chưa nói:**

_(để trống)_

---

## 7. Điều làm bạn ngạc nhiên nhất  *(optional)*

Điều ngạc nhiên nhất là việc tăng số luồng CPU (`-t 16`) không những không làm mô hình chạy nhanh hơn mà lại làm tụt hiệu năng tới 2.55× so với chạy 1 luồng (`-t 1`), minh chứng rõ ràng cho bài học Memory Bandwidth bottleneck và OpenMP barrier overhead trong LLM serving.

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
- [x] Mọi section **"required — replace this line"** trong các file `benchmarks/*.md` đã được thay bằng nhận xét của bạn
- [x] 5 screenshots trong `submission/screenshots/`
- [x] `make verify` → **exit 0**
- [x] Repo GitHub ở chế độ **public**
- [x] Đã paste public URL vào VinUni LMS
- [x] **Không** commit `models/*.gguf` hay `runtime/` (đã có trong `.gitignore`)

**Quan trọng:** repo phải **public** đến khi điểm được công bố. Private → grader không xem được → 0 điểm.


