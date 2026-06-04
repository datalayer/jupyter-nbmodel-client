# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import typing as t

import requests

from jupyter_nbmodel_client.constants import REQUEST_TIMEOUT


def url_path_join(*pieces: str) -> str:
    """Join components of url into a relative url

    Use to prevent double slash when joining subpath. This will leave the
    initial and final / in place
    """
    initial = pieces[0].startswith("/")
    final = pieces[-1].endswith("/")
    stripped = [s.strip("/") for s in pieces]
    result = "/".join(s for s in stripped if s)
    if initial:
        result = "/" + result
    if final:
        result = result + "/"
    if result == "//":
        result = "/"
    return result


def fetch(
    request: str,
    token: str | None = None,
    **kwargs: t.Any,
) -> requests.Response:
    """Fetch a network resource as a context manager."""
    method = kwargs.pop("method", "GET")
    f = getattr(requests, method.lower())
    # Start from the JSON defaults and let caller-supplied headers override them, so extra
    # headers (e.g. Cookie/X-XSRFToken for cookie-protected servers) can be added without
    # dropping the defaults.
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Jupyter Nbmodel Client",
    }
    headers.update(kwargs.pop("headers", None) or {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if "timeout" not in kwargs:
        kwargs["timeout"] = REQUEST_TIMEOUT
    response = f(request, headers=headers, **kwargs)
    response.raise_for_status()
    return response
