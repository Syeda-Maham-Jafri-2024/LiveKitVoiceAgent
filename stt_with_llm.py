# oksy so this code is basically the continuation of stt attempt that i have don in the stt_whisper.py
# file, the main idea for this code is to make a call to llm if the vad functionality is able to correctly
# identify that the user has stopped speaking, in the case where the user has stopped speaking all of what
# we have as the transcript is basically the user's question and we need that to pass to the llm to let it
# know what we want to know from it, so we are going to collect the transcript and provide it to the llm
# along with the context
# import asyncio
# import logging
# import time
# import openai  # Import OpenAI API
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
# from livekit.plugins import openai as livekit_openai, silero

# load_dotenv()

# logger = logging.getLogger("transcriber")

# # OpenAI API Key (Ensure you set this in your .env file)
# openai.api_key = "your-openai-api-key"

# async def call_llm(transcript):
#     """Send the final transcript to an LLM for processing."""
#     try:
#         response = await asyncio.to_thread(
#             openai.ChatCompletion.create,
#             model="gpt-4o",
#             messages=[{"role": "user", "content": transcript}]
#         )
#         reply = response["choices"][0]["message"]["content"]
#         print("\n[LLM RESPONSE]:", reply)
#     except Exception as e:
#         print("\n[ERROR] Failed to call LLM:", str(e))


# async def _forward_transcription(
#     stt_stream: stt.SpeechStream, stt_forwarder: transcription.STTSegmentsForwarder
# ):
#     """Forward real-time transcription to the client and log in console"""
#     transcript_text = ""  # Store final transcript

#     async for ev in stt_stream:
#         if ev.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
#             print(" [INTERIM] ->", ev.alternatives[0].text, end="\r", flush=True)
#         elif ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
#             print("\n [FINAL] ->", ev.alternatives[0].text)
#             transcript_text = ev.alternatives[0].text  # Store final text
#         elif ev.type == stt.SpeechEventType.RECOGNITION_USAGE:
#             logger.debug(f"metrics: {ev.recognition_usage}")

#         stt_forwarder.update(ev)

#     return transcript_text  # Return the final transcript


# async def entrypoint(ctx: JobContext):
#     logger.info(f"Starting real-time transcriber, room: {ctx.room.name}")

#     stt_impl = livekit_openai.STT(language="ur")

#     if not stt_impl.capabilities.streaming:
#         stt_impl = stt.StreamAdapter(
#             stt=stt_impl,
#             vad=silero.VAD.load(min_silence_duration=0.3),  # Reduced silence duration
#         )

#     async def transcribe_track(participant: rtc.RemoteParticipant, track: rtc.Track):
#         audio_stream = rtc.AudioStream(track)
#         stt_forwarder = transcription.STTSegmentsForwarder(
#             room=ctx.room, participant=participant, track=track
#         )

#         stt_stream = stt_impl.stream()
#         vad_stream = silero.VADStream(vad=silero.VAD.load(min_silence_duration=0.3))

#         asyncio.create_task(_forward_transcription(stt_stream, stt_forwarder))

#         silence_threshold = 1.0  # Detect user stop after 1 second
#         last_speech_time = time.time()
#         user_speaking = False
#         final_transcript = ""

#         async def monitor_silence():
#             """Monitor silence and trigger LLM call when user stops speaking."""
#             nonlocal last_speech_time, user_speaking, final_transcript
#             while True:
#                 await asyncio.sleep(0.1)
#                 if user_speaking and (time.time() - last_speech_time) > silence_threshold:
#                     print("\n[EVENT] User stopped speaking.")
#                     user_speaking = False  # Reset speaking state

#                     if final_transcript:  # Ensure we have text before calling LLM
#                         asyncio.create_task(call_llm(final_transcript))  # Call LLM async

#         asyncio.create_task(monitor_silence())  # Start silence detection

#         async for ev in audio_stream:
#             if vad_stream.is_speech(ev.frame):
#                 last_speech_time = time.time()
#                 if not user_speaking:
#                     print("\n[EVENT] User started speaking.")
#                     user_speaking = True
#                 stt_stream.push_frame(ev.frame)  # Send frame to STT

#     @ctx.room.on("track_subscribed")
#     def on_track_subscribed(
#         track: rtc.Track,
#         publication: rtc.TrackPublication,
#         participant: rtc.RemoteParticipant,
#     ):
#         if track.kind == rtc.TrackKind.KIND_AUDIO:
#             asyncio.create_task(transcribe_track(participant, track))

#     await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)


# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


# okay now this code below is doing the same as what the above code is doing but it does it by using the llm functionality
# that livekit it self provides
import asyncio
import logging
import time
import openai  # Import OpenAI API
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    stt,
    transcription,
    llm,
)
from livekit.plugins import openai as livekit_openai, silero

from context import CONTEXT

load_dotenv()

logger = logging.getLogger("transcriber")

# OpenAI API Key (Ensure you set this in your .env file)
openai.api_key = "your-openai-api-key"


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
        response = await asyncio.to_thread(
            llm=livekit_openai.LLM(model="gpt-4o-mini").chat(
                chat_ctx=initial_ctx, temperature=0
            )
        )
        reply = response["choices"][0]["message"]["content"]
        print("\n[LLM RESPONSE]:", reply)
    except Exception as e:
        print("\n[ERROR] Failed to call LLM:", str(e))


async def _forward_transcription(
    stt_stream: stt.SpeechStream, stt_forwarder: transcription.STTSegmentsForwarder
):
    """Forward real-time transcription to the client and log in console"""
    transcript_text = ""  # Store final transcript

    async for ev in stt_stream:
        if ev.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
            print(" [INTERIM] ->", ev.alternatives[0].text, end="\r", flush=True)
        elif ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
            print("\n [FINAL] ->", ev.alternatives[0].text)
            transcript_text = ev.alternatives[0].text  # Store final text
        elif ev.type == stt.SpeechEventType.RECOGNITION_USAGE:
            logger.debug(f"metrics: {ev.recognition_usage}")

        stt_forwarder.update(ev)

    return transcript_text  # Return the final transcript


async def entrypoint(ctx: JobContext):
    logger.info(f"Starting real-time transcriber, room: {ctx.room.name}")

    stt_impl = livekit_openai.STT(language="ur")

    if not stt_impl.capabilities.streaming:
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
        vad_stream = silero.VADStream(vad=silero.VAD.load(min_silence_duration=0.3))

        asyncio.create_task(_forward_transcription(stt_stream, stt_forwarder))

        silence_threshold = 1.0  # Detect user stop after 1 second
        last_speech_time = time.time()
        user_speaking = False
        final_transcript = ""

        async def monitor_silence():
            """Monitor silence and trigger LLM call when user stops speaking."""
            nonlocal last_speech_time, user_speaking, final_transcript
            while True:
                await asyncio.sleep(0.1)
                if (
                    user_speaking
                    and (time.time() - last_speech_time) > silence_threshold
                ):
                    print("\n[EVENT] User stopped speaking.")
                    user_speaking = False  # Reset speaking state

                    if final_transcript:  # Ensure we have text before calling LLM
                        asyncio.create_task(
                            call_llm(final_transcript)
                        )  # Call LLM async

        asyncio.create_task(monitor_silence())  # Start silence detection

        async for ev in audio_stream:
            if vad_stream.is_speech(ev.frame):
                last_speech_time = time.time()
                if not user_speaking:
                    print("\n[EVENT] User started speaking.")
                    user_speaking = True
                stt_stream.push_frame(ev.frame)  # Send frame to STT

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
