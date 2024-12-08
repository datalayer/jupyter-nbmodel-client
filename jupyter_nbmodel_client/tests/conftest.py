# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import logging
import secrets
import signal
import socket
import typing as t
from contextlib import closing
from pathlib import Path
from subprocess import PIPE, Popen, TimeoutExpired

import nbformat
import pytest
import requests


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("localhost", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def print_stream(stream):
    for line in stream.split(b"\n"):
        print(line.decode())


@pytest.fixture
def jupyter_server(tmp_path) -> t.Generator[tuple[str, str], t.Any, t.Any]:
    """Start a Jupyter Server in a subprocess.

    Returns:
        A tuple (server_url, token)
    """
    port = find_free_port()
    token = secrets.token_hex(20)

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
        stdout=PIPE,
        stderr=PIPE,
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
        jp_server.send_signal(signal.SIGINT)
        jp_server.send_signal(signal.SIGINT)
        failed_to_terminate = True
        try:
            out, err = jp_server.communicate(timeout=10)
            failed_to_terminate = False
            print_stream(out)
            print_stream(err)
        except TimeoutExpired:
            if jp_server.poll() is None:
                jp_server.terminate()

        # if failed_to_terminate:
        #     print_stream(b"".join(iter(jp_server.stdout.readline, b"")))
        #     print_stream(b"".join(iter(jp_server.stderr.readline, b"")))


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
