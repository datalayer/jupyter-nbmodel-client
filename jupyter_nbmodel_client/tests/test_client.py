# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from jupyter_nbmodel_client import NbModelClient, get_jupyter_notebook_websocket_url


async def test_create_notebook_context_manager(jupyter_server, notebook_factory):
    server_url, token = jupyter_server
    path = "test.ipynb"

    notebook_factory(path)

    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
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


async def test_create_notebook_no_context_manager(jupyter_server, notebook_factory):
    server_url, token = jupyter_server
    path = "test.ipynb"

    notebook_factory(path)

    notebook = NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    )
    await notebook.start()
    try:
        dumped = notebook.as_dict()
    finally:
        await notebook.stop()

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
