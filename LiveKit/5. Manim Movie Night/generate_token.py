# generate_token.py
"""
Generate a LiveKit token for testing
"""

import os
from dotenv import load_dotenv
from livekit import api

load_dotenv()

def generate_token():
    """Generate a token for LiveKit Meet testing."""
    
    # Get credentials from .env
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    server_url = os.getenv("LIVEKIT_URL")
    
    if not all([api_key, api_secret, server_url]):
        print("❌ Missing LiveKit credentials in .env file:")
        print("   LIVEKIT_API_KEY")
        print("   LIVEKIT_API_SECRET") 
        print("   LIVEKIT_URL")
        return
    
    print("🔑 Generating LiveKit token...")
    print(f"🌐 Server: {server_url}")
    
    # Room and participant details
    room_name = "audio-test"
    participant_name = "test-user"
    
    # Create token
    token = api.AccessToken(api_key, api_secret) \
        .with_identity(participant_name) \
        .with_name(participant_name) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        )).to_jwt()
    
    print(f"\n✅ TOKEN GENERATED:")
    print("="*80)
    print(token)
    print("="*80)
    
    print(f"\n📋 COPY THIS INFO TO LIVEKIT MEET:")
    print(f"Server URL: {server_url}")
    print(f"Room Name: {room_name}")
    print(f"Token: {token}")
    
    print(f"\n🎯 OR USE THIS DIRECT URL:")
    # Note: This might not work directly but shows the format
    print(f"https://meet.livekit.io/custom?liveKitUrl={server_url}&token={token}")

if __name__ == "__main__":
    generate_token()