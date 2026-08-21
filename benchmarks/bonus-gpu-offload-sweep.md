# Bonus - GPU offload sweep

Host `Linux-x86_64` · backend(s) `vulkan` ·
llama.cpp `b10488` · `threads=16` · metric `tg128`

| -ngl | tg128 (tok/s) | vs -ngl 0 | vs best |
|:--|--:|--:|--:|
| 0 | 6.8 | 1.00x | 17% |
| 8 | 8.6 | 1.27x | 22% |
| 16 | 11.5 | 1.70x | 30% |
| 24 | 18.2 | 2.69x | 47% |
| 32 | 25.8 | 3.82x | 67% |
| 99 | 38.7 | 5.73x | 100% |

Best: `-ngl 99` at 38.7 tok/s
-- 5.73x faster than CPU-only.

Where the curve flattens tells you the model ran out of layers to move. Where it
*peaks below* full offload tells you something did not fit and the accelerator
started paying to fetch weights it could not hold.

## Your finding

**Full offload thắng, và curve tăng đơn điệu — không có đỉnh ở partial:** 6.8 -> 8.6 -> 11.5 -> 18.2 -> 25.8 -> **38.7 tok/s** (`-ngl 0 -> 99` = **5.73x**). Không có gì "hết chỗ" trước khi tới full offload: model Q4_K_XL 2.95 GiB nằm trọn trong vùng nhớ mà iGPU dùng được, và máy này không có VRAM rời để tràn — iGPU Radeon chia sẻ chính 14.9 GB DDR5 với CPU.

**Cái gì thực sự được mua ở đây là compute, không phải bandwidth.** Vì host và device dùng cùng một bus DDR5, chuyển layer sang GPU không làm weight được đọc nhanh hơn. Phần lời đến từ chỗ khác: iGPU có nhiều đơn vị nhân-tích-luỹ song song hơn và dequantize Q4_K trong shader rẻ hơn so với làm trên core CPU. Mỗi layer chuyển sang GPU lấy bớt một phần matmul khỏi CPU, nên throughput tăng gần như tỉ lệ với số layer đã chuyển — đó chính là hình dạng mượt, không bậc thang, của bảng trên.

Kết luận này khớp với hai phép đo độc lập khác trong lab, và cả ba cùng nói một điều: **máy này compute-limited, không memory-bandwidth-limited.**

- `01-quickstart-results.md`: `UD-Q2_K_XL` giảm 0.73 GB nhưng **chậm hơn 1.17x** — giảm byte mà thêm việc dequantize thì lỗ.
- `01-tuning-tg128.md`: thread sweep **phẳng (1.06x)** — vì compute đã nằm trên GPU, CPU thread không còn gì để làm.

**Cảnh báo khi so với GPU rời:** trên GPU rời, partial offload trả thêm giá cho việc copy activation qua PCIe ở mỗi ranh giới layer, nên curve thường gãy khúc và có thể peak dưới full offload khi VRAM hết. Ở đây không có PCIe hop và không có giới hạn VRAM riêng, nên đừng suy diễn hình dạng curve này sang máy có GPU rời.

**Xếp hạng các knob đã đo trên máy này:** GPU offload **5.73x** >> quantization 1.17x (và ngược dấu) > thread count 1.06x (trong nhiễu). Nếu chỉ được đổi một thứ, đổi `-ngl`.
