"""Benchmark 4 model trên 3 prompt: đo latency, cost, chấm quality tự động.

Chạy:  python bench_models.py            (REPS=3 lần mỗi prompt/model)
Tốn tiền thật (rất nhỏ, vài cent). Kết quả in ra dạng bảng Markdown.
"""
from dotenv import load_dotenv
from anthropic import Anthropic
import json
import re
import statistics
import sys
import time

load_dotenv()
client = Anthropic(max_retries=3)

# Giá USD / 1M token (input, output). Nguồn: bảng giá Anthropic, kiểm tra lại khi dùng.
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-fable-5-1": (10.00, 50.00),
}
REPS = 3
MAX_TOKENS = 2000  # đủ chỗ cho thinking (tính vào output token)


def cost_usd(model, usage):
    p_in, p_out = PRICES[model]
    return (usage.input_tokens * p_in + usage.output_tokens * p_out) / 1_000_000


# --- Chấm điểm tự động: mỗi hàm trả về 0.0 hoặc 1.0 -------------------------

def grade_math(text):
    """Đúng nếu giờ HH:MM cuối cùng trong câu trả lời là 11:20 (cho phép có giải thích)."""
    times = re.findall(r"(?<!\d)\d{1,2}:\d{2}(?!\d)", text)
    return 1.0 if times and times[-1] == "11:20" else 0.0


def grade_json(text):
    try:
        data = json.loads(text.strip().removeprefix("```json").removesuffix("```").strip())
    except ValueError:
        return 0.0
    ok = (data.get("name") == "Linh Tran"
          and data.get("amount_usd") == 1249.5
          and data.get("date") == "2025-03-03")
    return 1.0 if ok else 0.0


def grade_bullets(text):
    lines = [l for l in text.strip().splitlines() if l.strip()]
    ok = len(lines) == 3 and all(
        l.startswith("- ") and len(l[2:].split()) <= 8 for l in lines)
    return 1.0 if ok else 0.0


PROMPTS = [
    ("math", "A train leaves at 09:40 and travels 150 km at 90 km/h. "
             "What time does it arrive? Answer in HH:MM only.", grade_math),
    ("json", "Extract JSON with keys name, amount_usd (number), date (YYYY-MM-DD) from: "
             "'On March 3rd, 2025, Linh Tran paid $1,249.50 for the invoice.' "
             "Return only the JSON.", grade_json),
    ("bullets", "Write exactly 3 bullet lines about the benefits of prompt caching. "
                "Each line starts with '- ' and has at most 8 words. No other text.",
     grade_bullets),
]


def run_once(model, prompt):
    start = time.perf_counter()
    msg = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        output_config={"effort": "low"},  # cùng mức effort cho mọi model
        messages=[{"role": "user", "content": prompt}],
    )
    latency = time.perf_counter() - start
    text = "".join(b.text for b in msg.content if b.type == "text")
    return text, latency, cost_usd(model, msg.usage)


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # console Windows mặc định không in được tiếng Việt
    print("| Model | Quality (0-1) | Latency median (s) | Cost / 1 request ($) |")
    print("|---|---|---|---|")
    for model in PRICES:
        scores, latencies, costs = [], [], []
        for _, prompt, grader in PROMPTS:
            for _ in range(REPS):
                text, latency, cost = run_once(model, prompt)
                scores.append(grader(text))
                latencies.append(latency)
                costs.append(cost)
        print(f"| {model} | {statistics.mean(scores):.2f} | "
              f"{statistics.median(latencies):.1f} | {statistics.mean(costs):.5f} |",
              flush=True)


if __name__ == "__main__":
    main()
