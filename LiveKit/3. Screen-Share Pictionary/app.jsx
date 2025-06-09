import {
  Room,
  RoomEvent,
  Track,
  createLocalScreenTracks,
  DataPacket_Kind
} from 'livekit-client';

const wsUrl = "wss://solvd-x191iqhu.livekit.cloud";

let room = null;
let screenTrack = null;
let identity = null;

// simple canvas setup
const localCanvas  = document.getElementById("drawLocal");
const localCtx     = localCanvas.getContext("2d");
const remoteCanvas = document.getElementById("drawRemote");
const remoteCtx    = remoteCanvas.getContext("2d");

let drawing = false, lastX = 0, lastY = 0;

// DRAW on local and send strokes
localCanvas.addEventListener("mousedown", e => {
  drawing = true;
  lastX = e.offsetX; lastY = e.offsetY;
});
localCanvas.addEventListener("mouseup", () => { drawing = false; });
localCanvas.addEventListener("mousemove", e => {
  if (!drawing || !room) return;
  const x = e.offsetX, y = e.offsetY;
  // draw locally
  localCtx.beginPath();
  localCtx.moveTo(lastX, lastY);
  localCtx.lineTo(x, y);
  localCtx.stroke();
  // send stroke data
  const payload = JSON.stringify({ x, y, lastX, lastY });
  room.localParticipant.publishData(
    new TextEncoder().encode(payload),
    DataPacket_Kind.RELIABLE
  );
  lastX = x; lastY = y;
});

// handle remote strokes
function handleData(data, participant) {
  const msg = new TextDecoder().decode(data);
  const { x, y, lastX, lastY } = JSON.parse(msg);
  remoteCtx.beginPath();
  remoteCtx.moveTo(lastX, lastY);
  remoteCtx.lineTo(x, y);
  remoteCtx.stroke();
}

// JOIN + setup
document.getElementById("joinBtn").addEventListener("click", async () => {
  identity = document.getElementById("identityInput").value || "guest";
  const name = document.getElementById("nameInput").value || identity;

  // fetch dynamic token
  const tokenRes = await fetch(
    `http://localhost:5000/getToken?identity=${identity}&name=${name}`
  );
  const token = await tokenRes.text();

  room = new Room();

  // when any new video track arrives (including screen‐share)
  room.on(RoomEvent.TrackSubscribed, (track, _, participant) => {
    if (track.kind === Track.Kind.Video) {
      const el = track.attach();
      el.style.width = "300px";
      document.getElementById("remoteVideos").appendChild(el);
    }
  });

  // when any data arrives (our drawing strokes)
  room.on(RoomEvent.DataReceived, (payload, participant) => {
    handleData(payload, participant);
  });

  // connect & publish camera/mic
  await room.connect(wsUrl, token);
  await room.localParticipant.setCameraEnabled(true);
  await room.localParticipant.setMicrophoneEnabled(true);

  // attach your camera
  const camPub = room.localParticipant.getTrackPublication("camera");
  if (camPub?.videoTrack) {
    const el = camPub.videoTrack.attach();
    document.getElementById("localVideo").replaceWith(el);
    el.id = "localVideo";
  }

  // enable screen-share button
  document.getElementById("shareBtn").disabled = false;
});

// SCREEN-SHARE toggle
document.getElementById("shareBtn").addEventListener("click", async () => {
  const btn = document.getElementById("shareBtn");
  if (!screenTrack) {
    // start sharing
    const [track] = await createLocalScreenTracks({ audio: false });
    screenTrack = track;
    await room.localParticipant.publishTrack(screenTrack);
    btn.textContent = "Stop Screen Share";
    track.on("ended", () => {
      // user hit browser “Stop sharing”
      screenTrack = null;
      btn.textContent = "Start Screen Share";
    });
  } else {
    // stop sharing
    await room.localParticipant.unpublishTrack(screenTrack);
    screenTrack.stop();
    screenTrack = null;
    btn.textContent = "Start Screen Share";
  }
});
