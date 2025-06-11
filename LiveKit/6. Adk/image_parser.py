from flask import Flask, request, jsonify
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# Allowed MIME types
SUPPORTED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif"
}

def vision_parse(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Parses a physics image and returns combined text + diagram description.

    Args:
        image_bytes (bytes): Image file as raw bytes.
        mime_type (str): MIME type of the image (e.g., image/jpeg, image/png)

    Returns:
        str: Extracted problem + diagram description (or error message if unsupported)
    """

    # ✅ Reject unsupported formats
    if mime_type not in SUPPORTED_MIME_TYPES:
        return f"❌ Unsupported file type: {mime_type}. Supported types are: {', '.join(SUPPORTED_MIME_TYPES)}"

    # Initialize client
    client = genai.Client()

    # Send request to Gemini
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            """
            This is an image of a physics problem. Please do the following:

            1. Extract all visible **text** from the image, including formulas, vector notations, units, and special symbols (like i-hat, j-hat, etc.).
            2. If the image includes a **diagram**, describe it in detail. Mention objects, coordinate systems, vectors, labels, angles, or arrows as appropriate.
            3. Combine the extracted text and diagram description to reconstruct a **clear and complete physics problem**, as if you were writing it for a textbook.

            ⚠️ Do **not** solve the problem. Only present the question and diagram description.
            """
        ]
    )
    print(response.text)
    return response.text

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    try:
        # Get image data from request
        data = request.get_json()
        
        # Decode base64 image
        image_data = base64.b64decode(data['image'])
        mime_type = data.get('mime_type', 'image/jpeg')
        
        # Use your existing function
        result = vision_parse(image_data, mime_type)
        
        return jsonify({
            'success': True,
            'description': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)