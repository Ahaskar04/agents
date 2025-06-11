# minimal_working_agent.py
"""
Minimal working agent based on EXACT LiveKit documentation
Tests both sine wave audio and simple TTS
"""

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, JobRequest
from livekit.plugins import cartesia
import asyncio
import logging
import numpy as np
import math

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MinimalWorkingAgent:
    """Minimal agent based on exact documentation examples."""
    
    def __init__(self):
        self.tts = cartesia.TTS()
        
    async def run(self, ctx: JobContext):
        """Main entry point."""
        logger.info(f"🚀 MINIMAL AGENT starting for room: {ctx.room.name}")
        
        try:
            # Connect to room - EXACT from docs
            await ctx.connect(auto_subscribe=agents.AutoSubscribe.SUBSCRIBE_NONE)
            logger.info("✅ Connected to room")
            
            # Test 1: Documentation sine wave example
            logger.info("\n🧪 TEST 1: Documentation Sine Wave")
            await self._test_docs_sine_wave(ctx)
            
            await asyncio.sleep(2)
            
            # Test 2: Simple TTS
            logger.info("\n🧪 TEST 2: Simple TTS")
            await self._test_simple_tts(ctx)
            
            logger.info("✅ All tests completed!")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _test_docs_sine_wave(self, ctx: JobContext):
        """Test using EXACT sine wave example from documentation."""
        try:
            # EXACT constants from docs
            SAMPLE_RATE = 48000
            NUM_CHANNELS = 1
            AMPLITUDE = 2 ** 8 - 1
            SAMPLES_PER_CHANNEL = 480  # 10ms at 48kHz
            
            # Create source and track - EXACT from docs
            source = rtc.AudioSource(SAMPLE_RATE, NUM_CHANNELS)
            track = rtc.LocalAudioTrack.create_audio_track("example-track", source)
            
            # Publish options - EXACT from docs
            options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
            publication = await ctx.agent.publish_track(track, options)
            
            logger.info(f"✅ Published sine wave track: {publication.sid}")
            
            # Generate sine wave - EXACT from docs approach
            frequency = 440
            total_samples = 0
            duration = 3.0  # 3 seconds
            total_frames = int(duration * SAMPLE_RATE / SAMPLES_PER_CHANNEL)
            
            for frame_num in range(total_frames):
                # Create audio frame - EXACT from docs
                audio_frame = rtc.AudioFrame.create(SAMPLE_RATE, NUM_CHANNELS, SAMPLES_PER_CHANNEL)
                audio_data = np.frombuffer(audio_frame.data, dtype=np.int16)
                
                # Generate sine wave data - EXACT from docs
                time = (total_samples + np.arange(SAMPLES_PER_CHANNEL)) / SAMPLE_RATE
                sinewave = (AMPLITUDE * np.sin(2 * np.pi * frequency * time)).astype(np.int16)
                np.copyto(audio_data, sinewave)
                
                # Send frame - EXACT from docs
                await source.capture_frame(audio_frame)
                total_samples += SAMPLES_PER_CHANNEL
                
                # 10ms delay as per docs
                await asyncio.sleep(0.01)
            
            # Wait for playout
            await source.wait_for_playout()
            await ctx.agent.unpublish_track(publication.sid)
            
            logger.info("✅ Documentation sine wave test completed!")
            
        except Exception as e:
            logger.error(f"❌ Docs sine wave test failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _test_simple_tts(self, ctx: JobContext):
        """Test TTS with documentation-style approach."""
        try:
            text = "Hello! This is a TTS test using the documentation approach."
            logger.info(f"🗣️ Testing TTS: {text}")
            
            # Use same approach as docs but for TTS
            SAMPLE_RATE = 24000  # Cartesia uses 24kHz
            NUM_CHANNELS = 1
            
            # Create source and track
            source = rtc.AudioSource(SAMPLE_RATE, NUM_CHANNELS)
            track = rtc.LocalAudioTrack.create_audio_track("tts-track", source)
            
            # Publish options - same as docs
            options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
            publication = await ctx.agent.publish_track(track, options)
            
            logger.info(f"✅ Published TTS track: {publication.sid}")
            
            # Generate TTS and stream
            frame_count = 0
            async for audio_chunk in self.tts.synthesize(text):
                try:
                    if hasattr(audio_chunk, 'frame') and audio_chunk.frame is not None:
                        audio_frame = audio_chunk.frame
                        frame_count += 1
                        
                        # Send frame
                        await source.capture_frame(audio_frame)
                        
                        if frame_count == 1:
                            logger.info("🔊 TTS streaming started...")
                            
                except Exception as chunk_error:
                    logger.error(f"❌ TTS chunk error: {chunk_error}")
            
            logger.info(f"🎵 TTS complete: {frame_count} frames")
            
            # Wait for playout and cleanup
            await source.wait_for_playout()
            await ctx.agent.unpublish_track(publication.sid)
            
            logger.info("✅ TTS test completed!")
            
        except Exception as e:
            logger.error(f"❌ TTS test failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")


async def entrypoint(ctx: JobContext):
    """Agent entrypoint."""
    logger.info("🚀 MINIMAL WORKING AGENT STARTED")
    logger.info(f"Room: {ctx.room.name}")
    
    # Create and run agent
    agent = MinimalWorkingAgent()
    await agent.run(ctx)
    
    logger.info("🏁 MINIMAL AGENT COMPLETED")


async def request_fnc(req: JobRequest) -> None:
    """Accept ALL room requests for testing."""
    logger.info(f"🎯 Accepting job request for room: {req.room.name}")
    await req.accept()  # Accept any room!


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            request_fnc=request_fnc,
            worker_type=agents.WorkerType.ROOM,
        )
    )