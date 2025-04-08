import asyncio

from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import openai, silero
from api import AssistantFnc
from livekit.plugins.openai import stt

load_dotenv()


async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by Livekit. Your interface with users will be the voice"
            "You should use shot and concise responses and avoid the usage oun unpronouncable punctuation."
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
