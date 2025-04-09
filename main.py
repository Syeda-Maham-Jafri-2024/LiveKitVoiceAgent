# import asyncio

# from dotenv import load_dotenv
# from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
# from livekit.agents.voice_assistant import VoiceAssistant
# from livekit.plugins import openai, silero
# from api import AssistantFnc
# from livekit.plugins.openai import stt

# from context import CONTEXT

# load_dotenv()


# async def entrypoint(ctx: JobContext):
#     initial_ctx = llm.ChatContext().append(
#         role="system",
#         text=(
#             "Your name is Zainab baji, an expert in providing neonatal care. You are soft, caring but extremely professional when responding. your main language of interaction is urdu"
#             "you have knowlegde of the WHO guidelines when it comes to antenatal care."
#             "you need to ascertain if your directly speaking with the paitent or someone representing the patient and then address them in your answers appropriately."
#             "you need to enquire if more details are needed."
#             "Keep in mind that your user may need responses urgently so try to craft concise and to the point responses unless asked to elaborate."
#             "you are mainly interfacing with users through voice and your user base are generaly people in remote areas or places with a lack of adequate medical facilities"
#             "Your output is sent to a transcription service that will convert your responses to text. ALWAYS respond in urdu."
#             "politley reject any query outside of your scope stating your reason."
#             "try to speak in words that are generally spoken rather than written as most of your users may not be literate."
#             "Do not give your responses in any form of markdown. try to give youre response as a natural response."
#             "you have acces to a database that has a list of all users registered. the only thing you can do is check if someone exists in the db."
#             f"Here is all the context you need to get started: {CONTEXT}"
#         ),
#     )

#     # specifyying that we just want to connect to the audio tracks currently
#     await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
#     fnc_ctx = AssistantFnc()

#     groq_stt = stt.STT.with_groq(
#         model="whisper-large-v3-turbo", language="ur", detect_language=False

#     )
#     assistant = VoiceAssistant(
#         # to detect if the user is speakin or not so we know when to cut them off and send the message over to our ai
#         vad=silero.VAD.load(),
#         stt=groq_stt,
#         llm=openai.LLM(model="gpt-4o", temperature=0),
#         tts=openai.TTS(model="gpt-4o-mini-tts", voice="shimmer"),
#         chat_ctx=initial_ctx,
#         fnc_ctx=fnc_ctx,
#     )
#     # the way these voice assistants work in live kit is that they can connet to a room
#     # the agent is going to connect to a live kti server, the live kit server is then going to send the agent a job
#     # and when that job is send it will have a room associated with it
#     assistant.start(ctx.room)

#     await asyncio.sleep(1)
#     await assistant.say(" میں آپ کی کیا مدد کر سکتا ہوں ", allow_interruptions=True)


# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))





import asyncio
from livekit.agents.voice_assistant import VoiceAssistant
import asyncio
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import openai, silero
from livekit.plugins.openai import stt
from api import AssistantFnc
from dotenv import load_dotenv
from context import CONTEXT

load_dotenv()

class StreamingVoiceAssistant(VoiceAssistant):
    async def continuous_listen(self):
        # Override the standard listen loop
        while True:
            # Read a short audio chunk
            audio_chunk = await self.audio_source.read_chunk()
            if audio_chunk is None:
                break
            
            # Directly call your STT engine for partial transcription
            # Assume transcribe_stream is a method supporting small chunks
            partial_text = self.stt.transcribe_stream(audio_chunk)
            if partial_text:
                # Immediately process or output the partial result.
                print("Partial transcription:", partial_text)
                # Optionally, send it back to the client or use as input for further processing.
                
            # Sleep a small interval to simulate continuous streaming
            await asyncio.sleep(0.1)

    def start(self, room):
        # Start the assistant and ensure you kick off the continuous listen loop.
        super().start(room)
        asyncio.create_task(self.continuous_listen())

# In your entrypoint, replace the creation of the voice assistant:
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
    
    # Instead of VoiceAssistant, instantiate the streaming version:
    assistant = StreamingVoiceAssistant(
        vad=silero.VAD.load(),
        stt=groq_stt,  # Ensure your STT engine here supports streaming or partial transcription calls
        llm=openai.LLM(model="gpt-4o", temperature=0),
        tts=openai.TTS(model="gpt-4o-mini-tts", voice="shimmer"),
        chat_ctx=initial_ctx,
        fnc_ctx=AssistantFnc(),
    )
    assistant.start(ctx.room)

    # Optionally, greet the user:
    await asyncio.sleep(1)
    await assistant.say(" میں آپ کی کیا مدد کر سکتا ہوں ", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

# -------------------------------
# main.py

# import asyncio
# from dotenv import load_dotenv

# from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
# from livekit.agents.voice_assistant import VoiceAssistant
# from livekit.plugins import openai, silero

# from api import AssistantFnc
# from context import CONTEXT
# from custom_whisper_stt import SimulatedStreamingWhisperSTT  # ✅ Our custom streaming STT

# load_dotenv()

# import logging

# logging.basicConfig(level=logging.INFO)


# async def entrypoint(ctx: JobContext):
#     initial_ctx = llm.ChatContext().append(
#         role="system",
#         text=(
#             "Your name is Zainab baji, an expert in providing neonatal care. You are soft, caring but extremely professional when responding. your main language of interaction is urdu. "
#             "you have knowlegde of the WHO guidelines when it comes to antenatal care. "
#             "you need to ascertain if your directly speaking with the paitent or someone representing the patient and then address them in your answers appropriately. "
#             "you need to enquire if more details are needed. "
#             "Keep in mind that your user may need responses urgently so try to craft concise and to the point responses unless asked to elaborate. "
#             "you are mainly interfacing with users through voice and your user base are generaly people in remote areas or places with a lack of adequate medical facilities. "
#             "Your output is sent to a transcription service that will convert your responses to text. ALWAYS respond in urdu. "
#             "politley reject any query outside of your scope stating your reason. "
#             "try to speak in words that are generally spoken rather than written as most of your users may not be literate. "
#             "Do not give your responses in any form of markdown. try to give your response as a natural response. "
#             "you have access to a database that has a list of all users registered. the only thing you can do is check if someone exists in the db. "
#             f"Here is all the context you need to get started: {CONTEXT}"
#         ),
#     )

#     await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
#     fnc_ctx = AssistantFnc()

#     # ✅ Replaced groq STT with our custom simulated streaming Whisper STT
#     simulated_stt = SimulatedStreamingWhisperSTT(
#         model="whisper-1", language="ur", detect_language=False
#     )

#     assistant = VoiceAssistant(
#         vad=silero.VAD.load(),
#         stt=simulated_stt,
#         llm=openai.LLM(model="gpt-4o", temperature=0),
#         tts=openai.TTS(model="gpt-4o-mini-tts", voice="shimmer"),
#         chat_ctx=initial_ctx,
#         fnc_ctx=fnc_ctx,
#     )

#     assistant.start(ctx.room)

#     await asyncio.sleep(1)
#     await assistant.say(" میں آپ کی کیا مدد کر سکتا ہوں ", allow_interruptions=True)


# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

