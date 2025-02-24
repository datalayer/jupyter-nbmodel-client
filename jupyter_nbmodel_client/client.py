# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import asyncio
import logging
import os

from pycrdt import (
    Subscription,
    TransactionEvent,
    YMessageType,
    YSyncMessageType,
    create_sync_message,
    create_update_message,
    handle_sync_message,
)
from websockets.asyncio.client import ClientConnection, connect

from .constants import DEFAULT_LOGGER, REQUEST_TIMEOUT
from .model import NotebookModel

# Default value taken from uvicorn: https://www.uvicorn.org/#command-line-options
# Note: the default size for Tornado is 10MB not 16MB
WEBSOCKETS_MAX_BODY_SIZE = int(os.environ.get("WEBSOCKETS_MAX_BODY_SIZE", 16 * 1024 * 1024))


class NbModelClient(NotebookModel):
    """Client to one Jupyter notebook model.

    Args:
        ws_url: Endpoint to connect to the collaborative Jupyter notebook.
        path: [optional] Notebook path relative to the server root directory; default None
        username: [optional] Client user name; default to environment variable USER
        timeout: [optional] Request timeout in seconds; default to environment variable REQUEST_TIMEOUT
        log: [optional] Custom logger; default local logger

    Examples:

    When connection to a Jupyter notebook server, you can leverage the get_jupyter_notebook_websocket_url
    helper:

    >>> from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url
    >>> client = NbModelClient(
    >>>     get_jupyter_notebook_websocket_url(
    >>>         "http://localhost:8888",
    >>>         "path/to/notebook.ipynb",
    >>>         "your-server-token"
    >>>     )
    >>> )
    """

    def __init__(
        self,
        websocket_url: str,
        path: str | None = None,
        username: str = os.environ.get("USER", "username"),
        timeout: float = REQUEST_TIMEOUT,
        log: logging.Logger | None = None,
        ws_max_body_size: int | None = None,
    ) -> None:
        super().__init__()
        self._ws_url = websocket_url
        self._path = path or websocket_url
        self._username = username
        self._timeout = timeout
        self._log = log or DEFAULT_LOGGER
        self._ws_max_body_size = ws_max_body_size or WEBSOCKETS_MAX_BODY_SIZE

        self.__synced = asyncio.Event()
        self.__websocket: ClientConnection | None = None
        self.__run: asyncio.Task | None = None
        self.__updates_queue: asyncio.Queue[bytes] = asyncio.Queue()

    @property
    def path(self) -> str:
        """Document path relative to the server root path."""
        return self._path

    @property
    def synced(self) -> bool:
        """Whether the model is synced or not."""
        return self.__synced.is_set()

    def __del__(self) -> None:
        if self.__run is not None:
            self.__run.cancel()

    async def __aenter__(self) -> "NbModelClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb) -> None:
        await self.stop()

    async def run(self) -> None:
        """Run the client."""
        if self.__websocket:
            RuntimeError("NbModelClient is already connected.")

        self._log.debug("Starting the websocket connection…")

        self.__websocket = await connect(
            self._ws_url,
            user_agent_header="Jupyter NbModel Client",
            logger=self._log,
            max_size=self._ws_max_body_size,
        )

        # Start listening to incoming message
        listener = asyncio.create_task(self._listen_to_websocket())

        # Start listening for model changes
        doc_update_subscription = self._doc.ydoc.observe(self._on_doc_update)
        forwarder = asyncio.create_task(self._forward_update())

        # Synchronize the model
        with self._lock:
            sync_message = create_sync_message(self._doc.ydoc)
        self._log.debug(
            "Sending SYNC_STEP1 message for document %s",
            self._path,
        )
        await self.__websocket.send(sync_message)

        try:
            # Wait forever and prevent the forwarder to be cancelled to avoid losing changes
            await asyncio.gather(listener, asyncio.shield(forwarder))
        finally:
            self._log.info("Stop the client…")

            # Stop listening to incoming messages
            if listener.cancel():
                await asyncio.wait([listener])

            # Stop listening for model changes
            try:
                self._doc.ydoc.unobserve(doc_update_subscription)
            except ValueError as e:
                if str(e) != "list.remove(x): x not in list":
                    self._log.error("Failed to unobserve the notebook model.", exc_info=e)

            # Try to propagate the last changes
            if not forwarder.done():
                if not self.__updates_queue.empty():
                    self._log.debug("Propagating the %s last changes…", self.__updates_queue.qsize())
                    await asyncio.shield(self.__updates_queue.join())

                # Stop forwarding changes
                if forwarder.cancel():
                    self._log.debug("Stop forwarding changes…")
                    await asyncio.wait([forwarder])
            else:
                while not self.__updates_queue.empty():
                    self.__updates_queue.get_nowait()

            # Reset the model
            self._reset_y_model()

            # Close the websocket
            if self.__websocket:
                try:
                    await self.__websocket.close()
                except BaseException as e:
                    self._log.error("Unable to close the websocket connection.", exc_info=e)
                    raise
                finally:
                    self._log.debug("Websocket connection closed.")
                    self.__websocket = None

    async def start(self) -> None:
        """Start the client."""
        if self.__run is not None:
            raise RuntimeError("The client is already running.")

        self.__run = asyncio.create_task(self.run())

        def callback(_: asyncio.Task) -> None:
            self.__run = None

        self.__run.add_done_callback(callback)

        self._log.debug("Waiting for model synchronization…")
        try:
            await asyncio.wait_for(self.__synced.wait(), REQUEST_TIMEOUT)
        except asyncio.TimeoutError:
            ...
        if not self.synced:
            self._log.warning("Document %s not yet synced.", self._path)

    async def stop(self) -> None:
        """Stop and reset the client."""
        if self.__run is not None and self.__run.cancel():
            await asyncio.wait([self.__run])

    async def wait_until_synced(self) -> None:
        """Wait until the model is synced."""
        await self.__synced.wait()

    async def _on_message(self, message: bytes) -> None:
        if message[0] == YMessageType.SYNC:
            self._log.debug(
                "Received %s message from document %s",
                YSyncMessageType(message[1]).name,
                self._path,
            )
            with self._lock:
                reply = handle_sync_message(message[1:], self._doc.ydoc)
            if message[1] == YSyncMessageType.SYNC_STEP2:
                self.__synced.set()
                self._fix_model()
            if reply is not None:
                self._log.debug(
                    "Sending SYNC_STEP2 message to document %s",
                    self._path,
                )
                await self.__websocket.send(reply)

    def _on_doc_update(self, event: TransactionEvent) -> None:
        if not self.__websocket:
            self._log.debug(
                "Ignoring document %s update prior to websocket connection.", self._path
            )
            return
        update = event.update
        message = create_update_message(update)
        self.__updates_queue.put_nowait(message)

    async def _listen_to_websocket(self) -> None:
        if self.__websocket is None:
            self._log.error("No websocket defined.")
            return

        while True:
            try:
                async for message in self.__websocket:
                    self._log.debug("Received message [%s]", message)
                    await self._on_message(message)
            except asyncio.CancelledError:
                raise
            except BaseException as e:
                self._log.error("Websocket client stopped.", exc_info=e)
                raise

    async def _forward_update(self) -> None:
        while True:
            try:
                message = await self.__updates_queue.get()
                self._log.debug("Forwarding message [%s]", message)
                await self.__websocket.send(message)
            except asyncio.CancelledError:
                raise
            except BaseException as e:
                self._log.error("Failed to forward update.", exc_info=e)
                raise
