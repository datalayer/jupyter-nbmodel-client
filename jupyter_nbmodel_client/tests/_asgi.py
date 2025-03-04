# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

import asyncio
import logging
import os

from hypercorn import Config
from hypercorn.asyncio import serve
from pycrdt_websocket import ASGIServer, WebsocketServer

# logging.basicConfig(level=logging.DEBUG)


async def main():
    websocket_server = WebsocketServer()
    app = ASGIServer(websocket_server)
    config = Config()
    port = os.environ.get("HYPERCORN_PORT", 1234)
    config.bind = [f"localhost:{port}"]
    async with websocket_server:
        await serve(app, config, mode="asgi")


if __name__ == "__main__":
    asyncio.run(main())
