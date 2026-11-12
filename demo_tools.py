from dotenv import load_dotenv
from anthropic import Anthropic
import json

load_dotenv()
client = Anthropic(max_retries=3)
model = "claude-sonnet-5-5"

tools = [{
    "name": "get_member_messages",
    "description": "Return all personalized messages for one member by numeric ID. "
                   "Use when the user asks about a specific member's messages.",
    "input_schema": {
        "type": "object",
        "properties": {"member_id": {"type": "integer", "description": "Numeric member ID"}},
        "required": ["member_id"],
    },
}]

FAKE_DB = {1: ["Happy birthday!", "Welcome back"], 2: []}

def get_member_messages(member_id):
    return FAKE_DB.get(member_id, [])

HANDLERS = {"get_member_messages": get_member_messages}

# messages = [{"role": "user", "content": "What messages does member 1 have?"}]
messages = [{"role": "user", "content": "What messages does Linh have?"}]

for _ in range(5):  # giới hạn số vòng, tránh lặp vô hạn
    resp = client.messages.create(model=model, max_tokens=1000, tools=tools, messages=messages)
    print("stop_reason:", resp.stop_reason)
    if resp.stop_reason != "tool_use":
        print("".join(b.text for b in resp.content if b.type == "text"))
        break
    messages.append({"role": "assistant", "content": resp.content})  # giữ nguyên, gồm cả thinking block
    results = []
    for b in resp.content:
        if b.type == "tool_use":
            print("model asks:", b.name, b.input)
            try:
                out = HANDLERS[b.name](**b.input)
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(out)})
            except Exception as e:
                results.append({"type": "tool_result", "tool_use_id": b.id,
                                "content": str(e), "is_error": True})
    messages.append({"role": "user", "content": results})
    print(resp.usage)