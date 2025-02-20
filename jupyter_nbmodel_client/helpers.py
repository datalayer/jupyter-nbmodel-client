# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import logging
from urllib.parse import quote, urlencode

from .constants import DEFAULT_LOGGER, HTTP_PROTOCOL_REGEXP, REQUEST_TIMEOUT
from .utils import fetch, url_path_join


def get_jupyter_notebook_websocket_url(
    server_url: str,
    path: str,
    token: str | None = None,
    timeout: float = REQUEST_TIMEOUT,
    log: logging.Logger | None = None,
) -> str:
    """Get the websocket endpoint to connect to a collaborative Jupyter notebook.

    Args:
        server_url: Jupyter Server URL
        path: Notebook path relative to the server root directory
        token: [optional] Jupyter Server authentication token; default None
        timeout: [optional] Request timeout in seconds; default to environment variable REQUEST_TIMEOUT
        log: [optional] Custom logger; default local logger

    Returns:
        The websocket endpoint
    """
    (log or DEFAULT_LOGGER).debug("Request the session ID from the Jupyter server.")
    # Fetch a session ID
    response = fetch(
        url_path_join(server_url, "/api/collaboration/session", quote(path)),
        token,
        method="PUT",
        json={"format": "json", "type": "notebook"},
        timeout=timeout,
    )

    response.raise_for_status()
    content = response.json()

    room_id = f"{content['format']}:{content['type']}:{content['fileId']}"

    base_ws_url = HTTP_PROTOCOL_REGEXP.sub("ws", server_url, 1)
    room_url = url_path_join(base_ws_url, "api/collaboration/room", room_id)
    params = {"sessionId": content["sessionId"]}
    if token is not None:
        params["token"] = token
    room_url += "?" + urlencode(params)
    return room_url


def get_datalayer_websocket_url(
    server_url: str,
    room_id: str,
    token: str | None = None,
    timeout: float = REQUEST_TIMEOUT,
    log: logging.Logger | None = None,
) -> str:
    """Get the websocket endpoint to connect to a collaborative notebook
    on Datalayer spacer.

    Args:
        server_url: Datalayer Server URL
        room_id: Document ID to connect to
        token: [optional] Datalayer Server JWT authentication token; default None
        timeout: [optional] Request timeout in seconds; default to environment variable REQUEST_TIMEOUT
        log: [optional] Custom logger; default local logger

    Returns:
        The websocket endpoint
    """
    DATALAYER_ROOMS_ENDPOINT = "/api/spacer/v1/rooms"
    (log or DEFAULT_LOGGER).debug("Request the session ID from the Datalayer server.")
    # Fetch a session ID
    response = fetch(
        url_path_join(server_url, DATALAYER_ROOMS_ENDPOINT, room_id),
        token,
        method="GET",
        timeout=timeout,
    )

    response.raise_for_status()
    content = response.json()
    session_id = content.get("sessionId") if content.get("success", False) else ""

    if not session_id:
        emsg = f"Failed to fetch session_id: {content.get('message', '')}"
        raise ValueError(emsg)

    base_ws_url = HTTP_PROTOCOL_REGEXP.sub("ws", server_url, 1)
    room_url = url_path_join(base_ws_url, DATALAYER_ROOMS_ENDPOINT, room_id)
    params = {"sessionId": session_id}
    if token is not None:
        params["token"] = token
    room_url += "?" + urlencode(params)
    return room_url
