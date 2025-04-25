import asyncio
from dotenv import load_dotenv
import os
from livekit import api


async def main():
    load_dotenv()

    livekit_api = api.LiveKitAPI()

    inbound_truck = api.SIPInboundTrunkInfo(
        name="Livekit Twilio Inbound Trunk",
        auth_username=os.getenv("TWIML_USERNAME"),
        auth_password=os.getenv("TWIML_PASSWORD"),
        numbers=["+19109910685"],
        # allowed_numbers=["+19109910685", "+923329266676"],
        krisp_enabled=True,
    )

    request = api.CreateSIPInboundTrunkRequest(trunk=inbound_truck)

    inbound_truck = await livekit_api.sip.create_sip_inbound_trunk(request)
    await livekit_api.aclose()


asyncio.run(main())
