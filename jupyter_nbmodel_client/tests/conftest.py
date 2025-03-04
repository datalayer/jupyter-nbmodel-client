# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import io
import logging
import secrets
import signal
import socket
import sys
import typing as t
from contextlib import closing
from pathlib import Path
from subprocess import PIPE, Popen, TimeoutExpired

import nbformat
import pytest
import requests

# logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def unused_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("localhost", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def print_stream(stream):
    for line in stream.split(b"\n"):
        print(line.decode())


@pytest.fixture
def jupyter_server(tmp_path: Path, unused_port) -> t.Generator[tuple[str, str], t.Any, t.Any]:
    """Start a Jupyter Server in a subprocess.

    Returns:
        A tuple (server_url, token)
    """
    port = unused_port
    token = secrets.token_hex(20)

    stdout = tmp_path / "stdout.log"
    stderr = tmp_path / "stderr.log"

    with stdout.open("wb") as out, stderr.open("wb") as err:
        jp_server = Popen(
            [
                "jupyter-server",
                "--port",
                str(port),
                "--IdentityProvider.token",
                token,
                "--debug",
                "--ServerApp.open_browser",
                "False",
                "--SQLiteYStore.db_path",
                str(tmp_path / "crdt.db"),
                "--BaseFileIdManager.root_dir",
                str(tmp_path),
                "--BaseFileIdManager.db_path",
                str(tmp_path / "file_id.db"),
                "--BaseFileIdManager.db_journal_mode",
                "OFF",
                str(tmp_path),
            ],
            stdout=out,
            stderr=err,
        )

        starting = True
        while starting:
            try:
                ans = requests.get(f"http://localhost:{port}/api", timeout=1)
                if ans.status_code == 200:
                    logging.debug("Server ready at http://localhost:%s", port)
                    break
            except requests.RequestException:
                ...
        try:
            yield (f"http://localhost:{port}", token)
        finally:
            # Send twice Keyboard interrupt to stop the server
            jp_server.send_signal(signal.SIGINT)
            jp_server.send_signal(signal.SIGINT)
            try:
                jp_server.communicate(timeout=10)
            except TimeoutExpired:
                if jp_server.poll() is None:
                    jp_server.terminate()
    try:
        print_stream(out.read())
    except io.UnsupportedOperation:
        ...
    try:
        print_stream(err.read())
    except io.UnsupportedOperation:
        ...


@pytest.fixture
def notebook_factory(tmp_path):
    """Creates a notebook in the test's home directory."""

    def factory(path: str, content: str | None = None) -> None:
        # Check that the notebook has the correct file extension.
        path_ = Path(path)
        if path_.suffix != ".ipynb":
            msg = "File extension for notebook must be .ipynb"
            raise ValueError(msg)

        nbpath = tmp_path / path_
        # If the notebook path has a parent directory, make sure it's created.
        nbpath.parent.mkdir(parents=True, exist_ok=True)

        # Create a notebook string and write to file.
        if content is None:
            nb = nbformat.v4.new_notebook()
            content = nbformat.writes(nb, version=4)

        nbpath.write_text(content)

    return factory


@pytest.fixture
def ws_server(unused_port, monkeypatch):
    monkeypatch.setenv("HYPERCORN_PORT", str(unused_port))

    HERE = Path(__file__).parent

    ws_server = Popen(
        [
            sys.executable,
            str(HERE / "_asgi.py"),
        ],
        stderr=PIPE,
    )

    while True:
        log = ws_server.stderr.readline()
        if b"Running on " in log:
            break

    try:
        yield f"ws://localhost:{unused_port}"
    finally:
        ws_server.send_signal(signal.SIGINT)
        ws_server.communicate(timeout=10)
        if ws_server.poll() is None:
            ws_server.terminate()
