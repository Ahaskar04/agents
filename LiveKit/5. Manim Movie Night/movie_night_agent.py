# movie_night_agent.py
"""
LiveKit Movie Night Agent
This agent does two things:
1. Publishes a pre-recorded Manim video to a LiveKit room
2. Speaks narration at scheduled times using TTS

The agent acts as a "virtual participant" in the room that streams
the video and provides commentary.
"""

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.plugins import cartesia
import json
import asyncio
import logging
import os
import cv2
import numpy as np
from pathlib import Path
from livekit.agents import AutoSubscribe


# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MovieNightAgent:
    """
    An agent that streams a Manim video and narrates it.
    
    This agent:
    1. Joins a LiveKit room as a participant
    2. Publishes a video track from an MP4 file
    3. Speaks narration at specific timestamps using TTS
    """
    
    def __init__(self, video_path: str, narration_path: str):
        """
        Initialize the Movie Night agent.
        
        Args:
            video_path: Path to the MP4 video file
            narration_path: Path to the JSON narration schedule
        """
        self.video_path = video_path
        self.narration_schedule = self._load_narration(narration_path)
        
        # Initialize TTS engine (Cartesia)
        self.tts = cartesia.TTS(
            model="sonic-2",
            voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"  # Professional voice
        )
        
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
        Called when the agent is assigned to a room.
        """
        logger.info(f"Movie Night Agent starting for room: {ctx.room.name}")
        
        try:
            # Step 1: Connect to the room
            # We don't subscribe to other participants' tracks since we're just broadcasting
            await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_NONE)
            logger.info("Connected to room")
            
            # Step 2: Start video streaming
            await self._start_video_stream(ctx)
            
            # Step 3: Run narration in parallel with video
            narration_task = asyncio.create_task(self._run_narration(ctx))
            
            # Keep the agent alive while video is streaming
            while self.is_streaming:
                await asyncio.sleep(1)
            
            # Clean up
            await narration_task
            logger.info("Movie Night completed")
            
        except Exception as e:
            logger.error(f"Error in Movie Night agent: {e}")
            raise
    
    async def _start_video_stream(self, ctx: JobContext):
        """
        Stream the video file to the room.
        
        This method:
        1. Opens the video file using OpenCV
        2. Creates a LiveKit video source and track
        3. Publishes frames at the correct framerate
        """
        logger.info(f"Starting video stream from: {self.video_path}")
        
        # Open video file with OpenCV
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video file: {self.video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        logger.info(f"Video info: {width}x{height} @ {fps}fps, duration: {duration:.1f}s")
        
        # Create LiveKit video source and track
        self.video_source = rtc.VideoSource(width, height)
        self.video_track = rtc.LocalVideoTrack.create_video_track(
            "manim-video",
            self.video_source
        )
        
        # Publish the video track to the room
        publication = await ctx.room.local_participant.publish_track(self.video_track)
        logger.info(f"Published video track: {publication.sid}")
        
        # Record when we started streaming
        self.video_start_time = asyncio.get_event_loop().time()
        self.is_streaming = True
        
        # Stream frames at the correct rate
        frame_interval = 1.0 / fps
        frame_count = 0
        
        try:
            while True:
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
                # This ensures video plays at normal speed
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
    
    async def _run_narration(self, ctx: JobContext):
        """
        Execute narration at scheduled times.
        
        This runs in parallel with video streaming and speaks
        narration lines at the correct timestamps.
        """
        logger.info("Starting narration schedule")
        
        # Wait for video to start
        while self.video_start_time is None:
            await asyncio.sleep(0.1)
        
        # Process each narration cue
        for i, cue in enumerate(self.narration_schedule):
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
        
        This creates an audio track, publishes it, streams the TTS audio,
        then unpublishes the track.
        """
        try:
            # Create audio source (24kHz mono for Cartesia)
            audio_source = rtc.AudioSource(
                sample_rate=24000,
                num_channels=1
            )
            
            # Create audio track
            audio_track = rtc.LocalAudioTrack.create_audio_track(
                "narration",
                audio_source
            )
            
            # Publish audio track
            publication = await ctx.room.local_participant.publish_track(audio_track)
            
            # Generate and stream TTS audio
            # The TTS engine returns audio frames that we capture
            frame_count = 0
            async for audio_frame in self.tts.synthesize(text):
                # Capture each audio frame
                audio_source.capture_frame(audio_frame)
                frame_count += 1
            
            logger.info(f"Spoke {len(text)} chars in {frame_count} frames")
            
            # Small pause after speaking
            await asyncio.sleep(0.5)
            
            # Unpublish the audio track
            await ctx.room.local_participant.unpublish_track(publication.sid)
            
        except Exception as e:
            logger.error(f"Error speaking: {e}")


