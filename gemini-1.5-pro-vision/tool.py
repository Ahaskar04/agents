import os 
from google import genai
from google.genai import types

# STEP 1: Authenticate with your Gemini API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyBs5PMuwcBY5-M8dk7L5mR_GRicZEVWX0k"

# STEP 2: Initialize the client
client = genai.Client()

# STEP 3: Read image bytes
with open('random.jpg', 'rb') as f:
    image_bytes = f.read()

# STEP 4: Make a request to Gemini with the image + prompt
response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[
        types.Part.from_bytes(
            data=image_bytes,
            mime_type='image/jpeg',
        ),
        'List all objects in this image and describe their spatial relationships.'
    ]
)

# STEP 5: Print the result
print(response.text)
