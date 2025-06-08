import { Room } from 'livekit-client';

const wsUrl = "wss://solvd-x191iqhu.livekit.cloud";
const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoibXkgbmFtZSIsInZpZGVvIjp7InJvb21Kb2luIjp0cnVlLCJyb29tIjoibXktcm9vbSIsImNhblB1Ymxpc2giOnRydWUsImNhblN1YnNjcmliZSI6dHJ1ZSwiY2FuUHVibGlzaERhdGEiOnRydWV9LCJzdWIiOiJpZGVudGl0eSIsImlzcyI6IkFQSXM5ZnZzcWF5Qm90YyIsIm5iZiI6MTc0OTM2NDkzNSwiZXhwIjoxNzQ5Mzg2NTM1fQ.rQ_DL8GYGR4H4K9y9ROLY9w82ljEO9ptv1Fox9eJgX0";

document.getElementById("joinBtn").addEventListener("click", async () => {
  const room = new Room();

  try {
    await room.connect(wsUrl, token);
    console.log("✅ Connected to room:", room.name);

    // 🔊 Enable mic + camera
    await room.localParticipant.setCameraEnabled(true);
    await room.localParticipant.setMicrophoneEnabled(true);
    console.log("🎥 Camera + 🎤 Mic published!");

    // 🎞️ Attach local video to <video id="localVideo">
    const videoTrack = room.localParticipant.getTrackPublication('camera')?.videoTrack;
    if (videoTrack) {
      const element = videoTrack.attach();
      document.getElementById('localVideo').replaceWith(element);
      element.id = 'localVideo'; // Keep same ID for styling
    }

  } catch (err) {
    console.error("❌ Error connecting or publishing tracks:", err);
  }
});
