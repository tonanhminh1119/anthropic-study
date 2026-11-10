"""Đo realtime: 20 request tuần tự giống demo_batch.py (cùng model, cùng prompt).

Chạy:  python bench_realtime.py
"""
from dotenv import load_dotenv
from anthropic import Anthropic
import statistics
import string
import sys
import time

from bench_models import cost_usd

load_dotenv()
client = Anthropic(max_retries=3)
model = "claude-sonnet-5-5"
NUM_REQUESTS = 20


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # console Windows mặc định không in được tiếng Việt
    latencies, total_cost = [], 0.0
    t0 = time.perf_counter()
    for c in string.ascii_lowercase[:NUM_REQUESTS]:
        start = time.perf_counter()
        msg = client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[{"role": "user",
                       "content": "Create one word starting with this character: " + c}],
        )
        latencies.append(time.perf_counter() - start)
        total_cost += cost_usd(model, msg.usage)
    total = time.perf_counter() - t0
    print(f"{NUM_REQUESTS} request tuần tự: tổng {total:.1f}s")
    print(f"mỗi request: median {statistics.median(latencies):.2f}s, "
          f"min {min(latencies):.2f}s, max {max(latencies):.2f}s")
    print(f"chi phí 20 request: ${total_cost:.4f}")


if __name__ == "__main__":
    main()
