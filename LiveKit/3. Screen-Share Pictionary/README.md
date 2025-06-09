# 🎨 Screen-Share Pictionary with LiveKit

This project demonstrates a **real-time Pictionary app** using [LiveKit](https://livekit.io). It allows one user to **screen-share a drawing canvas**, while others view the shared screen and receive live **drawing strokes via DataTrack**.

---

## ✅ Features

- 🔗 Connect to a LiveKit room with dynamic JWT token
- 🖥️ Screen-sharing using `createLocalScreenTracks()`
- 🎥 Remote participants auto-subscribe to shared screen
- ✍️ Real-time canvas drawing synced across participants using DataTrack
- 🧠 Track mute/unmute with server-side API
- 💬 Optional chat support using `sendText()` (reused from previous project)

---

## 🧠 Concepts Covered

### 1. `createLocalScreenTracks()`

LiveKit helper to capture your screen as a video track.

```ts
import { createLocalScreenTracks } from "livekit-client";

const tracks = await createLocalScreenTracks({ audio: false });
await room.localParticipant.publishTrack(tracks[0]);
```

Returns:

- A `LocalVideoTrack` for screen
- Optionally a `LocalAudioTrack` (if enabled & supported)

---

### 2. `RoomEvent.TrackSubscribed`

Used to detect when a remote participant subscribes to a shared track (e.g., screen).

```ts
room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
  if (track.kind === Track.Kind.Video) {
    const el = track.attach();
    remoteContainer.appendChild(el);
  }
});
```

---

### 3. Drawing with Canvas

Mouse/touch events on a `<canvas>` are used to draw lines locally and transmit them to others.

```js
canvas.addEventListener("mousedown", startDraw);
canvas.addEventListener("mousemove", draw);
```

---

### 4. Real-time Stroke Sync via DataTrack

We encode each stroke as a JSON message and send it through LiveKit's DataTrack:

```js
const data = JSON.stringify({ x0, y0, x1, y1, color });
room.localParticipant.publishData(data, DataPacket_Kind.RELIABLE);
```

Remote participants receive and draw it on their own canvas:

```js
room.on(RoomEvent.DataReceived, ({ payload }) => {
  const stroke = JSON.parse(new TextDecoder().decode(payload));
  drawStrokeRemotely(stroke);
});
```

---

## 🛠️ Setup Instructions

1. Clone the repo
2. Run the backend LiveKit token server (`livekit_admin_server.py`)
3. Start a local server for the frontend (e.g. using Live Server / Python)
4. Open in multiple tabs/browsers and start drawing!

---

## 🧪 What You’ll Learn

| Concept                     | Usage                                        |
| --------------------------- | -------------------------------------------- |
| `createLocalScreenTracks()` | Screen capture and sharing                   |
| Canvas drawing              | Mouse tracking and rendering strokes         |
| DataTrack with JSON payload | Real-time communication between participants |
| `RoomEvent.TrackSubscribed` | Detect and attach remote screen video        |
| `RoomEvent.DataReceived`    | Parse and render incoming drawing data       |

---

## 📸 Screenshot

![Pictionary Screenshot](screenshot.png) <!-- Add if available -->

---

## 📚 Resources

- [LiveKit Docs – Screen Sharing](https://docs.livekit.io/client-sdk-js/media/devices/#screen-sharing)
- [LiveKit Docs – DataTracks](https://docs.livekit.io/realtime-text-data/datatracks/)
- [Canvas Drawing Basics (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial)
