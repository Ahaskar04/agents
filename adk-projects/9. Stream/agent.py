import litellm

model = "ollama_chat/qwen3:4b"  # swap this later

response = litellm.completion(
    model=model,
    messages=[{"role": "user", "content": "Write a short poem about the moon"}],
    stream=True
)

for chunk in response:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)