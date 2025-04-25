import asyncio
import os

from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import openai, silero
from livekit import rtc, api

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

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    print(f"[Agent] Connected to room: {ctx.room.name}")

    # === SIP OUTBOUND CALL LOGIC ===
    import json
    from livekit import api  # Make sure this import is at the top of your file

    phone_number = "+9233266676"

    if phone_number:
        sip_participant_identity = phone_number
        try:
            await ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=ctx.room.name,
                    sip_call_to=phone_number,
                    sip_trunk_id="ST_MAsGRyAX43Tn",  # Replace with your real trunk ID
                    participant_identity=sip_participant_identity,
                    wait_until_answered=True,
                )
            )
            print("✅ SIP call picked up successfully")
        except api.TwirpError as e:
            print(f"❌ Error creating SIP participant: {e.message}")
            print(f"SIP status code: {e.code}")
            ctx.shutdown()
            return

    # === CONTINUE WITH ASSISTANT LOGIC ===
    groq_stt = stt.STT.with_groq(
        model="whisper-large-v3-turbo", language="ur", detect_language=False
    )

    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=groq_stt,
        llm=openai.LLM(model="gpt-4o", temperature=0),
        tts=openai.TTS(model="gpt-4o-mini-tts", voice="shimmer"),
        chat_ctx=initial_ctx,
    )

    assistant.start(ctx.room)

    await asyncio.sleep(1)
    await assistant.say(" میں آپ کی کیا مدد کر سکتا ہوں ", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="livekitoutbound"))
