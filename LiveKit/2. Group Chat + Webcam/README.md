# Group Chat + Webcam Demo

A LiveKit-powered demo that lets multiple users:

- Join a room with video + audio
- Auto-subscribe to each other’s camera feeds
- Mute each other’s tracks via a backend REST call
- Chat in real-time using LiveKit Text Streams

---

## 🚀 Prerequisites

1. **LiveKit Cloud project** — get your WS URL, API Key & Secret
2. **Backend**
   ```bash
   pip install flask python-dotenv livekit-api flask-cors
   ```

````

3. **Frontend**

   ```bash
   npm install livekit-client
   ```

4. Create a `.env` at your backend root:

   ```ini
   LIVEKIT_URL=https://<your-project>.livekit.cloud
   LIVEKIT_API_KEY=<your-key>
   LIVEKIT_API_SECRET=<your-secret>
   ```

---

## 📡 Backend: `server.py`

```python
import os, asyncio
from flask import Flask, request
from flask_cors import CORS
from livekit import api
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)

def get_lkapi():
    return api.LiveKitAPI(
        url=os.getenv("LIVEKIT_URL"),
        key=os.getenv("LIVEKIT_API_KEY"),
        secret=os.getenv("LIVEKIT_API_SECRET")
    )

@app.route('/getToken')
def get_token():
    identity = request.args.get("identity", "guest")
    name     = request.args.get("name", identity)
    token = api.AccessToken(
        os.getenv("LIVEKIT_API_KEY"),
        os.getenv("LIVEKIT_API_SECRET")
    ).with_identity(identity)\
     .with_name(name)\
     .with_grants(api.VideoGrants(room_join=True, room="my-room"))
    return token.to_jwt()

@app.route('/muteTrack/<identity>/<track_sid>')
def mute_track(identity, track_sid):
    async def inner():
        async with get_lkapi() as lkapi:
            await lkapi.room.mute_published_track(
                api.MuteRoomTrackRequest(
                    room="my-room",
                    identity=identity,
                    track_sid=track_sid,
                    muted=True
                )
            )
            return f"Muted {track_sid} of {identity}"
    return asyncio.run(inner())

if __name__ == '__main__':
    app.run(debug=True)
```

---

## 🎨 Frontend

### `index.html`

```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Group Chat + Webcam</title>
    <style>
      #remoteVideos {
        display: flex;
        gap: 8px;
        margin: 10px 0;
      }
      .message {
        margin: 4px 0;
      }
      .sender {
        font-weight: bold;
      }
    </style>
  </head>
  <body>
    <h1>LiveKit Group Chat + Webcam</h1>
    <label>Identity: <input id="identityInput" placeholder="alice" /></label>
    <label>Name: <input id="nameInput" placeholder="Alice" /></label>
    <button id="joinBtn">Join Room</button>
    <button id="muteBtn">Mute My Mic</button>
    <div id="remoteVideos"></div>
    <video
      id="localVideo"
      autoplay
      muted
      playsinline
      style="width:300px;border:1px solid #ccc;"
    ></video>
    <div
      id="chatContainer"
      style="height:200px;overflow-y:auto;border:1px solid #ccc;padding:8px;"
    ></div>
    <input id="chatInput" placeholder="Type a message…" style="width:300px;" />
    <button id="sendBtn">Send</button>
    <script type="module" src="app.jsx"></script>
  </body>
</html>
```

### `app.jsx`

