import asyncio
import websockets
import base64

async def handler(websocket):
    try:
        base64_string = await websocket.recv()
        image_data = base64.b64decode(base64_string)
        with open("received_image.jpg", "wb") as f:
            f.write(image_data)

        await websocket.send("image recieved")

    except Exception as e:
        print(f"Error while recieving image: {e}")
        await websocket.send("server could not handle image")

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("Server running on ws://localhost:8765")
        await asyncio.Future()  

asyncio.run(main())
