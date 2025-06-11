# server.py
"""
Flask server for Movie Night
Handles:
1. Token generation for participants
2. Room creation and management
3. Starting movie sessions
"""

import os
import asyncio
from flask import Flask, request, jsonify, make_response
from livekit import api
from dotenv import load_dotenv
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper to get LiveKitAPI instance
def get_lkapi():
    """Create a LiveKit API client with credentials from environment."""
    return api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )


@app.route('/getToken')
def get_token():
    """
    Generate a token for a participant to join a room.
    
    Query params:
    - identity: Unique identifier for the user
    - name: Display name for the user
    - room: Room name to join (defaults to "my-room")
    
    Returns:
    JWT token as text
    """
    identity = request.args.get("identity", "guest")
    name = request.args.get("name", identity)
    room = request.args.get("room", "my-room")
    
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
         # Participants can subscribe but not publish
         # (only the agent publishes)
         can_subscribe=True,
         can_publish=False,
         can_publish_data=True  # Allow chat messages
     ))
    
    return token.to_jwt()


@app.route('/createMovieRoom', methods=['POST'])
def create_movie_room():
    """
    Create a room for a movie night session.
    
    Body params:
    - animation: Name of the animation (e.g., "projectile")
    
    Returns:
    JSON with room information
    """
    data = request.json or {}
    animation = data.get('animation', 'projectile')
    
    # Create room name
    room_name = f"movie-{animation}"
    
    logger.info(f"Creating movie room: {room_name}")
    
    # Rooms are auto-created in LiveKit Cloud when first participant joins
    # But we can set metadata or use the API to pre-create if needed
    
    # For LiveKit Cloud, rooms auto-create, so we just return the info
    # For self-hosted, you might want to use the RoomService API here
    
    return jsonify({
        'success': True,
        'room': room_name,
        'animation': animation,
        'message': f'Room {room_name} is ready. The agent will join when you connect.'
    })


@app.route('/startMovie', methods=['POST'])
async def start_movie():
    """
    Start the movie by ensuring the agent is assigned to the room.
    
    Body params:
    - room: Room name where movie should start
    
    Note: With LiveKit agents, the agent automatically joins when
    a room is created and matches the agent's configuration.
    """
    data = request.json or {}
    room_name = data.get('room', 'movie-projectile')
    
    logger.info(f"Starting movie in room: {room_name}")
    
    # With WorkerType.ROOM agents, they automatically join matching rooms
    # So we just need to ensure participants can join
    
    # You could add additional logic here like:
    # - Checking if video file exists
    # - Setting room metadata
    # - Sending notifications
    
    return jsonify({
        'success': True,
        'room': room_name,
        'message': 'Movie agent will join the room automatically'
    })


@app.route('/listRooms')
async def list_rooms():
    """
    List all active rooms (requires LiveKit server API).
    
    Returns:
    JSON array of room information
    """
    try:
        lkapi = get_lkapi()
        # Create room service client
        room_service = lkapi.room
        
        # List all rooms
        rooms = await room_service.list_rooms()
        
        room_list = []
        for room in rooms:
            room_list.append({
                'name': room.name,
                'participants': room.num_participants,
                'created': room.creation_time,
                'metadata': room.metadata
            })
        
        return jsonify({
            'success': True,
            'rooms': room_list
        })
        
    except Exception as e:
        logger.error(f"Error listing rooms: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/')
def index():
    """Health check endpoint."""
    return jsonify({
        'status': 'running',
        'service': 'Movie Night Server',
        'endpoints': [
            '/getToken - Generate participant token',
            '/createMovieRoom - Create a movie room',
            '/startMovie - Start movie in a room',
            '/listRooms - List active rooms'
        ]
    })


if __name__ == "__main__":
    # Run Flask server
    app.run(debug=True, port=5000)