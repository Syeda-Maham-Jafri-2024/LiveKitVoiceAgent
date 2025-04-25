import asyncio
import random
from dotenv import load_dotenv
import os
from livekit import api


async def main():
    load_dotenv()

    lkapi = api.LiveKitAPI()
    request = api.CreateSIPDispatchRuleRequest(
        rule=api.SIPDispatchRule(
            dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                room_prefix="call-",
            )
        ),
        room_config=api.RoomConfiguration(
            agents=[
                api.RoomAgentDispatch(
                    agent_name="lk-inbound-agent",
                    metadata="job dispatch metadata",
                )
            ]
        ),
    )
    dispatch = await lkapi.sip.create_sip_dispatch_rule(request)
    print("created dispatch", dispatch)
    await lkapi.aclose()


asyncio.run(main())

# import random
# import json
# from livekit import api


# async def main():
#     livekit_api = api.LiveKitAPI()

#     await livekit_api.agent_dispatch.create_dispatch(
#         request=api.CreateAgentDispatchRequest(
#             room_name="outbound-room",
#             agent_name="outbound_agent",
#             metadata="outbound call test",
#         )
#     )
#     await livekit_api.aclose()


# asyncio.run(main())
