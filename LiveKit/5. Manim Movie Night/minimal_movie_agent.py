# minimal_movie_agent.py
"""
Minimal Movie Agent - Based on the WORKING audio test agent
Uses the exact same approach that works for audio + adds simple video
"""

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, JobRequest
from livekit.plugins import cartesia
import json
import asyncio
import logging
import os
import cv2
import numpy as np

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MinimalMovieAgent:
    """Minimal agent using the exact working audio approach + video."""
    
    def __init__(self, video_path: str, narration_path: str):
        self.video_path = video_path
        self.narration_schedule = self._load_narration(narration_path)
        self.tts = cartesia.TTS()
        self.start_time = None
        
    def _load_narration(self, narration_path: str) -> list:
        """Load narration schedule."""
        try:
            with open(narration_path, 'r') as f:
                data = json.load(f)
            narration = data.get("narration", [])
            logger.info(f"📖 Loaded {len(narration)} narration cues")
            narration.sort(key=lambda x: x['time'])
            return narration
        except Exception as e:
            logger.error(f"❌ Failed to load narration: {e}")
            return []
    
    async def run(self, ctx: JobContext):
        """Main entry point."""
        logger.info(f"🎬 MINIMAL MOVIE AGENT starting for room: {ctx.room.name}")
        
        try:
            # Connect to room
            await ctx.connect(auto_subscribe=agents.AutoSubscribe.SUBSCRIBE_NONE)
            logger.info("✅ Connected to room")
            
            # Start timing
            await asyncio.sleep(1)
            self.start_time = asyncio.get_event_loop().time()
            logger.info("⏰ Movie timing started")
            
            # Start video and audio concurrently
            video_task = asyncio.create_task(self._stream_video(ctx))
            audio_task = asyncio.create_task(self._run_narration(ctx))
            
            # Wait for both
            await asyncio.gather(video_task, audio_task)
            
            logger.info("🎬 Minimal movie agent completed")
            
        except Exception as e:
            logger.error(f"❌ Error in Minimal Movie agent: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def _stream_video(self, ctx: JobContext):
        """Stream video using the simplest possible approach."""
        logger.info(f"📹 Starting minimal video stream")
        
        # Check video file
        if not os.path.exists(self.video_path):
            logger.error(f"❌ Video file not found: {self.video_path}")
            return
        
        # Open video
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            logger.error(f"❌ Cannot open video: {self.video_path}")
            return
        
        # Get properties
        fps = cap.get(cv2.CAP_PROP_FPS) or 15
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        
        logger.info(f"📺 Video: {width}x{height} @ {fps}fps")
        
        # Create video source and track - MINIMAL
        video_source = rtc.VideoSource(width, height)
        video_track = rtc.LocalVideoTrack.create_video_track("movie-video", video_source)
        
        # Publish with MINIMAL options (same pattern as working audio)
        try:
            publication = await ctx.agent.publish_track(video_track)
            logger.info(f"✅ Published video track: {publication.sid}")
        except Exception as e:
            logger.error(f"❌ Failed to publish video: {e}")
            cap.release()
            return
        
        # Stream frames
        frame_interval = 1.0 / fps
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.info(f"📹 Video ended after {frame_count} frames")
                    break
                
                # Convert to RGBA
                frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                
                # Create frame
                video_frame = rtc.VideoFrame(
                    width=width,
                    height=height,
                    type=rtc.VideoBufferType.RGBA,
                    data=frame_rgba.tobytes()
                )
                
                # Send frame
                video_source.capture_frame(video_frame)
                await asyncio.sleep(frame_interval)
                frame_count += 1
                
                # Log every 5 seconds
                if frame_count % (int(fps) * 5) == 0:
                    elapsed = frame_count / fps
                    logger.info(f"📹 Video progress: {elapsed:.1f}s")
        
        finally:
            cap.release()
            logger.info("📹 Video streaming completed")
    
    async def _run_narration(self, ctx: JobContext):
        """Run narration using the EXACT working audio test approach."""
        logger.info("🎤 Starting narration schedule")
        
        if not self.narration_schedule:
            logger.warning("⚠️ No narration schedule")
            return
        
        # Process each narration cue
        for i, cue in enumerate(self.narration_schedule, 1):
            target_time = cue['time']
            text = cue['text']
            
            # Wait for right time
            elapsed = asyncio.get_event_loop().time() - self.start_time
            wait_time = target_time - elapsed
            
            if wait_time > 0:
                logger.info(f"⏳ [{i}/{len(self.narration_schedule)}] Waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
            
            # Speak using EXACT working approach
            logger.info(f"🎤 [{i}/{len(self.narration_schedule)}] Speaking: {text[:50]}...")
            await self._speak_working(ctx, text)
        
        logger.info("🎤 All narration completed")
    
    async def _speak_working(self, ctx: JobContext, text: str):
        """TTS using the EXACT approach from working audio test agent."""
        try:
            # Create audio source and track - EXACT same as working agent
            sample_rate = 24000
            audio_source = rtc.AudioSource(sample_rate, 1)
            audio_track = rtc.LocalAudioTrack.create_audio_track("narration", audio_source)
            
            # Publish with MINIMAL options (same as working audio test)
            publication = await ctx.agent.publish_track(audio_track)
            logger.info(f"✅ Published audio track: {publication.sid}")
            
            # Generate TTS - EXACT same logic as working agent
            frame_count = 0
            async for audio_chunk in self.tts.synthesize(text):
                try:
                    if hasattr(audio_chunk, 'frame') and audio_chunk.frame is not None:
                        audio_frame = audio_chunk.frame
                        frame_count += 1
                        
                        # Send frame
                        await audio_source.capture_frame(audio_frame)
                        
                        if frame_count == 1:
                            logger.info("🔊 TTS streaming...")
                            
                except Exception as chunk_error:
                    logger.error(f"❌ TTS chunk error: {chunk_error}")
            
            logger.info(f"🎵 TTS complete: {frame_count} frames")
            
            # Wait and cleanup - EXACT same as working agent
            await audio_source.wait_for_playout()
            await ctx.agent.unpublish_track(publication.sid)
            logger.info("✅ TTS completed")
            
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")


async def entrypoint(ctx: JobContext):
    """Agent entrypoint."""
    logger.info("🚀 MINIMAL MOVIE AGENT STARTED")
    logger.info(f"Room: {ctx.room.name}")
    
    # Find files
    current_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(current_dir, "media", "videos", "demomanim", "480p15", "ProjectileMotion.mp4")
    narration_path = os.path.join(current_dir, "narration.json")
    
    # Try alternative video path
    if not os.path.exists(video_path):
        video_path = os.path.join(current_dir, "ProjectileMotion.mp4")
    
    logger.info(f"📁 Video: {video_path}")
    logger.info(f"📁 Video exists: {os.path.exists(video_path)}")
    logger.info(f"📁 Narration: {narration_path}")
    logger.info(f"📁 Narration exists: {os.path.exists(narration_path)}")
    
    # Create and run agent
    agent = MinimalMovieAgent(video_path, narration_path)
    await agent.run(ctx)
    
    logger.info("🏁 MINIMAL MOVIE AGENT COMPLETED")


async def request_fnc(req: JobRequest) -> None:
    """Accept ANY room request for testing."""
    logger.info(f"🎯 Accepting job request for room: {req.room.name}")
    await req.accept()  # Accept all rooms!


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=request_fnc,
            worker_type=agents.WorkerType.ROOM,
        )
    )