async def entrypoint(ctx: JobContext):
    """
    Agent entrypoint - called when the agent is assigned to a room.
    
    The room name should be in format: "movie-{animation_name}"
    e.g., "movie-projectile" for the projectile motion animation
    """
    logger.info(f"=== MOVIE NIGHT AGENT STARTED ===")
    logger.info(f"Room: {ctx.room.name}")
    
    # Extract animation name from room name
    # Expected format: "movie-projectile" or "physics-projectile-room"
    room_name = ctx.room.name
    
    # Try different parsing strategies
    if room_name.startswith("movie-"):
        animation_name = room_name.replace("movie-", "")
    elif "physics-" in room_name:
        animation_name = room_name.replace("physics-", "").replace("-room", "")
    else:
        animation_name = "projectile"  # Default
    
    logger.info(f"Animation name: {animation_name}")
    
    # Build file paths
    # Adjust these paths based on your directory structure
    video_path = f"media/videos/demomanim/480p15/ProjectileMotion.mp4"
    narration_path = f"narration.json"
    
    # Check if files exist
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not os.path.exists(narration_path):
        logger.error(f"Narration file not found: {narration_path}")
        raise FileNotFoundError(f"Narration file not found: {narration_path}")
    
    # Create and run the agent
    agent = MovieNightAgent(video_path, narration_path)
    await agent.run(ctx)
        # movie_night_agent.py
