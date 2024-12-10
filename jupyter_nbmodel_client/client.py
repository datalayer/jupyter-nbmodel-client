# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import logging
import typing as t
from threading import Event, Thread
from urllib.parse import quote, urlencode

from pycrdt import (
    Subscription,
    TransactionEvent,
    YMessageType,
    YSyncMessageType,
    create_sync_message,
    create_update_message,
    handle_sync_message,
)
from websocket import WebSocket, WebSocketApp

from .constants import HTTP_PROTOCOL_REGEXP, REQUEST_TIMEOUT
from .model import NotebookModel
from .utils import fetch, url_path_join

default_logger = logging.getLogger("jupyter_nbmodel_client")


class NbModelClient(NotebookModel):
    """Client to one Jupyter notebook model.

    Args:
        server_url: Jupyter Server URL
        token: Jupyter Server authentication token
        path: Notebook path relative to the server root directory
        timeout: Request timeout in seconds; default to environment variable REQUEST_TIMEOUT
        log: Custom logger
    """

    def __init__(
        self,
        server_url: str,
        path: str,
        token: str | None = None,
        timeout: float = REQUEST_TIMEOUT,
        log: logging.Logger | None = None,
    ) -> None:
        super().__init__()
        self._server_url = server_url
        self._token = token
        self._path = path
        self._timeout = timeout
        self._log = log or default_logger

        self.__connection_thread: Thread | None = None
        self.__connection_ready = Event()
        self.__synced = Event()
        self.__websocket: WebSocketApp | None = None
        self._doc_update_subscription: Subscription | None = None

    @property
    def connected(self) -> bool:
        """Whether the client is connected to the server or not."""
        return self.__connection_ready.is_set()

    @property
    def path(self) -> str:
        """Document path relative to the server root path."""
        return self._path

    @property
    def server_url(self) -> str:
        """Jupyter Server URL."""
        return self._server_url

    @property
    def synced(self) -> bool:
        """Whether the model is synced or not."""
        return self.__synced.is_set()

    def __del__(self) -> None:
        self.stop()

    def __enter__(self) -> "NbModelClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        self._log.info("Closing the context")
        self.stop()

    def _get_websocket_url(self) -> str:
        """Get the websocket URL."""
        self._log.debug("Request the session ID from the server.")
        # Fetch a session ID
        response = fetch(
            url_path_join(self._server_url, "/api/collaboration/session", quote(self._path)),
            self._token,
            method="PUT",
            json={"format": "json", "type": "notebook"},
            timeout=self._timeout,
        )

        response.raise_for_status()
        content = response.json()

        room_id = f"{content['format']}:{content['type']}:{content['fileId']}"

        base_ws_url = HTTP_PROTOCOL_REGEXP.sub("ws", self._server_url, 1)
        room_url = url_path_join(base_ws_url, "api/collaboration/room", room_id)
        params = {"sessionId": content["sessionId"]}
        if self._token is not None:
            params["token"] = self._token
        room_url += "?" + urlencode(params)
        return room_url

    def start(self) -> None:
        """Start the client."""
        if self.__websocket:
            RuntimeError("NbModelClient is already connected.")

        self._log.debug("Starting the websocket connection…")

        self.__websocket = WebSocketApp(
            self._get_websocket_url(),
            header=["User-Agent: Jupyter NbModel Client"],
            on_close=self._on_close,
            on_open=self._on_open,
            on_message=self._on_message,
        )
        self.__connection_thread = Thread(target=self._run_websocket)
        self.__connection_thread.start()

        self._doc_update_subscription = self._doc.ydoc.observe(self._on_doc_update)

        self.__connection_ready.wait(timeout=self._timeout)

        if not self.__connection_ready.is_set():
            self.stop()
            emsg = f"Unable to open a websocket connection to {self._server_url} within {self._timeout} s."
            raise TimeoutError(emsg)

        sync_message = create_sync_message(self._doc.ydoc)
        self._log.debug(
            "Sending SYNC_STEP1 message for document %s",
            self._path,
        )
        self.__websocket.send_bytes(sync_message)

        self._log.debug("Waiting for model synchronization…")
        self.__synced.wait(REQUEST_TIMEOUT)
        if not self.synced:
            self._log.warning("Document %s not yet synced.", self._path)

    def stop(self) -> None:
        """Stop and reset the client."""
        # Reset the notebook
        self._log.info("Disposing NbModelClient…")

        if self._doc_update_subscription:
            try:
                self._doc.ydoc.unobserve(self._doc_update_subscription)
            except ValueError as e:
                if str(e) != "list.remove(x): x not in list":
                    self._log.error("Failed to unobserve the notebook model.", exc_info=e)

        # Reset the model
        self._reset_y_model()

        # Close the websocket
        if self.__websocket:
            try:
                self.__websocket.close(timeout=self._timeout)
            except BaseException as e:
                self._log.error("Unable to close the websocket connection.", exc_info=e)
                raise
            finally:
                self.__websocket = None
                if self.__connection_thread:
                    self.__connection_thread.join(timeout=self._timeout)
                self.__connection_thread = None
                self.__connection_ready.clear()

    def _on_open(self, _: WebSocket) -> None:
        self._log.debug("Websocket connection opened.")
        self.__connection_ready.set()

    def _on_close(self, _: WebSocket, close_status_code: t.Any, close_msg: t.Any) -> None:
        msg = "Websocket connection is closed"
        if close_status_code or close_msg:
            self._log.info("%s: %s %s", msg, close_status_code, close_msg)
        else:
            self._log.debug(msg)
        self.__connection_ready.clear()

    def _on_message(self, websocket: WebSocket, message: bytes) -> None:
        if message[0] == YMessageType.SYNC:
            self._log.debug(
                "Received %s message from document %s",
                YSyncMessageType(message[1]).name,
                self._path,
            )
            reply = handle_sync_message(message[1:], self._doc.ydoc)
            if message[1] == YSyncMessageType.SYNC_STEP2:
                self.__synced.set()
            if reply is not None:
                self._log.debug(
                    "Sending SYNC_STEP2 message to document %s",
                    self._path,
                )
                websocket.send_bytes(reply)

    def _on_doc_update(self, event: TransactionEvent) -> None:
        if not self.__connection_ready.is_set():
            self._log.debug(
                "Ignoring document %s update prior to websocket connection.", self._path
            )
            return

        update = event.update
        message = create_update_message(update)
        t.cast(WebSocketApp, self.__websocket).send_bytes(message)

    def _run_websocket(self) -> None:
        if self.__websocket is None:
            self._log.error("No websocket defined.")
            return

        try:
            self.__websocket.run_forever(ping_interval=60, reconnect=5)
        except ValueError as e:
            self._log.error(
                "Unable to open websocket connection with %s",
                self.__websocket.url,
                exc_info=e,
            )
        except BaseException as e:
            self._log.error("Websocket listener thread stopped.", exc_info=e)
