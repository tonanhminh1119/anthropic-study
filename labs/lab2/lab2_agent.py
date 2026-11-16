from dotenv import load_dotenv
from anthropic import Anthropic
import json
import os
import jsonschema
import re
import sys

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
client = Anthropic(max_retries=3)
model = "claude-sonnet-5-5"

tools = {}
with open(os.path.join(BASE_DIR, 'tools.json'), 'r', encoding='utf-8' ) as file:
    tools = json.load(file)


SCHEMAS = {t["name"]: t["input_schema"] for t in tools}
FAKE_DB = {}
# read JSON file and parse contents
with open(os.path.join(BASE_DIR, 'sample_data.json'), 'r', encoding='utf-8' ) as file:
    FAKE_DB = json.load(file)

def _find_member(member_id):
    for m in FAKE_DB:
        if m["id"] == member_id:
            return m
    raise ValueError(
        f"No member with id {member_id}. "
        "Use find_member_by_name to look up the correct id."
    )

def find_member_by_name(name):
    # Chỉ trả id và name: tin nhắn lấy riêng bằng get_member_messages (mỗi tool một việc)
    for m in FAKE_DB:
        if m["name"] == name:
            return {"id": m["id"], "name": m["name"]}
    raise ValueError(f"No member named '{name}'. Check the spelling or ask the user.")


def get_member_messages(member_id, event_type = None):
    messages = _find_member(member_id)["messages"]
    if event_type:
        messages = [x for x in messages if x["type"] == event_type]
    return messages

def delete_message(member_id, message_id):
    member = _find_member(member_id)
    before = len(member["messages"])
    member["messages"] = [x for x in member["messages"] if x["id"] != message_id]
    if len(member["messages"]) == before:
        raise ValueError(
            f"Message {message_id} does not belong to member {member_id}. Nothing was deleted."
        )
    return {"deleted": True, "member_id": member_id, "message_id": message_id}

HANDLERS = {
    "get_member_messages": get_member_messages,
    "find_member_by_name": find_member_by_name,
    "delete_message": delete_message
}
MAX_ROUNDS, TOKEN_BUDGET = 5, 20000
STOP_PREFIX = "(dừng:"   # run_agent trả chuỗi bắt đầu bằng tiền tố này khi bị cắt
CONFIRM = None           # None = hỏi người dùng bằng input(); "y"/"n" = tự trả lời (để chạy kịch bản)

SYSTEM_PROMPT = """You manage members' messages using the provided tools.
Never guess ids: look them up with the tools. Delete a message only when the user explicitly asks.
When you are finished, reply with ONLY a JSON object (no markdown, no extra text):
{"deleted": <true|false>, "message_id": <integer or null>, "summary": "<one short sentence>"}
Set "deleted" to true only if delete_message succeeded."""

def ask_user(question):
    if CONFIRM is None:
        return input(question + " (y/n) ")
    print(f"{question} (y/n) {CONFIRM}   [auto]")
    return CONFIRM

SIDE_EFFECT_TOOLS = {"delete_message"}   # tool làm thay đổi dữ liệu, không rút lại được

def stopped(reason, done):
    # Thông báo dừng kèm các hành động đã thực thi, để người gọi biết việc gì đã xảy ra
    extra = f"; đã thực thi: {', '.join(done)}" if done else ""
    return f"{STOP_PREFIX} {reason}{extra})"

def run_agent(prompt, messages=None, max_rounds=MAX_ROUNDS):
    used = 0
    done = []   # các lệnh có tác dụng phụ đã chạy thành công trong lần gọi này
    messages = messages if messages is not None else []
    messages.append({"role": "user", "content": prompt})
    for rnd in range(1, max_rounds + 1):
        resp = client.messages.create(model=model, max_tokens=4096, system=SYSTEM_PROMPT,
                                      tools=tools, messages=messages)
        used += resp.usage.input_tokens + resp.usage.output_tokens
        print(f"[round {rnd}] stop={resp.stop_reason} tokens={used}")      # trace
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                res = execute_tool(b)
                results.append(res)
                if b.name in SIDE_EFFECT_TOOLS and not res.get("is_error"):
                    done.append(f"{b.name}({json.dumps(b.input, ensure_ascii=False)})")
        messages.append({"role": "user", "content": results})
        if used > TOKEN_BUDGET:
            return stopped(f"vượt ngân sách {TOKEN_BUDGET} token", done)
    return stopped(f"hết {max_rounds} vòng", done)

