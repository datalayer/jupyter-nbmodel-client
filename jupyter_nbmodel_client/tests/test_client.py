# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from jupyter_nbmodel_client import NbModelClient


def test_create_notebook_context_manager(jupyter_server, notebook_factory):
    server_url, token = jupyter_server
    path = "test.ipynb"

    notebook_factory(path)

    with NbModelClient(server_url=server_url, path=path, token=token) as notebook:
        dumped = notebook.as_dict()

    assert isinstance(dumped["cells"][0]["id"], str)
    del dumped["cells"][0]["id"]
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


def test_create_notebook_no_context_manager(jupyter_server, notebook_factory):
    server_url, token = jupyter_server
    path = "test.ipynb"

    notebook_factory(path)

    notebook = NbModelClient(server_url=server_url, path=path, token=token)
    notebook.start()
    try:
        dumped = notebook.as_dict()
    finally:
        notebook.stop()

    assert isinstance(dumped["cells"][0]["id"], str)
    del dumped["cells"][0]["id"]
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

