from dotenv import load_dotenv
from anthropic import Anthropic, AsyncAnthropic
import asyncio
import base64
import mimetypes
import os
import sys

load_dotenv()
client = Anthropic(max_retries=3)
model = "claude-sonnet-5-5"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})

def add_user_message_with_media(messages, text, image_path):
    media_type, _ = mimetypes.guess_type(image_path)
    
    if not media_type:
        ext = os.path.splitext(image_path)[1].lower()
        if ext in ['.jpg', '.jpeg']: media_type = 'image/jpeg'
        elif ext == '.png': media_type = 'image/png'
        elif ext == '.gif': media_type = 'image/gif'
        elif ext == '.webp': media_type = 'image/webp'
        else:
            raise ValueError(f"Không hỗ trợ định dạng file này hoặc file không hợp lệ: {image_path}")


    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64_image,
                    },
                },
                {
                    "type": "text",
                    "text": text,
                },
            ],
        }
    )

def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})

def chat(messages, system=None, max_tokens=1000):
    params = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system:
        params["system"] = system
    message = client.messages.create(**params)
    u = message.usage
    cw = getattr(u, "cache_creation_input_tokens", 0) or 0
    cr = getattr(u, "cache_read_input_tokens", 0) or 0
    print(f"usage: in={u.input_tokens} cache_write={cw} cache_read={cr} "
        f"out={u.output_tokens} | total_in={u.input_tokens + cw + cr}")
    text = "".join(b.text for b in message.content if b.type == "text")
    if not text:
        print(f"warning: no text block, stop={message.stop_reason}")
    return text


async def streaming(messages, system=None, max_tokens=1000) -> str:
    params = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system:
        params["system"] = system

    chunks = []
    async with AsyncAnthropic(max_retries=3) as async_client:
        async with async_client.messages.stream(**params) as stream:
            async for text in stream.text_stream:
                print(text, end="", flush=True)
                chunks.append(text)
            message = await stream.get_final_message()
    print()  # xuống dòng trước khi in usage
    print(f"usage: in={message.usage.input_tokens} out={message.usage.output_tokens}"
          f" stop={message.stop_reason}")
    return "".join(chunks)


def demo_chat():
    """Hội thoại 2 lượt: tự giữ lịch sử messages."""
    messages = []
    add_user_message(messages, "What is claude? Answer in one sentence")
    answer1 = chat(messages)
    print(answer1)
    add_assistant_message(messages, answer1)
    add_user_message(messages, "What is claude? Write another sentence")
    print(chat(messages))


def demo_image(image_path=None):
    """Gửi ảnh kèm câu hỏi. Dùng: python demo.py image <đường_dẫn_ảnh>"""
    if not image_path:
        sys.exit("Thiếu đường dẫn ảnh: python demo.py image <đường_dẫn_ảnh>")
    messages = []
    add_user_message_with_media(
        messages, "Describe the contents of this image? Answer in one sentence", image_path)
    print(chat(messages))


def demo_streaming():
    """In câu trả lời theo từng đoạn."""
    messages = []
    add_user_message(messages, "What is claude? Answer in one sentence")
    asyncio.run(streaming(messages))


def demo_caching():
    """Prompt caching: system prompt dài được cache, lượt 2 sẽ có cache_read."""
    with open(os.path.join(BASE_DIR, "archive", "Building with the Claude API.txt"), encoding="utf-8") as f:
        long_text = f.read()
    system = [{
        "type": "text",
        "text": long_text,
        "cache_control": {"type": "ephemeral"},
    }]
    messages = []
    add_user_message(messages, "What is claude? Answer in one sentence")
    answer1 = chat(messages, system=system)
    print(answer1)
    add_assistant_message(messages, answer1)
    add_user_message(messages, "What is claude? Write another sentence")
    print(chat(messages, system=system))


DEMOS = {
    "chat": demo_chat,
    "image": demo_image,
    "streaming": demo_streaming,
    "caching": demo_caching,
}

if __name__ == "__main__":
    name, *extra = sys.argv[1:] or [None]
    if name:
        DEMOS[name](*extra)
    else:
        for name, fn in DEMOS.items():
            if name == "image":
                continue  # cần đường dẫn ảnh, chạy riêng
            print(f"\n=== {name} ===")
            fn()
