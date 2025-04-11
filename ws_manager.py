# ws_manager.py
import asyncio
import websockets

class WebSocketManager:
    def __init__(self, host="0.0.0.0", port=8765):
        self.clients = set()
        self.host = host
        self.port = port

    async def start(self):
        async def handler(websocket, path):
            self.clients.add(websocket)
            try:
                async for _ in websocket:
                    pass
            finally:
                self.clients.remove(websocket)

        return await websockets.serve(handler, self.host, self.port)

    async def broadcast(self, message: str):
        if not self.clients:
            return
        await asyncio.gather(*(client.send(message) for client in self.clients if client.open))
