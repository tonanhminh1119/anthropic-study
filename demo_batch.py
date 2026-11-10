from dotenv import load_dotenv
from anthropic import Anthropic
import random
import string
import time

load_dotenv()
client = Anthropic(max_retries=3)
model = "claude-sonnet-5-5"
NUM_REQUESTS = 20
POLL_SECONDS = 30


def random_char(used_ids):
    """Chọn một chữ cái chưa dùng làm custom_id."""
    while True:
        c = random.choice(string.ascii_lowercase)
        if "req-" + c not in used_ids:
            return c


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def build_params(text, system=None, max_tokens=1000):
    messages = []
    add_user_message(messages, text)
    params = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system:
        params["system"] = system
    return params


def add_to_batch(batch, custom_id, text):
    batch.append({"custom_id": custom_id, "params": build_params(text)})


def wait_for_batch(batch_id):
    waited = 0
    while True:
        message_batch = client.messages.batches.retrieve(batch_id)
        if message_batch.processing_status == "ended":
            return message_batch
        print(f"Batch {batch_id} is {message_batch.processing_status} after {waited}s, still processing...")
        time.sleep(POLL_SECONDS)
        waited += POLL_SECONDS


def message_text(message):
    """Chỉ trả về text của message (không in gì)."""
    text = "".join(b.text for b in message.content if b.type == "text")
    if not text:
        print(f"warning: no text block, stop={message.stop_reason}")
    return text


def run_batch(batch):
    message_batch = client.messages.batches.create(requests=batch)
    wait_for_batch(message_batch.id)

    for entry in client.messages.batches.results(message_batch.id):
        if entry.result.type == "succeeded":
            msg = entry.result.message
            u = msg.usage
            print(f"{entry.custom_id}: in={u.input_tokens} out={u.output_tokens}")
            print(message_text(msg))
        else:
            print(f"{entry.custom_id}: {entry.result.type}")


def main():
    batch = []
    used_ids = []
    for _ in range(NUM_REQUESTS):
        c = random_char(used_ids)
        custom_id = "req-" + c
        used_ids.append(custom_id)
        add_to_batch(batch, custom_id, "Create one word starting with this character: " + c)
    print(used_ids)
    run_batch(batch)


if __name__ == "__main__":
    main()
