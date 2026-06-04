# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

import jupyter_nbmodel_client.helpers as helpers_module
import jupyter_nbmodel_client.utils as utils_module


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        ...

    def json(self):
        return self._payload


def test_fetch__merges_custom_headers_over_defaults(monkeypatch):
    captured_headers = {}

    def fake_put(request, headers=None, **kwargs):
        captured_headers.update(headers)
        return _FakeResponse({})

    monkeypatch.setattr(utils_module.requests, "put", fake_put)

    utils_module.fetch(
        "http://localhost/api",
        token="secret-token",
        method="PUT",
        headers={"Cookie": "session=abc", "Accept": "text/plain"},
    )

    # Caller header overrides the default Accept, extra headers are added,
    # and the remaining defaults plus the token are preserved.
    assert captured_headers["Accept"] == "text/plain"
    assert captured_headers["Cookie"] == "session=abc"
    assert captured_headers["Content-Type"] == "application/json"
    assert captured_headers["Authorization"] == "Bearer secret-token"


def test_get_jupyter_notebook_websocket_url__forwards_headers(monkeypatch):
    captured = {}

    def fake_fetch(request, token=None, **kwargs):
        captured["headers"] = kwargs.get("headers")
        captured["token"] = token
        return _FakeResponse(
            {
                "format": "json",
                "type": "notebook",
                "fileId": "file-id",
                "sessionId": "session-id",
            }
        )

    monkeypatch.setattr(helpers_module, "fetch", fake_fetch)

    room_url = helpers_module.get_jupyter_notebook_websocket_url(
        "http://localhost:8888",
        "notebook.ipynb",
        headers={"Cookie": "session=abc", "X-XSRFToken": "xsrf"},
    )

    assert captured["headers"] == {"Cookie": "session=abc", "X-XSRFToken": "xsrf"}
    assert room_url.startswith("ws://localhost:8888/api/collaboration/room/")
    assert "sessionId=session-id" in room_url
