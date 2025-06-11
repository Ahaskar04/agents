# movie_night_agent.py
"""
LiveKit Movie Night Agent - Fixed Version
This agent streams a pre-recorded video and provides narration
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
from pathlib import Path

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MovieNightAgent:
    """
    An agent that streams a Manim video and narrates it.
    """
    
    def __init__(self, video_path: str, narration_path: str):
        """
        Initialize the Movie Night agent.
        """
        self.video_path = video_path
        self.narration_schedule = self._load_narration(narration_path)
        
        # Initialize TTS engine (Cartesia)
        self.tts = cartesia.TTS()
        
        # Video streaming state
        self.video_source = None
        self.video_track = None
        self.is_streaming = False
        
        # Timing state
        self.video_start_time = None
        
    def _load_narration(self, narration_path: str) -> list:
        """Load and validate the narration schedule from JSON."""
        try:
            with open(narration_path, 'r') as f:
                data = json.load(f)
            
            narration = data.get("narration", [])
            logger.info(f"Loaded {len(narration)} narration cues")
            
            # Sort by time to ensure correct order
            narration.sort(key=lambda x: x['time'])
            return narration
            
        except Exception as e:
            logger.error(f"Failed to load narration: {e}")
            return []
    
    async def run(self, ctx: JobContext):
        """
        Main entry point for the agent.
        """
        logger.info(f"Movie Night Agent starting for room: {ctx.room.name}")
        
        try:
            # Step 1: Connect to the room
            await ctx.connect(auto_subscribe=agents.AutoSubscribe.SUBSCRIBE_NONE)
            logger.info("Connected to room")
            
            # Update our name in the room (if method exists)
            try:
                await ctx.room.local_participant.update_name("Movie Night Agent")
            except AttributeError:
                logger.info("update_name not available in this version")
            
            # Step 2: Start video streaming
            video_task = asyncio.create_task(self._start_video_stream(ctx))
            
            # Step 3: Run narration in parallel with video
            narration_task = asyncio.create_task(self._run_narration(ctx))
            
            # Wait for both tasks to complete
            await asyncio.gather(video_task, narration_task)
            
            logger.info("Movie Night completed")
            
        except Exception as e:
            logger.error(f"Error in Movie Night agent: {e}")
            raise
    
    async def _start_video_stream(self, ctx: JobContext):
        """
        Stream the video file to the room.
        """
        logger.info(f"Starting video stream from: {self.video_path}")
        
        # Check if file exists
        if not os.path.exists(self.video_path):
            logger.error(f"Video file not found: {self.video_path}")
            # Create a test pattern instead
            await self._stream_test_pattern(ctx)
            return
        
        # Open video file with OpenCV
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video file: {self.video_path}")
            await self._stream_test_pattern(ctx)
            return
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS) or 15  # Default to 15fps if not found
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"Video info: {width}x{height} @ {fps}fps, duration: {duration:.1f}s")
        
        # Create LiveKit video source and track
        self.video_source = rtc.VideoSource(width, height)
        self.video_track = rtc.LocalVideoTrack.create_video_track(
            "manim-video",
            self.video_source
        )
        
        # Publish the video track to the room
        try:
            publication = await ctx.room.local_participant.publish_track(self.video_track)
            logger.info(f"Published video track: {publication.sid}")
        except Exception as e:
            logger.error(f"Failed to publish video track: {e}")
            cap.release()
            return
        
        # Record when we started streaming
        self.video_start_time = asyncio.get_event_loop().time()
        self.is_streaming = True
        
        # Stream frames at the correct rate
        frame_interval = 1.0 / fps
        frame_count = 0
        
        try:
            while self.is_streaming:
                # Read next frame
                ret, frame = cap.read()
                if not ret:
                    logger.info(f"End of video after {frame_count} frames")
                    break
                
                # Convert BGR (OpenCV) to RGBA (LiveKit expects)
                frame_rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                
                # Create LiveKit VideoFrame
                video_frame = rtc.VideoFrame(
                    width=width,
                    height=height,
                    type=rtc.VideoBufferType.RGBA,
                    data=frame_rgba.tobytes()
                )
                
                # Capture frame to the video source
                self.video_source.capture_frame(video_frame)
                
                # Wait to maintain correct framerate
                await asyncio.sleep(frame_interval)
                
                frame_count += 1
                
                # Log progress every second
                if frame_count % int(fps) == 0:
                    elapsed = frame_count / fps
                    logger.info(f"Video progress: {elapsed:.1f}s / {duration:.1f}s")
        
        finally:
            # Clean up
            cap.release()
            self.is_streaming = False
            logger.info("Video streaming completed")
    
    async def _stream_test_pattern(self, ctx: JobContext):
        """Stream a test pattern when video file is not found"""
        logger.info("Streaming test pattern")
        
        width, height = 640, 480
        fps = 15
        
        # Create video source and track
        self.video_source = rtc.VideoSource(width, height)
        self.video_track = rtc.LocalVideoTrack.create_video_track(
            "test-pattern",
            self.video_source
        )
        
        # Publish the video track
        try:
            publication = await ctx.room.local_participant.publish_track(self.video_track)
            logger.info(f"Published test pattern track: {publication.sid}")
        except Exception as e:
            logger.error(f"Failed to publish test pattern: {e}")
            return
        
        self.video_start_time = asyncio.get_event_loop().time()
        self.is_streaming = True
        
        # Stream test pattern for 30 seconds
        frame_interval = 1.0 / fps
        for i in range(int(30 * fps)):
            if not self.is_streaming:
                break
                
            # Create a simple test pattern
            frame = np.zeros((height, width, 4), dtype=np.uint8)
            
            # Draw some text
            text = f"Test Pattern - Frame {i}"
            cv2.putText(frame, text, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255, 255), 2)
            
            # Add some color bars
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
                x_start = j * bar_width
                x_end = (j + 1) * bar_width
                frame[100:200, x_start:x_end] = color
            
            # Create video frame
            video_frame = rtc.VideoFrame(
                width=width,
                height=height,
                type=rtc.VideoBufferType.RGBA,
                data=frame.tobytes()
            )
            
            self.video_source.capture_frame(video_frame)
            await asyncio.sleep(frame_interval)
        
        self.is_streaming = False
        logger.info("Test pattern completed")
    
    async def _run_narration(self, ctx: JobContext):
        """
        Execute narration at scheduled times.
        """
        logger.info("Starting narration schedule")
        
        # Wait for video to start
        while self.video_start_time is None:
            await asyncio.sleep(0.1)
        
        # If no narration schedule, just wait
        if not self.narration_schedule:
            logger.info("No narration schedule found")
            return
        
        # Process each narration cue
        for i, cue in enumerate(self.narration_schedule):
            if not self.is_streaming:
                break
                
            target_time = cue['time']
            text = cue['text']
            
            # Calculate how long to wait
            elapsed = asyncio.get_event_loop().time() - self.video_start_time
            wait_time = target_time - elapsed
            
            if wait_time > 0:
                logger.info(f"Waiting {wait_time:.1f}s for cue {i+1}/{len(self.narration_schedule)}")
                await asyncio.sleep(wait_time)
            
            # Speak the narration
            logger.info(f"Speaking at {target_time}s: {text[:50]}...")
            await self._speak(ctx, text)
        
        logger.info("Narration schedule completed")
    
    async def _speak(self, ctx: JobContext, text: str):
        """
        Use TTS to speak text in the room.
        """
        try:
            # Create audio source (24kHz mono for Cartesia)
            audio_source = rtc.AudioSource(24000, 1)
            
            # Create audio track
            audio_track = rtc.LocalAudioTrack.create_audio_track(
                "narration",
                audio_source
            )
            
            # Publish audio track
            publication = await ctx.room.local_participant.publish_track(audio_track)
            
            # Generate and stream TTS audio
            # Try the newer API first, fall back to older API if needed
            try:
                tts_stream = self.tts.stream()
                tts_stream.push_text(text)
                tts_stream.flush()
                
                async for audio_event in tts_stream:
                    audio_frame = rtc.AudioFrame(
                        data=audio_event.audio,
                        sample_rate=24000,
                        num_channels=1,
                        samples_per_channel=len(audio_event.audio) // 2  # 16-bit audio
                    )
                    await audio_source.capture_frame(audio_frame)
            except AttributeError:
                # Fall back to older synthesize API
                logger.info("Using older TTS API")
                async for audio_frame in self.tts.synthesize(text):
                    await audio_source.capture_frame(audio_frame)
            
            logger.info(f"Spoke {len(text)} chars")
            
            # Small pause after speaking
            await asyncio.sleep(0.5)
            
            # Unpublish the audio track
            await ctx.room.local_participant.unpublish_track(publication.sid)
            
        except Exception as e:
            logger.error(f"Error speaking: {e}")


async def entrypoint(ctx: JobContext):
    """
    Agent entrypoint - called when the agent is assigned to a room.
    """
    logger.info(f"=== MOVIE NIGHT AGENT STARTED ===")
    logger.info(f"Room: {ctx.room.name}")
    logger.info(f"Room SID: {ctx.room.sid}")
    
    # Extract animation name from room name
    room_name = ctx.room.name
    
    # Try different parsing strategies
    if room_name.startswith("movie-"):
        animation_name = room_name.replace("movie-", "")
    elif "physics-" in room_name:
        animation_name = room_name.replace("physics-", "").replace("-room", "")
    else:
        animation_name = "projectile"  # Default
    
    logger.info(f"Animation name: {animation_name}")
    
    # Build file paths - use current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(current_dir, "media", "videos", "demomanim", "480p15", "ProjectileMotion.mp4")
    narration_path = os.path.join(current_dir, "narration.json")
    
    # Also try alternative paths
    if not os.path.exists(video_path):
        # Try without the media folder structure
        video_path = os.path.join(current_dir, "ProjectileMotion.mp4")
    
    logger.info(f"Video path: {video_path}")
    logger.info(f"Narration path: {narration_path}")
    
    # Create and run the agent
    agent = MovieNightAgent(video_path, narration_path)
    await agent.run(ctx)
    
    logger.info("=== MOVIE NIGHT AGENT COMPLETED ===")


# Define a job request handler for room assignment
async def request_fnc(req: JobRequest) -> None:
    """
    Decide whether to accept a job request.
    Accept rooms that start with "movie-"
    """
    logger.info(f"Job request for room: {req.room.name}")
    
    # Accept movie rooms
    if req.room.name.startswith("movie-"):
        logger.info(f"Accepting job for room: {req.room.name}")
        await req.accept()
    else:
        logger.info(f"Rejecting job for room: {req.room.name}")
        await req.reject()


if __name__ == "__main__":
    # Run the agent using LiveKit CLI
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=request_fnc,  # Add request function
            worker_type=agents.WorkerType.ROOM,
        )
    )