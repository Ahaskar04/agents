# 📸 Image Input Strategy for AI Agent (Gemini Vision)

This agent takes a user-uploaded image (e.g. a physics question), extracts text from it, and sends the extracted text to other downstream agents. This README explains how to handle image input efficiently using the Gemini API.

---

## ✅ TL;DR – What Should You Use?

| Your Situation                                          | Best Choice                     |
| ------------------------------------------------------- | ------------------------------- |
| 🔁 Image used **once** in a tool call                   | **Pass inline**                 |
| 🔁 Image reused across multiple agents/tools or prompts | **Use Artifact** (Google ADK)   |
| ⏫ Image is **large** (file + prompt > 20MB)            | **Upload via Gemini Files API** |

---

## ✅ Current Setup (Best Practice)

Since the image is used **once** and only by **one tool**, we use **inline image passing** with `Part.from_bytes()`.

```python
from google import genai
from google.genai import types

client = genai.Client(api_key="YOUR_API_KEY")

# Read image as bytes
with open('path/to/image.jpg', 'rb') as f:
    image_bytes = f.read()

# Call Gemini with inline image + prompt
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[
        types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg"
        ),
        "Convert this image (possibly a physics problem) into plain text and describe any diagram present."
    ]
)

print(response.text)
```
