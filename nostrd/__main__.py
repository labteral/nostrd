from .relay import handler
import websockets
import asyncio


async def main():
    async with websockets.serve(handler, '0.0.0.0', 80):
        await asyncio.Future()  # run forever


asyncio.run(main())
