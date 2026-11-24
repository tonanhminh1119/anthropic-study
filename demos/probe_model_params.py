"""Thử xem claude-haiku-5-5 chấp nhận tham số nào (xem notes W4D2 mục 7 và 30).

Gửi 4 request nhỏ: bình thường, temperature=1.0, temperature=0.5, và prefill kèm
stop_sequences. In ra OK hoặc mã lỗi cùng thông báo đầy đủ của API.
Tốn vài phần trăm cent. Chạy từ thư mục gốc: python demos/probe_model_params.py

Lưu ý: SDK anthropic 2.x không còn tham số `temperature` trong Messages.create(),
nên gửi qua extra_body để thử phía API.
"""
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(max_retries=0)

MODEL = "claude-haiku-5-5"
base = dict(model=MODEL, max_tokens=50)
user = {"role": "user", "content": 'Return JSON {"a":1}'}

tests = {
    "plain": dict(messages=[user]),
    "temperature=1.0": dict(messages=[user], extra_body={"temperature": 1.0}),
    "temperature=0.5": dict(messages=[user], extra_body={"temperature": 0.5}),
    "prefill+stop": dict(
        messages=[user, {"role": "assistant", "content": "```json"}],
        stop_sequences=["```"],
    ),
}

for name, kwargs in tests.items():
    try:
        r = client.messages.create(**base, **kwargs)
        print(name, "OK", repr(r.content[0].text[:40]))
    except anthropic.APIStatusError as e:
        print(name, e.status_code, e.message)
