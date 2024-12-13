# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

import os

import pytest

from jupyter_nbmodel_client import NbModelClient

jupyter_kernel_client = pytest.importorskip("jupyter_kernel_client")


def test_execute_notebook_context_manager(notebook_factory):
# def test_execute_notebook_context_manager(jupyter_server, notebook_factory):
    # server_url, token = jupyter_server
    server_url = "http://localhost:" + os.environ["JUPYTER_SERVER_PORT"]
    token = os.environ["JUPYTER_SERVER_TOKEN"]

    path = "test.ipynb"

    notebook_factory(path)

    with jupyter_kernel_client.KernelClient(server_url=server_url, token=token) as kernel:
        with NbModelClient(server_url=server_url, path=path, token=token) as notebook:
            result = notebook.execute_cell(
                notebook.add_code_cell("print('hello world')"), kernel_client=kernel, timeout=2.0
            )
            dumped = notebook.as_dict()

    for cell in dumped["cells"]:
        if "id" in cell:
            del cell["id"]

    assert result == {
        "execution_count": 1,
        "outputs": [{"name": "stdout", "output_type": "stream", "text": "hello world\n"}],
        "status": "ok",
    }
    assert dumped == {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {
                    "trusted": True,
                },
                "outputs": [],
                "source": "",
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [
                    {
                        "name": "stdout",
                        "output_type": "stream",
                        "text": "hello world\n",
                    },
                ],
                "source": "print('hello world')",
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "",
                "name": "",
            },
            "language_info": {
                "name": "",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
