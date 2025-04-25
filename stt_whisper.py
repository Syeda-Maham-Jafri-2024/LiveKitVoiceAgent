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


# This code works perfectly fine for trying to implement the real time transcription approach using the stt_stream function
# but what i wanted to know was in this how are we going to know if the user has stopped speaking so that we can move on to
# the next step of llm generating response based on what user said, and hence i tried looking into what events vad offers and
# that is when i came across VADStream class so i need to try that now to check if this overall code can identify the user
# starting and stopping
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
    llm,
    transcription,
)
from livekit.plugins import openai, silero
from livekit.agents import transcription

from context import CONTEXT

load_dotenv()

logger = logging.getLogger("transcriber")


async def call_llm(transcript):
    """Send the final transcript to an LLM for processing."""
    try:
        initial_ctx = llm.ChatContext().append(
            role="system",
            text=(
                "Your name is Zainab baji, an expert in providing neonatal care. You are soft, caring but extremely professional when responding. your main language of interaction is urdu"
                "you have knowlegde of the WHO guidelines when it comes to antenatal care."
                "you need to ascertain if your directly speaking with the paitent or someone representing the patient and then address them in your answers appropriately."
                "you need to enquire if more details are needed."
                "Keep in mind that your user may need responses urgently so try to craft concise and to the point responses unless asked to elaborate."
                "you are mainly interfacing with users through voice and your user base are generaly people in remote areas or places with a lack of adequate medical facilities"
                "Your output is sent to a transcription service that will convert your responses to text. ALWAYS respond in urdu."
                "politley reject any query outside of your scope stating your reason."
                "try to speak in words that are generally spoken rather than written as most of your users may not be literate."
                "Do not give your responses in any form of markdown. try to give youre response as a natural response."
                "you have acces to a database that has a list of all users registered. the only thing you can do is check if someone exists in the db."
                f"Here is the question {transcript} and all the context you need to get started: {CONTEXT}"
            ),
        )
        llm_instance = openai.LLM(model="gpt-4o-mini")
        response = llm_instance.chat(chat_ctx=initial_ctx, temperature=0)

        reply = response["choices"][0]["message"]["content"]
        print("\n[LLM RESPONSE]:", reply)
        # return reply
    except Exception as e:
        print("\n[ERROR] Failed to call LLM:", str(e))
        # return None


async def _forward_transcription(
    stt_stream: stt.SpeechStream, stt_forwarder: transcription.STTSegmentsForwarder
):
    """Forward real-time transcription to the client and log in console"""
    cumulative_transcript = ""
    async for ev in stt_stream:
        if ev.type == stt.SpeechEventType.START_OF_SPEECH:
            print("\n[EVENT] User started speaking.")

        elif ev.type == stt.SpeechEventType.END_OF_SPEECH:
            print("\n[EVENT] User stopped speaking.")
            # asyncio.create_task(call_llm(cumulative_transcript))

        elif ev.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
            print(" [INTERIM] ->", ev.alternatives[0].text, end="\r", flush=True)

        elif ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
            print("\n [FINAL] ->", ev.alternatives[0].text)
            cumulative_transcript += " " + ev.alternatives[0].text

        elif ev.type == stt.SpeechEventType.RECOGNITION_USAGE:
            logger.debug(f"metrics: {ev.recognition_usage}")

        stt_forwarder.update(ev)


async def entrypoint(ctx: JobContext):
    logger.info(f"Starting real-time transcriber, room: {ctx.room.name}")

    stt_impl = openai.STT.with_groq(
        model="whisper-large-v3-turbo", language="ur", detect_language=False
    )

    if not stt_impl.capabilities.streaming:
        stt_impl = stt.StreamAdapter(
            stt=stt_impl,
            vad=silero.VAD.load(min_silence_duration=0.1),
        )

    async def transcribe_track(participant: rtc.RemoteParticipant, track: rtc.Track):
        audio_stream = rtc.AudioStream(track)
        stt_forwarder = transcription.STTSegmentsForwarder(
            room=ctx.room, participant=participant, track=track
        )

        stt_stream = stt_impl.stream()
        asyncio.create_task(_forward_transcription(stt_stream, stt_forwarder))
        async for ev in audio_stream:
            # print("[DEBUG] Pushing frame at", time.time())
            stt_stream.push_frame(ev.frame)

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
