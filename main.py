import asyncio

from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import openai, silero
from api import AssistantFnc
from livekit.plugins.openai import stt

from context import CONTEXT

load_dotenv()


async def entrypoint(ctx: JobContext):
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
            f"Here is all the context you need to get started: {CONTEXT}"
        ),
    )

    # specifyying that we just want to connect to the audio tracks currently
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    fnc_ctx = AssistantFnc()

    groq_stt = stt.STT.with_groq(
        model="whisper-large-v3-turbo", language="ur", detect_language=False
    )
    assistant = VoiceAssistant(
        # to detect if the user is speakin or not so we know when to cut them off and send the message over to our ai
        vad=silero.VAD.load(),
        stt=groq_stt,
        llm=openai.LLM(model="gpt-4o", temperature=0),
        tts=openai.TTS(model="gpt-4o-mini-tts", voice="shimmer"),
        chat_ctx=initial_ctx,
        fnc_ctx=fnc_ctx,
    )
    # the way these voice assistants work in live kit is that they can connet to a room
    # the agent is going to connect to a live kti server, the live kit server is then going to send the agent a job
    # and when that job is send it will have a room associated with it
    assistant.start(ctx.room)

    await asyncio.sleep(1)
    await assistant.say(" میں آپ کی کیا مدد کر سکتا ہوں ", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

# import asyncio
# from dotenv import load_dotenv
# from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
# from livekit.agents.voice_assistant import VoiceAssistant
# from livekit.plugins import openai, silero
# from api import AssistantFnc
# from livekit.plugins.openai import stt

# load_dotenv()


# async def entrypoint(ctx: JobContext):
#     initial_ctx = llm.ChatContext().append(
#         role="system",
#         text=(
#             "You are a voice assistant created by Livekit. Your interface with users will be the voice"
#             "You should use short and concise responses and avoid the usage of unpronounceable punctuation."
#         ),
#     )

#     # Specify that we just want to connect to the audio tracks currently
#     await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
#     fnc_ctx = AssistantFnc()

#     # STT (Speech-to-Text) with Groq for Whisper model
#     groq_stt = stt.STT.with_groq(
#         model="whisper-large-v3-turbo", language="ur", detect_language=False
#     )

#     # Create the assistant with Voice Activity Detection (VAD)
#     assistant = VoiceAssistant(
#         vad=silero.VAD.load(),  # Detects when the user is speaking
#         stt=groq_stt,  # Speech-to-Text for real-time transcription
#         llm=openai.LLM(model="gpt-4o", temperature=0),
#         tts=openai.TTS(model="gpt-4o-mini-tts", voice="shimmer"),
#         chat_ctx=initial_ctx,
#         fnc_ctx=fnc_ctx,
#     )

#     # Start the assistant and connect it to the room
#     assistant.start(ctx.room)

#     # Capture the audio stream and start real-time transcription
#     audio_stream = (
#         await assistant.audio_stream()
#     )  # Capture the audio stream from the assistant

#     async def process_audio_stream():
#         # Send audio frames to STT (whisper model)
#         stt_stream = groq_stt.stream()
#         async for frame in audio_stream:
#             stt_stream.push_frame(frame)  # Push audio frames to STT model

#             # Handle interim transcription results
#             async for ev in stt_stream:
#                 if ev.type == stt.SpeechEventType.INTERIM_TRANSCRIPT:
#                     print(
#                         f"Interim: {ev.alternatives[0].text}", end=""
#                     )  # Print interim results
#                 elif ev.type == stt.SpeechEventType.FINAL_TRANSCRIPT:
#                     print(
#                         f"\nFinal: {ev.alternatives[0].text}"
#                     )  # Print final transcription

#     # Run the process for streaming and real-time transcription
#     await process_audio_stream()

#     # Wait before starting response
#     await asyncio.sleep(1)
#     await assistant.say("میں آپ کی کیا مدد کر سکتا ہوں", allow_interruptions=True)


# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
