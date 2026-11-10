from dotenv import load_dotenv
from anthropic import Anthropic
import random
import string
import time

load_dotenv()
client = Anthropic(max_retries=3)
model = "claude-sonnet-5-5"

def randomChar(batchIds):
    allowed_characters = string.ascii_letters
    while True:
        random_string = ''.join(random.choices(allowed_characters, k=1)).lower()
        if("req-" + random_string not in batchIds):
            return random_string

def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})

def add_user_message_to_request(text, system=None, max_tokens=1000):
    messages = []
    add_user_message(messages, text)
    params = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system:
        params["system"] = system
    return params

def add_user_message_to_batch(batch, batchID, text):
    params = add_user_message_to_request(text)
    batch.append({"custom_id" : batchID, "params":params})

def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})

def chat(batch):
    message_batch = client.messages.batches.create(requests= batch)
    initSeconds = 0
    while True:
        message_batch = client.messages.batches.retrieve(message_batch.id)
        if message_batch.processing_status == "ended":
            break
        print(f"Batch {message_batch.id} is currently at {message_batch.processing_status} after {initSeconds} and still processing...")
        time.sleep(30)
        initSeconds += 30

    for entry in client.messages.batches.results(message_batch.id):
        if entry.result.type == "succeeded":
            print(f"{entry.custom_id}: {printContent(entry.result.message)}")
    

def printContent(message):
    u = message.usage
    cw = getattr(u, "cache_creation_input_tokens", 0) or 0
    cr = getattr(u, "cache_read_input_tokens", 0) or 0
    print(f"usage: in={u.input_tokens} cache_write={cw} cache_read={cr} "
        f"out={u.output_tokens} | total_in={u.input_tokens + cw + cr}")
    text = "".join(b.text for b in message.content if b.type == "text")
    if not text:
        print(f"warning: no text block, stop={message.stop_reason}")
    return text

batch = []
batchIds = []
for i in range(20):
    randomCharacter = randomChar(batchIds)
    prompt = "Create one word stating with this character: " + randomCharacter
    batchID = "req-" + randomCharacter
    batchIds.append(batchID)
    add_user_message_to_batch(batch, batchID, prompt)
print(batchIds)
chat(batch)