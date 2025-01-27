# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url


def test_create_notebook_context_manager(jupyter_server, notebook_factory):
    server_url, token = jupyter_server
    path = "test.ipynb"

    notebook_factory(path)

    with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        dumped = notebook.as_dict()

    assert dumped == {
        "cells": [],
        "metadata": {},
        "nbformat": 0,
        "nbformat_minor": 0,
    }


def test_create_notebook_no_context_manager(jupyter_server, notebook_factory):
    server_url, token = jupyter_server
    path = "test.ipynb"

    notebook_factory(path)

    notebook = NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    )
    notebook.start()
    try:
        dumped = notebook.as_dict()
    finally:
        notebook.stop()

    assert dumped == {
        "cells": [],
        "metadata": {},
        "nbformat": 0,
        "nbformat_minor": 0,
    }
