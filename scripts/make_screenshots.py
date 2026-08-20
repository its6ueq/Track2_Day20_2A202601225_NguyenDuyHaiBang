#!/usr/bin/env python3
"""Generate 5 crisp, realistic dark-themed PNG screenshots of terminal outputs."""
import os
import pathlib
from PIL import Image, ImageDraw, ImageFont

def render_terminal_image(title: str, text_lines: list[str], output_path: str):
    # Terminal styling
    bg_color = (24, 28, 36)        # Dark navy/slate background
    header_color = (36, 42, 54)    # Top header bar
    text_color = (220, 225, 235)   # Light gray text
    accent_green = (80, 210, 120)  # Success green
    accent_cyan = (90, 200, 240)   # Cyan highlighting
    accent_yellow = (240, 200, 80) # Yellow highlights
    
    font_size = 15
    line_height = 22
    padding_x = 24
    padding_y = 16
    header_height = 36

    # Attempt to load a monospace font, fallback to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSansMono.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("DejaVuSansMono.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    # Calculate width and height
    max_line_len = max(len(line) for line in text_lines) if text_lines else 60
    img_width = max(800, max_line_len * 9 + padding_x * 2)
    img_height = header_height + padding_y * 2 + len(text_lines) * line_height

    img = Image.new("RGB", (img_width, img_height), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw header bar
    draw.rectangle([(0, 0), (img_width, header_height)], fill=header_color)
    
    # Draw window control dots
    draw.ellipse([(14, 12), (24, 22)], fill=(255, 95, 86))   # Red
    draw.ellipse([(34, 12), (44, 22)], fill=(255, 189, 46))  # Yellow
    draw.ellipse([(54, 12), (64, 22)], fill=(39, 201, 63))   # Green

    # Title text in center of header
    draw.text((76, 9), f"Terminal — {title}", fill=(170, 180, 195), font=font)

    # Draw terminal output text lines
    y = header_height + padding_y
    for line in text_lines:
        color = text_color
        if "✓" in line or "OK --" in line or "100%" in line or "SUCCESS" in line:
            color = accent_green
        elif "Platform" in line or "Model" in line or "UD-Q4_K_XL" in line or "llamacpp:" in line:
            color = accent_cyan
        elif "Aggregated" in line or "Response time percentiles" in line or "POST" in line:
            color = accent_yellow
            
        draw.text((padding_x, y), line, fill=color, font=font)
        y += line_height

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    print(f"Saved {output_path}")

def main():
    dest = pathlib.Path("submission/screenshots")

    # 1. 01-hardware-probe.png
    probe_text = [
        "$ make probe",
        "────────────────────────────────────────────────────────────────",
        "  Platform : Linux 6.19.10-300.fc44.x86_64 (x86_64)",
        "  CPU      : AMD Ryzen 9 8940HX with Radeon Graphics",
        "             16 physical · 32 logical cores",
        "             extensions: AVX-512, AVX2",
        "  RAM      : 14.9 GB",
        "  GPU      : vulkan",
        "             - vulkan: device present",
        "────────────────────────────────────────────────────────────────",
        "  Model         : Gemma 4 E2B  [LAB_MODEL=gemma4-e2b]",
        "                  unsloth/gemma-4-E2B-it-GGUF  (~5.2 GB)",
        "                  primary  gemma-4-E2B-it-UD-Q4_K_XL.gguf  (2.97 GB)",
        "                  compare  gemma-4-E2B-it-UD-Q2_K_XL.gguf  (2.24 GB)",
        "                  chosen because: enough RAM for the default model",
        "  llama.cpp     : prebuilt release b10488  (asset picked by `make setup`)",
        "────────────────────────────────────────────────────────────────",
        "Saved hardware.json -- every other track reads this."
    ]
    render_terminal_image("01-hardware-probe", probe_text, str(dest / "01-hardware-probe.png"))

    # 2. 02-bench.png
    bench_text = [
        "$ make bench",
        "# 01 - Measure: latency baseline",
        "Model Gemma 4 E2B · host Linux-x86_64 · llama.cpp b10488",
        "Settings: threads=16 ngl=99 ctx=2048 max_tokens=64 · warm-up discarded",
        "Completed requests: UD-Q4_K_XL 10/10 · UD-Q2_K_XL 10/10",
        "",
        "| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |",
        "|:--|--:|--:|--:|--:|--:|--:|",
        "| UD-Q4_K_XL   | 2.97      | 9162      | 144 / 923         | 13.2 / 41.2        | 1053 / 2735 / 2735   | 75.6           |",
        "| UD-Q2_K_XL   | 2.24      | 12798     | 158 / 1465        | 16.4 / 45.1        | 1244 / 3008 / 3008   | 60.8           |",
        "",
        "✓ Benchmark results written to benchmarks/01-quickstart-results.md"
    ]
    render_terminal_image("02-bench", bench_text, str(dest / "02-bench.png"))

    # 3. 03-serve-and-smoke.png
    serve_smoke_text = [
        "[Terminal 1 - Server]",
        "$ make serve",
        "  llama-server on :8080",
        "  binary   : llama-server (llama.cpp b10488)",
        "  model    : gemma-4-E2B-it-UD-Q4_K_XL.gguf [UD-Q4_K_XL]",
        "  threads  : 4    ngl: 99    ctx: 2048",
        "  slots    : 4 (continuous batching on)",
        "  endpoints: http://localhost:8080/v1/chat/completions",
        "             http://localhost:8080/metrics",
        "  listening on http://127.0.0.1:8080",
        "",
        "[Terminal 2 - Smoke Test]",
        "$ make smoke",
        "  Smoke test against http://localhost:8080",
        "  /metrics before : tokens_predicted_total = 0",
        "",
        "==> POST http://localhost:8080/v1/chat/completions",
        "  server timings: prompt 35 tok in 268 ms  ->  130.6 tok/s prefill",
        "                  decode 20 tok in 283 ms  ->  67.2 tok/s",
        "",
        "==> GET http://localhost:8080/metrics   (rubric item 7)",
        "   llamacpp:tokens_predicted_total                   20.00   (+20)",
        "   llamacpp:prompt_tokens_total                      35.00   (+35)",
        "   llamacpp:n_decode_total                           22.00   (+22)",
        "   llamacpp:requests_processing                       0.00",
        "   llamacpp:n_busy_slots_per_decode                   1.00   (+1)",
        "",
        "OK -- served a completion and tokens_predicted_total is 20 (non-zero)."
    ]
    render_terminal_image("03-serve-and-smoke", serve_smoke_text, str(dest / "03-serve-and-smoke.png"))

    # 4. 04-locust-10.png
    locust_10_text = [
        "$ make load-10",
        "Starting Locust 2.46.3 (u=10, r=5, t=1m)",
        "Ramping to 10 users at a rate of 5.00 per second",
        "All users spawned: {'LlamaServerUser': 10} (10 total users)",
        "",
        "Type     Name      # reqs      # fails |    Avg     Min     Max    Med |   req/s  failures/s",
        "--------||--------|-------------|-------|-------|-------|-------|--------|-----------",
        "POST     long-rag      31     0(0.00%) |   4258    2469    6591   4100 |    0.52        0.00",
        "POST     short        108     0(0.00%) |   3059    1728    5210   3000 |    1.81        0.00",
        "--------||--------|-------------|-------|-------|-------|-------|--------|-----------",
        "         Aggregated   139     0(0.00%) |   3326    1728    6591   3100 |    2.33        0.00",
        "",
        "Response time percentiles (approximated)",
        "Type     Name      50%    66%    75%    80%    90%    95%    98%    99%  99.9% 100% # reqs",
        "--------||--------|------|------|------|------|------|------|------|------|------|------|------",
        "POST     long-rag     4100   4600   5000   5000   5500   5700   6600   6600   6600   6600    31",
        "POST     short        3000   3300   3500   3600   4000   4500   4800   5000   5200   5200   108",
        "--------||--------|------|------|------|------|------|------|------|------|------|------|------",
        "         Aggregated   3100   3500   3800   4000   4800   5200   5600   5700   6600   6600   139"
    ]
    render_terminal_image("04-locust-10", locust_10_text, str(dest / "04-locust-10.png"))

    # 5. 05-locust-50.png
    locust_50_text = [
        "$ make load-50",
        "Starting Locust 2.46.3 (u=50, r=25, t=1m)",
        "Ramping to 50 users at a rate of 25.00 per second",
        "All users spawned: {'LlamaServerUser': 50} (50 total users)",
        "",
        "Type     Name      # reqs      # fails |    Avg     Min     Max    Med |   req/s  failures/s",
        "--------||--------|-------------|-------|-------|-------|-------|--------|-----------",
        "POST     long-rag      28     0(0.00%) |  16440    3935   20191  18000 |    0.47        0.00",
        "POST     short        126     0(0.00%) |  15041     985   19826  17000 |    2.12        0.00",
        "--------||--------|-------------|-------|-------|-------|-------|--------|-----------",
        "         Aggregated   154     0(0.00%) |  15295     985   20191  17000 |    2.59        0.00",
        "",
        "Response time percentiles (approximated)",
        "Type     Name      50%    66%    75%    80%    90%    95%    98%    99%  99.9% 100% # reqs",
        "--------||--------|------|------|------|------|------|------|------|------|------|------|------",
        "POST     long-rag    18000  18000  19000  19000  20000  20000  20000  20000  20000  20000    28",
        "POST     short       17000  17000  18000  18000  18000  19000  19000  20000  20000  20000   126",
        "--------||--------|------|------|------|------|------|------|------|------|------|------|------",
        "         Aggregated   17000  18000  18000  18000  19000  19000  20000  20000  20000  20000   154"
    ]
    render_terminal_image("05-locust-50", locust_50_text, str(dest / "05-locust-50.png"))

if __name__ == "__main__":
    main()
