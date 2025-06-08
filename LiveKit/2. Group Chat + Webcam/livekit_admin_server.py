# server.py
import os, asyncio
from flask import Flask, request
from livekit import api
from dotenv import load_dotenv
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
load_dotenv()

@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS"
    return response


# This function returns a ready-to-use LiveKitAPI instance
def get_lkapi():
    return api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )

@app.route('/getToken')
def get_token():
    identity = request.args.get("identity", "guest")
    name = request.args.get("name", identity)

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

@app.route("/listParticipants")
def list_participants():
    async def inner():
        async with get_lkapi() as lkapi:
            res = await lkapi.room.list_participants(api.ListParticipantsRequest(room="my-room"))
            return [p.identity for p in res.participants]
    return asyncio.run(inner())

@app.route("/removeParticipant/<identity>")
def remove_participant(identity):
    async def inner():
        async with get_lkapi() as lkapi:
            await lkapi.room.remove_participant(api.RoomParticipantIdentity(
                room="my-room",
                identity=identity
            ))
            return f"Removed participant: {identity}"
    return asyncio.run(inner())

from flask import make_response

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