```js
import { Room, RoomEvent, Track } from "livekit-client";

const wsUrl = "wss://<your-project>.livekit.cloud";

let room, micTrackSid, identity;

// Append chat message to DOM
function appendMessage(sender, text) {
  const c = document.getElementById("chatContainer");
  const d = document.createElement("div");
  d.className = "message";
  d.innerHTML = `<span class="sender">${sender}:</span> ${text}`;
  c.appendChild(d);
  c.scrollTop = c.scrollHeight;
}

document.getElementById("joinBtn").onclick = async () => {
  identity = document.getElementById("identityInput").value || "guest";
  const name = document.getElementById("nameInput").value || identity;

  // 1) Fetch a dynamic token
  const token = await fetch(
    `http://localhost:5000/getToken?identity=${identity}&name=${name}`
  ).then((r) => r.text());

  // 2) Instantiate and connect
  room = new Room();
  await room.connect(wsUrl, token);
  console.log("✅ Connected as", identity);

  // 3) Subscribe to remote video
  room.on(RoomEvent.TrackSubscribed, (track, _, participant) => {
    if (track.kind === Track.Kind.Video) {
      const el = track.attach();
      el.style.width = "200px";
      document.getElementById("remoteVideos").appendChild(el);
    }
  });

  // 4) Register chat handler on Room
  room.registerTextStreamHandler("chat", async (reader, info) => {
    const msg = await reader.readAll();
    appendMessage(info.identity, msg);
  });

  // 5) Publish camera & mic
  await room.localParticipant.setCameraEnabled(true);
  await room.localParticipant.setMicrophoneEnabled(true);

  // Attach local video
  const camPub = room.localParticipant.getTrackPublication("camera");
  const camTrack = camPub?.videoTrack;
  if (camTrack) {
    const el = camTrack.attach();
    document.getElementById("localVideo").replaceWith(el);
    el.id = "localVideo";
  }

  // Store mic track SID
  micTrackSid =
    room.localParticipant.getTrackPublication("microphone")?.trackSid;

  appendMessage("System", `${identity} joined the room`);
};

document.getElementById("sendBtn").onclick = async () => {
  const input = document.getElementById("chatInput");
  const msg = input.value.trim();
  if (!msg || !room) return;
  await room.localParticipant.sendText(msg, { topic: "chat" });
  appendMessage(identity, msg);
  input.value = "";
};

document.getElementById("muteBtn").onclick = async () => {
  if (!micTrackSid || !identity) return;
  const res = await fetch(
    `http://localhost:5000/muteTrack/${identity}/${micTrackSid}`
  );
  console.log("🔇", await res.text());
};
```

---

## 🔑 What is `trackSid`?

- A **unique string** LiveKit assigns to _each_ published track (camera/mic, per join).
- Even the same user rejoining gets a _new_ `trackSid`.
- You need it to remotely mute/unmute via the admin API.

---

## 🔍 Publication vs Track

```
┌───────────────────────┐     ┌─────────────────────┐
│   TrackPublication    │ ──>│       Track         │
│  (metadata only)      │     │ (actual media data) │
└───────────────────────┘     └─────────────────────┘
```

- **Publication** = metadata (SID, kind, source, permissions)
- **Track** = live audio/video frames, `.attach()` to render

---

## 🔄 Subscription Flow

1. **Upon connect** you get every `TrackPublication` in the room.
2. **Auto-subscribe** by default or call `participant.setTrackSubscription(...)`.
3. **`TrackSubscribed` event** fires when frames arrive.
4. Call **`track.attach()`** to bind into your HTML.

---

## 💬 Text Streaming (Chat)

- **Fire-and-forget**:

  ```js
  room.localParticipant.sendText("Hello!", { topic: "chat" });
  ```

- **Register handler** on the **Room**:

  ```js
  room.registerTextStreamHandler("chat", async (reader, info) => {
    const msg = await reader.readAll();
    console.log(info.identity, msg);
  });
  ```

- Streams are **real-time only**—no built-in history or persistence.

---

## ▶️ Running the Demo

1. **Start backend**

   ```bash
   python server.py
   ```

2. **Install frontend**

   ```bash
   npm install livekit-client
   ```

3. **Serve** `index.html` from a local server (e.g. `npx serve .`)
4. **Open two browsers** (or incognito) at your frontend URL
5. **Join** as different identities—see each other’s video + chat!
````
