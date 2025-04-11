import asyncio
import logging

from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    stt,
    transcription,
)
from livekit.plugins import openai, silero

load_dotenv()

# This sets up a logger to record messages related to the transcriber. The logger is initialized with the name "transcriber" for clarity.
logger = logging.getLogger("transcriber")


async def _forward_transcription(
    # stt_stream: Represents the real-time stream of speech-to-text events.
    # stt_forwarder: Handles forwarding the transcription results to the client.
    stt_stream: stt.SpeechStream,
    stt_forwarder: transcription.STTSegmentsForwarder,
):
    """Forward the transcription to the client and log the transcript in the console"""
    async for ev in stt_stream:
        if ev.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
            # you may not want to log interim transcripts, they are not final and may be incorrect
            pass
        elif ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
            print(" -> ", ev.alternatives[0].text)
        elif ev.type == stt.SpeechEventType.RECOGNITION_USAGE:
            logger.debug(f"metrics: {ev.recognition_usage}")

        stt_forwarder.update(ev)


async def entrypoint(ctx: JobContext):
    logger.info(f"starting transcriber (speech to text) example, room: {ctx.room.name}")

    stt_impl = openai.STT(model="whisper-1", language="ur")

    if not stt_impl.capabilities.streaming:
        # wrap with a stream adapter to use streaming semantics
        stt_impl = stt.StreamAdapter(
            stt=stt_impl,
            vad=silero.VAD.load(
                min_silence_duration=0.2,
            ),
        )

    async def transcribe_track(participant: rtc.RemoteParticipant, track: rtc.Track):
        audio_stream = rtc.AudioStream(track)
        stt_forwarder = transcription.STTSegmentsForwarder(
            room=ctx.room, participant=participant, track=track
        )

        stt_stream = stt_impl.stream()
        asyncio.create_task(_forward_transcription(stt_stream, stt_forwarder))

        async for ev in audio_stream:
            stt_stream.push_frame(ev.frame)

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        # spin up a task to transcribe each track
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            asyncio.create_task(transcribe_track(participant, track))

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


# import asyncio
# import logging

# from dotenv import load_dotenv
# from livekit import rtc
# from livekit.agents import (
#     AutoSubscribe,
#     JobContext,
#     WorkerOptions,
#     cli,
#     stt,
#     transcription,
# )
# from livekit.plugins import openai
# from livekit.plugins.openai import stt

# # Load environment variables
# load_dotenv()

# # Set up logging
# logger = logging.getLogger("transcriber")
# logging.basicConfig(level=logging.DEBUG)  # Set logging level to debug for more info


# async def entrypoint(ctx: JobContext):
#     logger.info(f"Starting transcriber (speech to text) example, room: {ctx.room.name}")

#     # Set up the STT implementation (using OpenAI Whisper)
#     stt_impl = openai.STT()

#     @ctx.room.on("track_subscribed")
#     def on_track_subscribed(
#         track: rtc.Track,
#         publication: rtc.TrackPublication,
#         participant: rtc.RemoteParticipant,
#     ):
#         # Log when an audio track is subscribed to
#         if track.kind == rtc.TrackKind.KIND_AUDIO:
#             logger.debug(
#                 f"Audio track subscribed: {track.sid} by participant {participant.sid}"
#             )
#             asyncio.create_task(transcribe_track(participant, track))

#     async def transcribe_track(participant: rtc.RemoteParticipant, track: rtc.Track):
#         """
#         Handles the parallel tasks of sending audio to the STT service and
#         forwarding transcriptions back to the app.
#         """
#         audio_stream = rtc.AudioStream(track)
#         stt_forwarder = transcription.STTSegmentsForwarder(
#             room=ctx.room, participant=participant, track=track
#         )

#         stt_stream = stt_impl.stream()

#         # Run tasks for audio input and transcription output in parallel
#         await asyncio.gather(
#             _handle_audio_input(audio_stream, stt_stream),
#             _handle_transcription_output(stt_stream, stt_forwarder),
#         )

#     async def _handle_audio_input(
#         audio_stream: rtc.AudioStream, stt_stream: stt.SpeechStream
#     ):
#         """Pushes audio frames to the speech-to-text stream."""
#         async for ev in audio_stream:
#             logger.debug(f"Received audio frame: {ev.frame}")  # Log audio frame
#             stt_stream.push_frame(ev.frame)

#     async def _handle_transcription_output(
#         stt_stream: stt.SpeechStream, stt_forwarder: transcription.STTSegmentsForwarder
#     ):
#         """Receives transcription events from the speech-to-text service."""
#         async for ev in stt_stream:
#             logger.debug(f"Received STT event: {ev.type}")  # Log event type
#             if ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
#                 print(" -> ", ev.alternatives[0].text)  # Output final transcript
#             stt_forwarder.update(ev)

#     # Connect to the room with automatic audio-only subscription
#     await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)


# if __name__ == "__main__":
#     # Run the app with the entrypoint function
#     cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
