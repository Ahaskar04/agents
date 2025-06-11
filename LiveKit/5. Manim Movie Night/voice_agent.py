# backend/narration_agent.py
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import JobContext, AutoSubscribe
from livekit.plugins import cartesia
import json
import asyncio
import logging
from datetime import datetime

load_dotenv()
logger = logging.getLogger(__name__)


class NarrationBot:
    """A bot that joins the room and speaks narration at scheduled times"""
    
    def __init__(self, narration_schedule: list):
        self.narration_schedule = narration_schedule
        self.tts = cartesia.TTS(
            model="sonic-2", 
            voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"
        )
        self.start_time = None
        self.video_track = None
        
    async def run(self, ctx: JobContext):
        """Main bot logic"""
        # Connect to room
        await ctx.connect(auto_subscribe=AutoSubscribe.VIDEO_ONLY)
        logger.info(f"Narration bot connected to room: {ctx.room.name}")
        
        # Set up event handlers
        ctx.room.on('track_subscribed', self.on_track_subscribed)
        
        # Wait for video to start
        logger.info("Waiting for video track...")
        while self.video_track is None:
            await asyncio.sleep(0.1)
        
        # Start narration schedule
        await self.run_narration_schedule(ctx)
    
    def on_track_subscribed(self, track: rtc.Track, *args):
        """Detect when video starts playing"""
        if track.kind == "video" and self.video_track is None:
            logger.info("Video track detected! Starting narration timer...")
            self.video_track = track
            self.start_time = datetime.now()
    
    async def run_narration_schedule(self, ctx: JobContext):
        """Execute narration at scheduled times"""
        logger.info(f"Starting narration schedule with {len(self.narration_schedule)} cues")
        
        for cue in self.narration_schedule:
            # Calculate when to speak
            target_time = cue['time']
            elapsed = (datetime.now() - self.start_time).total_seconds()
            wait_time = target_time - elapsed
            
            if wait_time > 0:
                logger.info(f"Waiting {wait_time:.1f}s until next cue at {target_time}s")
                await asyncio.sleep(wait_time)
            
            # Speak the narration
            logger.info(f"Speaking at {target_time}s: {cue['text']}")
            await self.speak(ctx, cue['text'])
    
    async def speak(self, ctx: JobContext, text: str):
        """Use TTS to speak in the room"""
        try:
            # Generate audio using TTS
            audio_source = rtc.AudioSource(sample_rate=24000, num_channels=1)
            track = rtc.LocalAudioTrack.create_audio_track("narration", audio_source)
            
            # Publish the track
            publication = await ctx.room.local_participant.publish_track(track)
            
            # Generate and play TTS audio
            async for audio_frame in self.tts.synthesize(text):
                await audio_source.capture_frame(audio_frame.data)
            
            # Small pause after speaking
            await asyncio.sleep(0.5)
            
            # Unpublish the track
            await ctx.room.local_participant.unpublish_track(publication.sid)
            
        except Exception as e:
            logger.error(f"Error speaking: {e}")


async def entrypoint(ctx: JobContext):
    """Entry point for the narration agent"""
    logger.info("=== NARRATION AGENT STARTED ===")
    
    # Get narration schedule from room metadata or load from file
    # For this example, we'll load from a file based on room name
    room_name = ctx.room.name
    animation_name = room_name.replace("physics-", "").replace("-room", "")
    
    try:
        # Load narration schedule
        narration_file = f"animations/{animation_name}_narration.json"
        with open(narration_file) as f:
            narration_data = json.load(f)
        
        narration_schedule = narration_data.get("narration", [])
        logger.info(f"Loaded {len(narration_schedule)} narration cues for {animation_name}")
        
        # Create and run the bot
        bot = NarrationBot(narration_schedule)
        await bot.run(ctx)
        
    except Exception as e:
        logger.error(f"Error in narration agent: {e}")
        raise


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(
        entrypoint_fnc=entrypoint,
        worker_type=agents.WorkerType.ROOM,
    ))