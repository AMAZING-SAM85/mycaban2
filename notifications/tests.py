# test_websocket.py
import websockets
import asyncio

async def test():
    uri = "ws://localhost:8000/ws/notifications/"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            print(f"Received: {message}")

asyncio.get_event_loop().run_until_complete(test())