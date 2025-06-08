import { Room, RoomEvent, Track } from 'livekit-client';

// your LiveKit Cloud WebSocket URL
const wsUrl = "wss://solvd-x191iqhu.livekit.cloud";

let room = null;
let micTrackSid = null;
let identity = null;

// helper to append chat messages
function appendMessage(sender, text) {
  const container = document.getElementById("chatContainer");
  const div = document.createElement("div");
  div.className = "message";
  div.innerHTML = `<span class="sender">${sender}:</span> ${text}`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// JOIN ROOM + PUBLISH MEDIA + SETUP HANDLERS
document.getElementById("joinBtn").addEventListener("click", async () => {
  identity = document.getElementById("identityInput").value || "guest";
  const name = document.getElementById("nameInput").value || identity;

  try {
    // 1) fetch a dynamic token from your Python backend
    const tokenRes = await fetch(
      `http://localhost:5000/getToken?identity=${identity}&name=${name}`
    );
    const token = await tokenRes.text();

    // 2) instantiate the Room
    room = new Room();

    // 3) subscribe to remote video tracks
    room.on(RoomEvent.TrackSubscribed, (track, _, participant) => {
      if (track.kind === Track.Kind.Video) {
        const remoteEl = track.attach();
        remoteEl.style.width = "200px";
        document.getElementById("remoteVideos").appendChild(remoteEl);
      }
    });

    // 4) connect & publish local media
    await room.connect(wsUrl, token);
    console.log("✅ Connected to room:", room.name);

    // 5) now we can register the chat handler
    room.registerTextStreamHandler(
      "chat",
      async (reader, participantInfo) => {
        const msg = await reader.readAll();
        appendMessage(participantInfo.identity, msg);
      }
    );


    await room.localParticipant.setCameraEnabled(true);
    await room.localParticipant.setMicrophoneEnabled(true);
    console.log("🎥 Camera + 🎤 Mic published!");

    // attach your own video
    const localVid = room.localParticipant
      .getTrackPublication("camera")
      ?.videoTrack;
    if (localVid) {
      const el = localVid.attach();
      document.getElementById("localVideo").replaceWith(el);
      el.id = "localVideo";
    }

    // grab mic track SID for mute/unmute
    micTrackSid = room.localParticipant
      .getTrackPublication("microphone")
      ?.trackSid;
    console.log("🎙️ Mic track SID:", micTrackSid);

    // notify chat that you joined
    appendMessage("System", `${identity} joined the room`);
  } catch (err) {
    console.error("❌ Error during join/publish:", err);
  }
});

// MUTE MIC button
document.getElementById("muteBtn").addEventListener("click", async () => {
  if (!micTrackSid || !identity) {
    console.error("Mic not ready.");
    return;
  }
  const res = await fetch(
    `http://localhost:5000/muteTrack/${identity}/${micTrackSid}`
  );
  const text = await res.text();
  console.log("🔇 Server response:", text);
});

// SEND CHAT MESSAGE
document.getElementById("sendBtn").addEventListener("click", async () => {
  const input = document.getElementById("chatInput");
  const msg = input.value.trim();
  if (!msg || !room) return;
  try {
    // send full text on topic "chat"
    await room.localParticipant.sendText(msg, { topic: "chat" });
    appendMessage(identity, msg); // echo locally
    input.value = "";
  } catch (err) {
    console.error("❌ Failed to send chat:", err);
  }
});
