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

async def test_set_cell_source(jupyter_server, notebook_factory):
    server_url, token = jupyter_server
    path = "test.ipynb"

    notebook_factory(path)

    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        index = notebook.add_code_cell("print('hello')")
        cell_source = notebook._doc._ycells[index]["source"]
        notebook.set_cell_source(index, "1 + 1 != 3")
        assert cell_source.to_py() == "1 + 1 != 3"


async def test_save_on_disconnect(jupyter_server, notebook_factory):
    """Test that changes are saved when disconnecting quickly.
    
    This test verifies the fix for the issue where rapid disconnection
    could cause unsaved changes to be lost from the message queue.
    """
    server_url, token = jupyter_server
    path = "test_disconnect.ipynb"

    notebook_factory(path)

    # Connect and make multiple rapid changes
    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        # Quickly add multiple cells
        for i in range(10):
            notebook.add_code_cell(f"print({i})")
        # Exit context immediately (triggers close)

    # Reconnect and verify all changes were saved
    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook2:
        # Should have original empty cell + 10 new cells = 11 total
        assert len(notebook2) == 11
        # Verify content of the cells
        for i in range(10):
            cell = notebook2[i + 1]  # Skip first empty cell
            assert cell["source"] == f"print({i})"
            assert cell["cell_type"] == "code"