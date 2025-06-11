# fixed_movie_night_agent.py
"""
LiveKit Movie Night Agent - WORKING VERSION
Based on current LiveKit documentation
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


class MovieNightAgent:
    """An agent that streams a Manim video and narrates it."""
            
    def __init__(self, video_path: str, narration_path: str):
        self.video_path = video_path
        self.narration_schedule = self._load_narration(narration_path)
        
        # Initialize TTS engine
        self.tts = cartesia.TTS()
        
        # Video streaming state
        self.video_source = None
        self.video_track = None
        self.is_streaming = False
        self.video_start_time = None
        
    def _load_narration(self, narration_path: str) -> list:
        """Load and validate the narration schedule from JSON."""
        try:
            with open(narration_path, 'r') as f:
                data = json.load(f)
            narration = data.get("narration", [])
            logger.info(f"Loaded {len(narration)} narration cues")
            narration.sort(key=lambda x: x['time'])
            return narration
        except Exception as e:
            logger.error(f"Failed to load narration: {e}")
            return []
    
    async def run(self, ctx: JobContext):
        """Main entry point for the agent."""
        logger.info(f"🎬 Movie Night Agent starting for room: {ctx.room.name}")
        
        try:
            # Connect to the room
            await ctx.connect(auto_subscribe=agents.AutoSubscribe.SUBSCRIBE_NONE)
            logger.info("✅ Connected to room")
            
            # Update our name
            try:
                await ctx.room.local_participant.update_name("Movie Night Agent")
                logger.info("✅ Updated agent name")
            except Exception as e:
                logger.warning(f"Could not update name: {e}")
            
            # Start video streaming and narration in parallel
            video_task = asyncio.create_task(self._start_video_stream(ctx))
            narration_task = asyncio.create_task(self._run_narration(ctx))
            
            # Wait for both tasks
            await asyncio.gather(video_task, narration_task)
            
            logger.info("🎬 Movie Night completed")
            
        except Exception as e:
            logger.error(f"❌ Error in Movie Night agent: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    async def _start_video_stream(self, ctx: JobContext):
        """Stream the video file using current LiveKit patterns."""
        logger.info(f"📹 Starting video stream from: {self.video_path}")
        
        # Check if video file exists
        if not os.path.exists(self.video_path):
            logger.error(f"❌ Video file not found: {self.video_path}")
            await self._stream_test_pattern(ctx)
            return
        
        # Open video with OpenCV
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            logger.error(f"❌ Cannot open video file: {self.video_path}")
            await self._stream_test_pattern(ctx)
            return
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS) or 15
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"📺 Video: {width}x{height} @ {fps}fps, duration: {duration:.1f}s")
        
        # Create video source and track using CURRENT API
        self.video_source = rtc.VideoSource(width, height)
        self.video_track = rtc.LocalVideoTrack.create_video_track(
            "manim-video", 
            self.video_source
        )
        
        # Publish track with CURRENT options format
        options = rtc.TrackPublishOptions(
            source=rtc.TrackSource.SOURCE_CAMERA,  # Updated enum
            simulcast=True,
            video_encoding=rtc.VideoEncoding(
                max_framerate=int(fps),
                max_bitrate=3_000_000,
            ),
            video_codec=rtc.VideoCodec.H264,
        )
        
        try:
            # Use ctx.agent instead of ctx.room.local_participant
            publication = await ctx.agent.publish_track(self.video_track, options)
            logger.info(f"✅ Published video track: {publication.sid}")
        except Exception as e:
            logger.error(f"❌ Failed to publish video track: {e}")
            cap.release()
            return
        
        # Record start time
        self.video_start_time = asyncio.get_event_loop().time()
        self.is_streaming = True
        
        # Stream frames at correct rate
        frame_interval = 1.0 / fps
        frame_count = 0
        
        try:
            while self.is_streaming:
                ret, frame = cap.read()
                if not ret:
                    logger.info(f"📹 End of video after {frame_count} frames")
                    break
                
                # Convert BGR to RGBA (CRITICAL: use correct format)
                frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                
                # Create VideoFrame using CURRENT API
                video_frame = rtc.VideoFrame(
                    width=width,
                    height=height,
                    type=rtc.VideoBufferType.RGBA,  # Updated enum
                    data=frame_rgba.tobytes()
                )
                
                # Send frame using CURRENT method
                self.video_source.capture_frame(video_frame)  # Note: not await
                
                # Wait for next frame
                await asyncio.sleep(frame_interval)
                frame_count += 1
                
                # Log progress
                if frame_count % int(fps) == 0:
                    elapsed = frame_count / fps
                    logger.info(f"📹 Progress: {elapsed:.1f}s / {duration:.1f}s")
        
        finally:
            cap.release()
            self.is_streaming = False
            logger.info("📹 Video streaming completed")
    
    async def _stream_test_pattern(self, ctx: JobContext):
        """Stream a test pattern when video file is missing."""
        logger.info("🎨 Streaming test pattern")
        
        width, height, fps = 640, 480, 15
        
        # Create video source and track
        self.video_source = rtc.VideoSource(width, height)
        self.video_track = rtc.LocalVideoTrack.create_video_track(
            "test-pattern", 
            self.video_source
        )
        
        # Publish with current API
        options = rtc.TrackPublishOptions(
            source=rtc.TrackSource.SOURCE_CAMERA,
            video_encoding=rtc.VideoEncoding(
                max_framerate=fps,
                max_bitrate=1_000_000,
            ),
        )
        
        try:
            publication = await ctx.agent.publish_track(self.video_track, options)
            logger.info(f"✅ Published test pattern: {publication.sid}")
        except Exception as e:
            logger.error(f"❌ Failed to publish test pattern: {e}")
            return
        
        self.video_start_time = asyncio.get_event_loop().time()
        self.is_streaming = True
        
        frame_interval = 1.0 / fps
        
        # Create colored test pattern for 30 seconds
        for i in range(int(30 * fps)):
            if not self.is_streaming:
                break
            
            # Create RGBA frame
            frame = np.zeros((height, width, 4), dtype=np.uint8)
            
            # Add text
            text = f"Movie Night Test - Frame {i}"
            cv2.putText(frame, text, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 
                       1, (255, 255, 255, 255), 2)
            
            # Add color bars
            bar_width = width // 7
            colors = [
                (255, 255, 255, 255),  # White
                (255, 255, 0, 255),    # Yellow  
                (0, 255, 255, 255),    # Cyan
                (0, 255, 0, 255),      # Green
                (255, 0, 255, 255),    # Magenta
                (255, 0, 0, 255),      # Red
                (0, 0, 255, 255),      # Blue
            ]
            
            for j, color in enumerate(colors):
                x1, x2 = j * bar_width, (j + 1) * bar_width
                frame[100:200, x1:x2] = color
            
            # Create and send video frame
            video_frame = rtc.VideoFrame(
                width=width,
                height=height, 
                type=rtc.VideoBufferType.RGBA,
                data=frame.tobytes()
            )
            
            self.video_source.capture_frame(video_frame)
            await asyncio.sleep(frame_interval)
        
        self.is_streaming = False
        logger.info("🎨 Test pattern completed")
    
    async def _run_narration(self, ctx: JobContext):
        """Execute narration at scheduled times."""
        logger.info("🎤 Starting narration schedule")
        
        # Wait for video to start
        while self.video_start_time is None:
            await asyncio.sleep(0.1)
        
        if not self.narration_schedule:
            logger.info("No narration schedule - skipping")
            # Just wait while video plays
            while self.is_streaming:
                await asyncio.sleep(1)
            return
        
        # Process narration cues
        for i, cue in enumerate(self.narration_schedule):
            if not self.is_streaming:
                break
                
            target_time = cue['time']
            text = cue['text']
            
            # Wait for the right time
            elapsed = asyncio.get_event_loop().time() - self.video_start_time
            wait_time = target_time - elapsed
            
            if wait_time > 0:
                logger.info(f"⏳ Waiting {wait_time:.1f}s for narration {i+1}")
                await asyncio.sleep(wait_time)
            
            # Speak the narration
            logger.info(f"🎤 Speaking: {text[:50]}...")
            await self._speak(ctx, text)
        
        logger.info("🎤 Narration completed")
    
    async def _speak(self, ctx: JobContext, text: str):
        """Use TTS to speak text in the room."""
        try:
            # Create audio source for TTS
            audio_source = rtc.AudioSource(24000, 1)  # 24kHz mono
            audio_track = rtc.LocalAudioTrack.create_audio_track(
                "narration", 
                audio_source
            )
            
            # Publish audio track
            options = rtc.TrackPublishOptions(
                source=rtc.TrackSource.SOURCE_MICROPHONE
            )
            publication = await ctx.agent.publish_track(audio_track, options)
            
            # Generate and stream TTS
            async for audio_chunk in self.tts.synthesize(text):
                # Extract audio data
                if hasattr(audio_chunk, 'data'):
                    audio_data = audio_chunk.data
                else:
                    audio_data = audio_chunk
                
                # Get sample rate
                sample_rate = getattr(audio_chunk, 'sample_rate', 24000)
                
                # Calculate samples (assuming 16-bit audio)
                samples_per_channel = len(audio_data) // 2
                
                # Create audio frame
                audio_frame = rtc.AudioFrame(
                    data=audio_data,
                    sample_rate=sample_rate,
                    num_channels=1,
                    samples_per_channel=samples_per_channel
                )
                
                # Send to room
                await audio_source.capture_frame(audio_frame)
            
            # Cleanup
            await asyncio.sleep(1)  # Let audio finish
            await ctx.agent.unpublish_track(publication.sid)
            
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")


async def entrypoint(ctx: JobContext):
    """Agent entrypoint."""
    logger.info(f"🚀 MOVIE NIGHT AGENT STARTED")
    logger.info(f"Room: {ctx.room.name}")
    
    # Parse animation from room name
    room_name = ctx.room.name
    if room_name.startswith("movie-"):
        animation_name = room_name.replace("movie-", "")
    else:
        animation_name = "projectile"
    
    logger.info(f"🎬 Animation: {animation_name}")
    
    # Build file paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(current_dir, "media", "videos", "demomanim", "480p15", "ProjectileMotion.mp4")
    narration_path = os.path.join(current_dir, "narration.json")
    
    # Try alternative paths
    if not os.path.exists(video_path):
        video_path = os.path.join(current_dir, "ProjectileMotion.mp4")
    
    logger.info(f"📁 Video: {video_path}")
    logger.info(f"📁 Narration: {narration_path}")
    logger.info(f"📁 Video exists: {os.path.exists(video_path)}")
    
    # Create and run agent
    agent = MovieNightAgent(video_path, narration_path)
    await agent.run(ctx)
    
    logger.info("🏁 MOVIE NIGHT COMPLETED")


async def request_fnc(req: JobRequest) -> None:
    """Accept movie room requests."""
    logger.info(f"🎯 Job request for room: {req.room.name}")
    
    if req.room.name.startswith("movie-"):
        logger.info(f"✅ Accepting movie room: {req.room.name}")
        await req.accept()
    else:
        logger.info(f"❌ Rejecting non-movie room: {req.room.name}")
        await req.reject()


if __name__ == "__main__":
    # Run with current CLI patterns
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=request_fnc,
            worker_type=agents.WorkerType.ROOM,
        )
    )