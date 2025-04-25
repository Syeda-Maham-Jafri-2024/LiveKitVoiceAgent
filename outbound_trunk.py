import asyncio
import os
from dotenv import load_dotenv
from livekit import api
from livekit.protocol.sip import CreateSIPOutboundTrunkRequest, SIPOutboundTrunkInfo


async def main():
    load_dotenv()
    livekit_api = api.LiveKitAPI()

    trunk = SIPOutboundTrunkInfo(
        name="livekitoutbound",
        address="livekitoutbound.pstn.twilio.com",
        numbers=["+19109910685"],
        auth_username=os.getenv("TRUNK_CRED_USERNAME"),
        auth_password=os.getenv("TRUNK_CRED_PWD"),
    )

    request = CreateSIPOutboundTrunkRequest(trunk=trunk)

    trunk = await livekit_api.sip.create_sip_outbound_trunk(request)

    print(f"Successfully created {trunk}")

    await livekit_api.aclose()


asyncio.run(main())
