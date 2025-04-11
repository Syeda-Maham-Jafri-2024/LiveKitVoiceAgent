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
# from livekit.plugins import openai, silero

# load_dotenv()

# logger = logging.getLogger("transcriber")


# async def _forward_transcription(
#     stt_stream: stt.SpeechStream, stt_forwarder: transcription.STTSegmentsForwarder
# ):
#     """Forward the transcription to the client and log the transcript in the console"""
#     async for ev in stt_stream:
#         if ev.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
#             print(" -> ", ev.alternatives[0].text)
#         elif ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
#             print(" -> ", ev.alternatives[0].text)
#         elif ev.type == stt.SpeechEventType.RECOGNITION_USAGE:
#             logger.debug(f"metrics: {ev.recognition_usage}")

#         stt_forwarder.update(ev)


# async def entrypoint(ctx: JobContext):
#     logger.info(f"starting transcriber (speech to text) example, room: {ctx.room.name}")
#     # this example uses OpenAI Whisper, but you can use assemblyai, deepgram, google, azure, etc.

#     stt_impl = openai.STT(language="ur")

#     if not stt_impl.capabilities.streaming:
#         # wrap with a stream adapter to use streaming semantics
#         stt_impl = stt.StreamAdapter(
#             stt=stt_impl,
#             vad=silero.VAD.load(
#                 min_silence_duration=1.0,  # Increase to 1 second of silence before triggering end of speech
#             ),
#         )

#     async def transcribe_track(participant: rtc.RemoteParticipant, track: rtc.Track):
#         audio_stream = rtc.AudioStream(track)
#         stt_forwarder = transcription.STTSegmentsForwarder(
#             room=ctx.room, participant=participant, track=track
#         )

#         stt_stream = stt_impl.stream()
#         asyncio.create_task(_forward_transcription(stt_stream, stt_forwarder))

#         async for ev in audio_stream:
#             stt_stream.push_frame(ev.frame)

#     @ctx.room.on("track_subscribed")
#     def on_track_subscribed(
#         track: rtc.Track,
#         publication: rtc.TrackPublication,
#         participant: rtc.RemoteParticipant,
#     ):
#         # spin up a task to transcribe each track
#         if track.kind == rtc.TrackKind.KIND_AUDIO:
#             asyncio.create_task(transcribe_track(participant, track))

#     await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)


# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


#####################################################################################################################
# import time
# import asyncio

# async def transcribe_track(participant: rtc.RemoteParticipant, track: rtc.Track):
#     audio_stream = rtc.AudioStream(track)
#     stt_forwarder = transcription.STTSegmentsForwarder(
#         room=ctx.room, participant=participant, track=track
#     )

#     stt_stream = stt_impl.stream()
#     asyncio.create_task(_forward_transcription(stt_stream, stt_forwarder))

#     frame_buffer = []  # Store frames
#     push_interval = 2.0  # Push frames every 2 seconds
#     last_push_time = time.time()

#     async for ev in audio_stream:
#         frame_buffer.append(ev.frame)  # Collect frames

#         current_time = time.time()
#         if current_time - last_push_time >= push_interval:
#             print(f"Pushing {len(frame_buffer)} frames for transcription after {push_interval} seconds.")

#             # Push all buffered frames
#             for frame in frame_buffer:
#                 stt_stream.push_frame(frame)

#             # Clear buffer and reset timer
#             frame_buffer.clear()
#             last_push_time = current_time
#########################################################################################################################


import asyncio
import logging
import time
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

logger = logging.getLogger("transcriber")


async def _forward_transcription(
    stt_stream: stt.SpeechStream, stt_forwarder: transcription.STTSegmentsForwarder
):
    """Forward real-time transcription to the client and log in console"""
    async for ev in stt_stream:
        if ev.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
            print(
                " [INTERIM] ->", ev.alternatives[0].text, end="\r", flush=True
            )  # Keep updating
        elif ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
            print("\n [FINAL] ->", ev.alternatives[0].text)
        elif ev.type == stt.SpeechEventType.RECOGNITION_USAGE:
            logger.debug(f"metrics: {ev.recognition_usage}")

        stt_forwarder.update(ev)


async def entrypoint(ctx: JobContext):
    logger.info(f"Starting real-time transcriber, room: {ctx.room.name}")

    stt_impl = openai.STT(language="ur")

    if not stt_impl.capabilities.streaming:
        # Enable near-real-time processing by reducing silence detection time
        stt_impl = stt.StreamAdapter(
            stt=stt_impl,
            vad=silero.VAD.load(min_silence_duration=0.3),  # Reduced silence duration
        )

    async def transcribe_track(participant: rtc.RemoteParticipant, track: rtc.Track):
        audio_stream = rtc.AudioStream(track)
        stt_forwarder = transcription.STTSegmentsForwarder(
            room=ctx.room, participant=participant, track=track
        )

        stt_stream = stt_impl.stream()
        asyncio.create_task(_forward_transcription(stt_stream, stt_forwarder))
        # vad_stream = silero.VADStream(vad=silero.VAD.load(min_silence_duration=0.3))
        async for ev in audio_stream:
            # if vad_stream.is_speech(ev.frame):
            stt_stream.push_frame(ev.frame)  # Push frames as they arrive

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            asyncio.create_task(transcribe_track(participant, track))

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
