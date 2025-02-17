# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""This module provides a base class agent to interact with collaborative Jupyter notebook."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from enum import IntEnum
from logging import Logger
from typing import Any, Literal, cast
from uuid import uuid4

from pycrdt import ArrayEvent, Map, MapEvent

from .client import REQUEST_TIMEOUT, NbModelClient


def timestamp() -> int:
    """Return the current timestamp in milliseconds since epoch."""
    return int(datetime.now(timezone.utc).timestamp() * 1000.0)


class AIMessageType(IntEnum):
    """Type of AI agent message."""

    ERROR = -1
    """Error message."""
    ACKNOWLEDGE = 0
    """Prompt is being processed."""
    REPLY = 1
    """AI reply."""


# def _debug_print_changes(part: str, changes: Any) -> None:
#     print(f"{part}")

#     def print_change(changes):
#         if isinstance(changes, MapEvent):
#             print(f"{type(changes.target)} {changes.target} {changes.keys} {changes.path}")
#         elif isinstance(changes, ArrayEvent):
#             print(f"{type(changes.target)} {changes.target} {changes.delta} {changes.path}")
#         else:
#             print(changes)

#     if isinstance(changes, list):
#         for c in changes:
#             print_change(c)
#     else:
#         print_change(changes)


class BaseNbAgent(NbModelClient):
    """Base class to react to user prompt and notebook changes based on CRDT changes.

    Notes:
      - Agents are expected to extend this base class and override either
        - method:`async _on_user_prompt(self, cell_id: str, prompt: str, username: str | None = None) -> str | None`:
            Callback on user prompt, it may return an AI reply and must raise an error in case of failure
        - method:`async _on_cell_source_changes(self, cell_id: str, new_source: str, old_source: str, username: str | None = None) -> None`:
            Callback on cell source changes, it must raise an error in case of failure

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

    # FIXME implement username retrieval
    def __init__(
        self,
        websocket_url: str,
        path: str | None = None,
        username: str = os.environ.get("USER", "username"),
        timeout: float = REQUEST_TIMEOUT,
        log: Logger | None = None,
    ) -> None:
        super().__init__(websocket_url, path, username, timeout, log)
        self._doc_events: asyncio.Queue[dict] = asyncio.Queue()
        self._events_worker: asyncio.Task | None = None
        self._id = uuid4().hex  # ID for doc modification origin

    async def start(self) -> None:
        await super().start()
        self._events_worker = asyncio.create_task(self._process_doc_events())

    async def stop(self) -> None:
        await super().stop()
        if self._events_worker:
            self._events_worker.cancel()
            self._events_worker = None

        while not self._doc_events.empty():
            self._doc_events.get_nowait()

    async def __handle_cell_source_changes(
        self,
        cell_id: str,
        new_source: str,
        old_source: str,
        username: str | None = None,
    ) -> None:
        self._log.info("Process user [%s] cell [%s] source changes.", username, cell_id)
        with self._doc._ydoc.transaction(origin=self._id):
            # Acknowledge through awareness
            # await self.notify(
            #     AIMessageType.ACKNOWLEDGE,
            #     "AI has successfully processed the prompt.",
            #     cell_id=cell_id,
            # )
            try:
                await self._on_cell_source_changes(cell_id, new_source, old_source, username)
            except asyncio.CancelledError:
                raise
            except BaseException as e:
                error_message = f"Error while processing user prompt: {e!s}"
                self._log.error(error_message)
                # await self.notify(
                #     AIMessageType.ERROR, error_message, cell_id=cell_id
                # )
            else:
                self._log.info("AI processed successfully cell [%s] source changes.", cell_id)
                # await self.notify(
                #     AIMessageType.ACKNOWLEDGE,
                #     "AI has successfully processed the prompt.",
                #     cell_id=cell_id,
                # )

    async def __handle_user_prompt(
        self,
        cell_id: str,
        prompt_id: str,
        prompt: str,
        username: str | None = None,
        timestamp: int | None = None,
    ) -> None:
        self._log.info("Received user [%s] prompt [%s].", username, prompt_id)
        self._log.debug(
            "Prompt: timestamp [%d] / cell_id [%s] / prompt [%s]",
            timestamp,
            username,
            cell_id,
            prompt_id,
            prompt[:20],
        )

        with self._doc._ydoc.transaction(origin=self._id):
            # Acknowledge
            await self.save_ai_message(
                AIMessageType.ACKNOWLEDGE,
                "Requesting AI…",
                cell_id=cell_id,
                parent_id=prompt_id,
            )
            try:
                reply = await self._on_user_prompt(cell_id, prompt_id, prompt, username, timestamp)
            except asyncio.CancelledError:
                raise
            except BaseException as e:
                error_message = "Error while processing user prompt"
                self._log.error(error_message + " [%s].", prompt_id, exc_info=e)
                await self.save_ai_message(
                    AIMessageType.ERROR,
                    error_message + f": {e!s}",
                    cell_id=cell_id,
                    parent_id=prompt_id,
                )
            else:
                self._log.info("AI replied successfully to prompt [%s]: [%s]", prompt_id, reply)
                if reply is not None:
                    await self.save_ai_message(
                        AIMessageType.REPLY, reply, cell_id=cell_id, parent_id=prompt_id
                    )
                else:
                    await self.save_ai_message(
                        AIMessageType.ACKNOWLEDGE,
                        "AI has successfully processed the prompt.",
                        cell_id=cell_id,
                        parent_id=prompt_id,
                    )

    async def _process_doc_events(self) -> None:
        self._log.debug("Starting listening on document [%s] changes…", self.path)
        while True:
            try:
                event = await self._doc_events.get()
                event_type = event.pop("type")
                if event_type == "user":
                    await self.__handle_user_prompt(**event)
                if event_type == "source":
                    await self.__handle_cell_source_changes(**event)
            except asyncio.CancelledError:
                raise
            except BaseException as e:
                self._log.error("Error while processing document events: %s", exc_info=e)
            else:
                # Sleep to get a chance to propagate changes through the websocket
                await asyncio.sleep(0)

    def _on_notebook_changes(
        self,
        part: Literal["state"] | Literal["meta"] | Literal["cells"] | str,
        all_changes: Any,
    ) -> None:
        # _debug_print_changes(part, all_changes)

        if part == "cells":
            for changes in all_changes:
                transaction_origin = changes.transaction.origin()
                if transaction_origin == self._id:
                    continue
                else:
                    self._log.debug(
                        "Document changes from origin [%s] != agent origin [%s].",
                        transaction_origin,
                        self._id,
                    )
                path_length = len(changes.path)
                if path_length == 0:
                    # Change is on the cell list
                    for delta in changes.delta:
                        if "insert" in delta:
                            # New cells got added
                            for cell in delta["insert"]:
                                if "metadata" in cell:
                                    new_metadata = cell["metadata"]
                                    datalayer_ia = new_metadata.get("datalayer", {}).get("ai", {})
                                    prompts = datalayer_ia.get("prompts", [])
                                    prompt_ids = {prompt["id"] for prompt in prompts}
                                    new_prompts = prompt_ids.difference(
                                        message["parent_id"]
                                        for message in datalayer_ia.get("messages", [])
                                    )
                                    if new_prompts:
                                        for prompt in filter(
                                            lambda p: p.get("id") in new_prompts,
                                            prompts,
                                        ):
                                            self._doc_events.put_nowait(
                                                {
                                                    "type": "user",
                                                    "cell_id": cell["id"],
                                                    "prompt_id": prompt["id"],
                                                    "prompt": prompt["prompt"],
                                                    "username": prompt.get("user"),
                                                    "timestamp": prompt.get("timestamp"),
                                                }
                                            )
                                if "source" in cell:
                                    self._doc_events.put_nowait(
                                        {
                                            "type": "source",
                                            "cell_id": cell["id"],
                                            "new_source": cell["source"].to_py(),
                                            "old_source": "",
                                        }
                                    )
                elif path_length == 1:
                    # Change is on one cell
                    for key, change in changes.keys.items():
                        if key == "source":
                            if change["action"] == "add":
                                self._doc_events.put_nowait(
                                    {
                                        "type": "source",
                                        "cell_id": changes.target["id"],
                                        "new_source": change["newValue"],
                                        "old_source": change.get("oldValue", ""),
                                    }
                                )
                            elif change["action"] == "update":
                                self._doc_events.put_nowait(
                                    {
                                        "type": "source",
                                        "cell_id": changes.target["id"],
                                        "new_source": change["newValue"],
                                        "old_source": change["oldValue"],
                                    }
                                )
                            elif change["action"] == "delete":
                                self._doc_events.put_nowait(
                                    {
                                        "type": "source",
                                        "cell_id": changes.target["id"],
                                        "new_source": change.get("newValue", ""),
                                        "old_source": change["oldValue"],
                                    }
                                )
                        elif key == "metadata":
                            new_metadata = change.get("newValue", {})
                            datalayer_ia = new_metadata.get("datalayer", {}).get("ai", {})
                            prompts = datalayer_ia.get("prompts", [])
                            prompt_ids = {prompt["id"] for prompt in prompts}
                            new_prompts = prompt_ids.difference(
                                message["parent_id"] for message in datalayer_ia.get("messages", [])
                            )
                            if new_prompts and change["action"] in {"add", "update"}:
                                for prompt in filter(lambda p: p.get("id") in new_prompts, prompts):
                                    self._doc_events.put_nowait(
                                        {
                                            "type": "user",
                                            "cell_id": changes.target["id"],
                                            "prompt_id": prompt["id"],
                                            "prompt": prompt["prompt"],
                                            "username": prompt.get("user"),
                                            "timestamp": prompt.get("timestamp"),
                                        }
                                    )
                            # elif change["action"] == "delete":
                            #     ...
                        # elif key == "outputs":
                        #     # TODO
                        #     ...
                elif (
                    path_length == 2
                    and isinstance(changes.path[0], int)
                    and changes.path[1] == "metadata"
                ):
                    # Change in cell metadata
                    for key, change in changes.keys.items():
                        if key == "datalayer":
                            new_metadata = change.get("newValue", {})
                            datalayer_ia = new_metadata.get("ai", {})
                            prompts = datalayer_ia.get("prompts")
                            prompt_ids = {prompt["id"] for prompt in prompts}
                            new_prompts = prompt_ids.difference(
                                message["parent_id"] for message in datalayer_ia.get("messages", [])
                            )
                            if new_prompts and change["action"] in {"add", "update"}:
                                for prompt in filter(lambda p: p.get("id") in new_prompts, prompts):
                                    self._doc_events.put_nowait(
                                        {
                                            "type": "user",
                                            "cell_id": self._doc.ycells[changes.path[0]]["id"],
                                            "prompt_id": prompt["id"],
                                            "prompt": prompt["prompt"],
                                            "username": prompt.get("user"),
                                            "timestamp": prompt.get("timestamp"),
                                        }
                                    )
                            # elif change["action"] == "delete":
                            #     ...

        # elif part == "meta":
        #     # FIXME handle notebook metadata

    def _reset_y_model(self) -> None:
        try:
            self._doc.unobserve()
        except AttributeError:
            pass
        finally:
            super()._reset_y_model()
            self._doc.observe(self._on_notebook_changes)

    async def _on_user_prompt(
        self,
        cell_id: str,
        prompt_id: str,
        prompt: str,
        username: str | None = None,
        timestamp: int | None = None,
    ) -> str | None:
        username = username or self._username
        self._log.debug("New AI prompt sets by user [%s] in [%s]: [%s].", username, cell_id, prompt)

    async def _on_cell_source_changes(
        self,
        cell_id: str,
        new_source: str,
        old_source: str,
        username: str | None = None,
    ) -> None:
        username = username or self._username
        self._log.debug("New cell source sets by user [%s] in [%s].", username, cell_id)

    # async def _on_cell_outputs_changes(self, *args) -> None:
    #     print(args)

    def get_cell(self, cell_id: str) -> Map | None:
        """Find the cell with the given ID.

        If the cell cannot be found it will return ``None``.

        Args:
            cell_id: str
        Returns:
            Cell or None
        """
        for cell in self._doc.ycells:
            if cell["id"] == cell_id:
                return cast(Map, cell)

        return None

    def get_cell_index(self, cell_id: str) -> int:
        """Find the cell with the given ID.

        If the cell cannot be found it will return ``-1``.

        Args:
            cell_id: str
        Returns:
            Cell index or -1
        """
        for index, cell in enumerate(self._doc.ycells):
            if cell["id"] == cell_id:
                return index

        return -1

    async def save_ai_message(
        self,
        message_type: AIMessageType,
        message: str,
        cell_id: str = "",
        parent_id: str | None = None,
    ) -> None:
        """Update the document.

        If a message with the same ``parent_id`` already exists, it will be
        overwritten.

        Args:
            message_type: Type of message to insert in the document
            message: Message to insert
            cell_id: Cell targeted by the update; if empty, the notebook is the target
            parent_id: Parent message id
        """
        message_dict = {
            "parent_id": parent_id,
            "message": message,
            "type": message_type,
            "timestamp": timestamp(),
        }

        def set_message(metadata: Map, message: dict):
            if "datalayer" not in metadata:
                metadata["datalayer"] = {"ai": {"prompts": [], "messages": []}}
            elif "ai" not in metadata["datalayer"]:
                metadata["datalayer"] = {"ai": {"prompts": [], "messages": []}}
            elif "messages" not in metadata["datalayer"]["ai"]:
                metadata["datalayer"]["ai"] = {"messages": []}

            messages = list(
                filter(
                    lambda m: not m.get("parent_id") or m["parent_id"] != parent_id,
                    metadata["datalayer"]["ai"]["messages"],
                )
            )
            messages.append(message)
            metadata["datalayer"]["ai"]["messages"] = messages

            metadata["datalayer"] = metadata["datalayer"].copy()

        if cell_id:
            cell = self.get_cell(cell_id)
            if not cell:
                raise ValueError(f"Cell [{cell_id}] not found.")
            with self._doc._ydoc.transaction():
                if "metadata" not in cell:
                    cell["metadata"] = Map({"datalayer": {"ai": {"prompts": [], "messages": []}}})
                set_message(cell["metadata"], message_dict)
            self._log.debug("Add ai message in cell [%s] metadata: [%s].", cell_id, message_dict)

        else:
            notebook_metadata = self._doc._ymeta["metadata"]
            with self._doc._ydoc.transaction():
                set_message(notebook_metadata, message_dict)
            self._log.debug("Add ai message in notebook metadata: [%s].", cell_id, message_dict)

        # Sleep to get a chance to propagate the changes through the websocket
        await asyncio.sleep(0)

    # async def notify(self, message: str, cell_id: str = "") -> None:
    #     """Send a transient message to users.

    #     Args:
    #         message: Notification message
    #         cell_id: Cell targeted by the notification; if empty the notebook is the target
    #     """
    #     # Sleep to get a chance to propagate the changes through the websocket
    #     await asyncio.sleep(0)
