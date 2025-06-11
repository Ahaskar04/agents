# server.py
"""
Flask server for LiveKit Image Analysis
Handles:
1. Token generation for participants
2. Room creation and management
3. Image analysis via Google Gemini API
"""

import os
import base64
import random
import string
from flask import Flask, request, jsonify
from livekit import api
from dotenv import load_dotenv
from flask_cors import CORS
import logging
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app)
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allowed MIME types for images
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
    """
    if mime_type not in SUPPORTED_MIME_TYPES:
        return f"❌ Unsupported file type: {mime_type}. Supported types are: {', '.join(SUPPORTED_MIME_TYPES)}"

    try:
        # Pass the API key to the client
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return "❌ Error: GOOGLE_API_KEY not found in environment variables"
        
        client = genai.Client(api_key=api_key)
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
        return response.text
    except Exception as e:
        logger.error(f"Vision parsing error: {e}")
        return f"❌ Error analyzing image: {str(e)}"

def generate_room_name():
    """Generate a random room name"""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"physics-analysis-{suffix}"

@app.route('/getToken')
def get_token():
    """
    Generate a token for a participant to join a room.
    
    Query params:
    - identity: Unique identifier for the user
    - name: Display name for the user  
    - room: Room name to join
    
    Returns:
    JWT token as text
    """
    identity = request.args.get("identity", f"user-{random.randint(1000, 9999)}")
    name = request.args.get("name", identity)
    room = request.args.get("room", "default-room")
    
    logger.info(f"Generating token for {identity} to join room {room}")
    
    # Create access token with permissions
    token = api.AccessToken(
        os.getenv('LIVEKIT_API_KEY'),
        os.getenv('LIVEKIT_API_SECRET')
    ).with_identity(identity)\
     .with_name(name)\
     .with_grants(api.VideoGrants(
         room_join=True,
         room=room,
         can_subscribe=True,
         can_publish=True,
         can_publish_data=True  # Allow sending files and data
     ))
    
    return token.to_jwt()

@app.route('/createRoom', methods=['POST'])
def create_room():
    """
    Create a room for image analysis.
    
    Returns:
    JSON with room information
    """
    room_name = generate_room_name()
    
    logger.info(f"Creating analysis room: {room_name}")
    
    return jsonify({
        'success': True,
        'room': room_name,
        'message': f'Room {room_name} is ready for image analysis.'
    })

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    """
    Analyze an uploaded image using Google Gemini API.
    
    Body params:
    - image: Base64 encoded image data
    - mime_type: MIME type of the image
    - room: Room name (for logging)
    
    Returns:
    JSON with analysis result
    """
    try:
        data = request.get_json()
        
        # Decode base64 image
        image_data = base64.b64decode(data['image'])
        mime_type = data.get('mime_type', 'image/jpeg')
        room = data.get('room', 'unknown')
        
        logger.info(f"Analyzing image in room {room}, type: {mime_type}, size: {len(image_data)} bytes")
        
        # Use vision parsing function
        result = vision_parse(image_data, mime_type)
        
        return jsonify({
            'success': True,
            'description': result,
            'room': room
        })
        
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/rooms', methods=['GET'])
def list_rooms():
    """
    List active rooms (basic implementation)
    """
    # This is a simplified version - in production you'd query LiveKit API
    return jsonify({
        'success': True,
        'message': 'Rooms are created dynamically. Use /createRoom to create a new one.'
    })

@app.route('/')
def index():
    """Health check endpoint."""
    return jsonify({
        'status': 'running',
        'service': 'LiveKit Image Analysis Server',
        'endpoints': [
            '/getToken - Generate participant token',
            '/createRoom - Create an analysis room',
            '/analyze-image - Analyze uploaded image',
            '/rooms - List rooms'
        ]
    })

if __name__ == "__main__":
    # Check required environment variables
    required_vars = ['LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET', 'LIVEKIT_URL', 'GOOGLE_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")
        exit(1)
    
    logger.info("Starting LiveKit Image Analysis Server...")
    app.run(debug=True, port=5000)