import os, asyncio
from flask import Flask, request, make_response
from livekit import api
from dotenv import load_dotenv
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
load_dotenv()

# Helper to get LiveKitAPI
def get_lkapi():
    return api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )

@app.route('/getToken')
def get_token():
    identity = request.args.get("identity", "guest")
    name     = request.args.get("name", identity)

    token = api.AccessToken(
        os.getenv('LIVEKIT_API_KEY'),
        os.getenv('LIVEKIT_API_SECRET')
    ).with_identity(identity)\
     .with_name(name)\
     .with_grants(api.VideoGrants(
         room_join=True,
         room="my-room",
     ))

    return token.to_jwt()

@app.route("/muteTrack/<identity>/<track_sid>")
def mute_track(identity, track_sid):
    async def inner():
        async with get_lkapi() as lkapi:
            await lkapi.room.mute_published_track(api.MuteRoomTrackRequest(
                room="my-room",
                identity=identity,
                track_sid=track_sid,
                muted=True
            ))
            return f"Muted track {track_sid} of {identity}"

    result = asyncio.run(inner())
    response = make_response(result)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

if __name__ == "__main__":
    app.run(debug=True)