def execute_tool(b):
    res = _run_tool(b)
    status = "ERR" if res.get("is_error") else "ok"
    print(f"  tool={b.name} input={b.input} -> {status}")
    return res

def _run_tool(b):
    if b.name not in SCHEMAS:
        return {"type": "tool_result", "tool_use_id": b.id, 
                "content": f"Unknown tool '{b.name}'", "is_error": True}
    try:
        jsonschema.validate(b.input, SCHEMAS[b.name])
    except jsonschema.ValidationError as e:
        return {"type": "tool_result", "tool_use_id": b.id, 
                "content": f"Invalid input: {e.message}", "is_error": True}
    if  b.name == "delete_message":
        ans = ask_user(f"Xóa message {b.input.get('message_id')} của member {b.input.get('member_id')}?")
        if ans.strip().lower() != "y":
            return {"type": "tool_result", "tool_use_id": b.id,
                    "content": "User declined", "is_error": True}
    try:
        out = HANDLERS[b.name](**b.input)
        return {"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(out)}
    except Exception as e:
        return {"type": "tool_result", "tool_use_id": b.id,
                        "content": str(e), "is_error": True}

FINAL_SCHEMA = {
    "type": "object",
    "properties": {
        "deleted": {"type": "boolean"},
        "message_id": {"type": ["integer", "null"]},
        "summary": {"type": "string"},
    },
    "required": ["deleted", "message_id", "summary"],
    "additionalProperties": False,
}

def strip_fence(text):
    # model hay bọc JSON trong ```json ... ```
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())

def parse_final(text):
    data = json.loads(strip_fence(text))     # có thể ném JSONDecodeError
    jsonschema.validate(data, FINAL_SCHEMA)  # có thể ném ValidationError
    return data

def run_with_validation(prompt, history, max_rounds=MAX_ROUNDS):
    text = run_agent(prompt, history, max_rounds)
    for attempt in (1, 2):
        if text.startswith(STOP_PREFIX):
            return text                      # agent bị cắt: không phải lỗi định dạng, không sửa
        try:
            return parse_final(text)
        except (json.JSONDecodeError, jsonschema.ValidationError) as e:
            print(f"[validate] lần {attempt} không hợp lệ: {e}")
            if attempt == 2:
                return f"(output không hợp lệ sau 1 lần sửa: {e})"
            text = run_agent(f"Your final answer was invalid: {e}. "
                             "Reply with ONLY the JSON object, nothing else.", history, max_rounds)


# (câu hỏi, câu trả lời HITL tự động, số vòng tối đa)
SCENARIOS = {
    "A": ("Xoá tin nhắn welcome của Linh", "y", MAX_ROUNDS),   # xác nhận -> xoá đúng một tin
    "B": ("Xoá tin nhắn welcome của Linh", "n", MAX_ROUNDS),   # từ chối -> không xoá, agent báo lại
    "C": ("Xoá tin nhắn welcome của Zed", None, MAX_ROUNDS),   # member không tồn tại -> không bịa ID
    "D": ("Xoá tin nhắn welcome của Linh", "y", 2),            # MAX_ROUNDS=2 -> dừng sạch
}

def linh_state():
    return [(x["id"], x["type"]) for x in get_member_messages(find_member_by_name("Linh")["id"])]

def run_scenario(key):
    global CONFIRM, FAKE_DB
    prompt, answer, rounds = SCENARIOS[key]
    with open(os.path.join(BASE_DIR, 'sample_data.json'), 'r', encoding='utf-8') as f:   # DB sạch cho mỗi kịch bản
        FAKE_DB = json.load(f)
    CONFIRM = answer
    print("=" * 20, f"Scenario {key}: {prompt} | confirm={answer} | max_rounds={rounds}")
    print("Linh before:", linh_state())
    result = run_with_validation(prompt, [], max_rounds=rounds)
    print("RESULT:", json.dumps(result, ensure_ascii=False))
    print("Linh after: ", linh_state())

if __name__ == "__main__":
    # py lab2_agent.py        -> chạy A, B, C, D
    # py lab2_agent.py A      -> chỉ chạy kịch bản A (có thể: A C ...)
    for k in [a.upper() for a in sys.argv[1:]] or list(SCENARIOS):
        run_scenario(k)