"""
LiveKit Movie Night Agent
This agent does two things:
1. Publishes a pre-recorded Manim video to a LiveKit room
2. Speaks narration at scheduled times using TTS

The agent acts as a "virtual participant" in the room that streams
the video and provides commentary.
"""

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
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
    
    This agent:
    1. Joins a LiveKit room as a participant
    2. Publishes a video track from an MP4 file
    3. Speaks narration at specific timestamps using TTS
    """
    
    def __init__(self, video_path: str, narration_path: str):
        """
        Initialize the Movie Night agent.
        
        Args:
            video_path: Path to the MP4 video file
            narration_path: Path to the JSON narration schedule
        """
        self.video_path = video_path
        self.narration_schedule = self._load_narration(narration_path)
        
        # Initialize TTS engine (Cartesia)
        self.tts = cartesia.TTS(
            model="sonic-2",
            voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"  # Professional voice
        )
        
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
        Called when the agent is assigned to a room.
        """
        logger.info(f"Movie Night Agent starting for room: {ctx.room.name}")
        
        try:
            # Step 1: Connect to the room
            # We don't subscribe to other participants' tracks since we're just broadcasting
            await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_NONE)
            logger.info("Connected to room")
            
            # Step 2: Start video streaming
            await self._start_video_stream(ctx)
            
            # Step 3: Run narration in parallel with video
            narration_task = asyncio.create_task(self._run_narration(ctx))
            
            # Keep the agent alive while video is streaming
            while self.is_streaming:
                await asyncio.sleep(1)
            
            # Clean up
            await narration_task
            logger.info("Movie Night completed")
            
        except Exception as e:
            logger.error(f"Error in Movie Night agent: {e}")
            raise
    
    async def _start_video_stream(self, ctx: JobContext):
        """
        Stream the video file to the room.
        
        This method:
        1. Opens the video file using OpenCV
        2. Creates a LiveKit video source and track
        3. Publishes frames at the correct framerate
        """
        logger.info(f"Starting video stream from: {self.video_path}")
        
        # Open video file with OpenCV
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video file: {self.video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        logger.info(f"Video info: {width}x{height} @ {fps}fps, duration: {duration:.1f}s")
        
        # Create LiveKit video source and track
        self.video_source = rtc.VideoSource(width, height)
        self.video_track = rtc.LocalVideoTrack.create_video_track(
            "manim-video",
            self.video_source
        )
        
        # Publish the video track to the room
        publication = await ctx.room.local_participant.publish_track(self.video_track)
        logger.info(f"Published video track: {publication.sid}")
        
        # Record when we started streaming
        self.video_start_time = asyncio.get_event_loop().time()
        self.is_streaming = True
        
        # Stream frames at the correct rate
        frame_interval = 1.0 / fps
        frame_count = 0
        
        try:
            while True:
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
                # This ensures video plays at normal speed
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
    
    async def _run_narration(self, ctx: JobContext):
        """
        Execute narration at scheduled times.
        
        This runs in parallel with video streaming and speaks
        narration lines at the correct timestamps.
        """
        logger.info("Starting narration schedule")
        
        # Wait for video to start
        while self.video_start_time is None:
            await asyncio.sleep(0.1)
        
        # Process each narration cue
        for i, cue in enumerate(self.narration_schedule):
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
        
        This creates an audio track, publishes it, streams the TTS audio,
        then unpublishes the track.
        """
        try:
            # Create audio source (24kHz mono for Cartesia)
            audio_source = rtc.AudioSource(
                sample_rate=24000,
                num_channels=1
            )
            
            # Create audio track
            audio_track = rtc.LocalAudioTrack.create_audio_track(
                "narration",
                audio_source
            )
            
            # Publish audio track
            publication = await ctx.room.local_participant.publish_track(audio_track)
            
            # Generate and stream TTS audio
            # The TTS engine returns audio frames that we capture
            frame_count = 0
            async for audio_frame in self.tts.synthesize(text):
                # Capture each audio frame
                audio_source.capture_frame(audio_frame)
                frame_count += 1
            
            logger.info(f"Spoke {len(text)} chars in {frame_count} frames")
            
            # Small pause after speaking
            await asyncio.sleep(0.5)
            
            # Unpublish the audio track
            await ctx.room.local_participant.unpublish_track(publication.sid)
            
        except Exception as e:
            logger.error(f"Error speaking: {e}")


async def entrypoint(ctx: JobContext):
    """
    Agent entrypoint - called when the agent is assigned to a room.
    
    The room name should be in format: "movie-{animation_name}"
    e.g., "movie-projectile" for the projectile motion animation
    """
    logger.info(f"=== MOVIE NIGHT AGENT STARTED ===")
    logger.info(f"Room: {ctx.room.name}")
    
    # Extract animation name from room name
    # Expected format: "movie-projectile" or "physics-projectile-room"
    room_name = ctx.room.name
    
    # Try different parsing strategies
    if room_name.startswith("movie-"):
        animation_name = room_name.replace("movie-", "")
    elif "physics-" in room_name:
        animation_name = room_name.replace("physics-", "").replace("-room", "")
    else:
        animation_name = "projectile"  # Default
    
    logger.info(f"Animation name: {animation_name}")
    
    # Build file paths
    # Adjust these paths based on your directory structure
    video_path = f"media/videos/demomanim/480p15/ProjectileMotion.mp4"
    narration_path = f"narration.json"
    
    # Check if files exist
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not os.path.exists(narration_path):
        logger.error(f"Narration file not found: {narration_path}")
        raise FileNotFoundError(f"Narration file not found: {narration_path}")
    
    # Create and run the agent
    agent = MovieNightAgent(video_path, narration_path)
    await agent.run(ctx)
    
    logger.info("=== MOVIE NIGHT AGENT COMPLETED ===")


if __name__ == "__main__":
    # Run the agent using LiveKit CLI
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            # Set the worker type to ROOM so it gets assigned to specific rooms
            worker_type=agents.WorkerType.ROOM,
        )
    )
    logger.info("=== MOVIE NIGHT AGENT COMPLETED ===")


if __name__ == "__main__":
    # Run the agent using LiveKit CLI
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            # Set the worker type to ROOM so it gets assigned to specific rooms
            worker_type=agents.WorkerType.ROOM,
        )
    )