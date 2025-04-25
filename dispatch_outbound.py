import random
import asyncio
from livekit import api


async def make_dispatch():
    lkapi = api.LiveKitAPI()

    room_name = f"outbound-{''.join(str(random.randint(0, 9)) for _ in range(10))}"

    await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name="livekitoutbound",  # This must match your WorkerOptions
            room=room_name,
            metadata='{"phone_number": "+9233266676"}',
        )
    )
    print(f"Dispatch created for room {room_name}")
    await lkapi.aclose()


if __name__ == "__main__":
    asyncio.run(make_dispatch())
