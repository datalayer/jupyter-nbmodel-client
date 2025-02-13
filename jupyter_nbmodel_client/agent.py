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
    SUGGESTION = 1
    """Message suggesting a new cell content."""
    EXPLANATION = 2
    """Message explaining a content."""


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
        - method:`_on_user_prompt(self, cell_id: str, prompt: str, username: str | None = None)`:
            Callback on user prompt
        - method:`_on_cell_source_changes(self, cell_id: str, new_source: str, old_source: str, username: str | None = None):
            Callback on cell source changes
      - The agent can leverage the helper functions to send a reply to the user:
        - method:`save_ai_message(self, message_type: AIMessageType, message: str, cell_id: str = "", parent_id: str | None = None)`:
            Attach a message to the given cell (or to the notebook if no ``cell_id`` is provided).

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

    async def _process_doc_events(self) -> None:
        self._log.debug("Starting listening on document [%s] changes…", self.path)
        while True:
            try:
                event = await self._doc_events.get()
                event_type = event.pop("type")
                if event_type == "user":
                    self._on_user_prompt(**event)
                if event_type == "source":
                    self._on_cell_source_changes(**event)
            except asyncio.CancelledError:
                raise
            except BaseException as e:
                self._log.error("Error while processing document events: %s", e)

    def _on_notebook_changes(
        self,
        part: Literal["state"] | Literal["meta"] | Literal["cells"] | str,
        all_changes: Any,
    ) -> None:
        # _debug_print_changes(part, all_changes)

        if part == "cells":
            for changes in all_changes:
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

    def _on_user_prompt(
        self,
        cell_id: str,
        prompt_id: str,
        prompt: str,
        username: str | None = None,
        timestamp: int | None = None,
    ) -> None:
        username = username or self._username
        self._log.debug("New AI prompt sets by user [%s] in [%s]: [%s].", username, cell_id, prompt)

    def _on_cell_source_changes(
        self,
        cell_id: str,
        new_source: str,
        old_source: str,
        username: str | None = None,
    ) -> None:
        username = username or self._username
        self._log.debug("New cell source sets by user [%s] in [%s].", username, cell_id)

    # def _on_cell_outputs_changes(self, *args) -> None:
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

    def save_ai_message(
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
            if "metadata" not in cell:
                cell["metadata"] = Map({"datalayer": {"ai": {"prompts": [], "messages": []}}})
            set_message(cell["metadata"], message_dict)
            self._log.debug("Add ai message in cell [%s] metadata: [%s].", cell_id, message_dict)

        else:
            notebook_metadata = self._doc._ymeta["metadata"]
            set_message(notebook_metadata, message_dict)
            self._log.debug("Add ai message in notebook metadata: [%s].", cell_id, message_dict)

    # def notify(self, message: str, cell_id: str = "") -> None:
    #     """Send a transient message to users.

    #     Args:
    #         message: Notification message
    #         cell_id: Cell targeted by the notification; if empty the notebook is the target
    #     """
