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


async def test_insert_cell_code(jupyter_server, notebook_factory):
    """Test inserting a code cell using the unified insert_cell method."""
    server_url, token = jupyter_server
    path = "test_insert_cell.ipynb"

    notebook_factory(path)

    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        # Insert a code cell at index 0
        notebook.insert_cell(0, "import numpy as np", cell_type="code")
        
        # Verify the cell was inserted correctly
        assert len(notebook) == 2  # Original empty cell + new cell
        cell = notebook[0]
        assert cell["cell_type"] == "code"
        assert cell["source"] == "import numpy as np"


async def test_insert_cell_markdown(jupyter_server, notebook_factory):
    """Test inserting a markdown cell using the unified insert_cell method."""
    server_url, token = jupyter_server
    path = "test_insert_markdown.ipynb"

    notebook_factory(path)

    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        # Insert a markdown cell
        notebook.insert_cell(0, "# Hello World", cell_type="markdown")
        
        # Verify the cell was inserted correctly
        assert len(notebook) == 2
        cell = notebook[0]
        assert cell["cell_type"] == "markdown"
        assert cell["source"] == "# Hello World"


async def test_insert_cell_raw(jupyter_server, notebook_factory):
    """Test inserting a raw cell using the unified insert_cell method."""
    server_url, token = jupyter_server
    path = "test_insert_raw.ipynb"

    notebook_factory(path)

    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        # Insert a raw cell
        notebook.insert_cell(0, "Raw content", cell_type="raw")
        
        # Verify the cell was inserted correctly
        assert len(notebook) == 2
        cell = notebook[0]
        assert cell["cell_type"] == "raw"
        assert cell["source"] == "Raw content"


async def test_insert_cell_at_end(jupyter_server, notebook_factory):
    """Test inserting cells at the end using index -1."""
    server_url, token = jupyter_server
    path = "test_insert_end.ipynb"

    notebook_factory(path)

    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        # Insert cells at the end
        notebook.insert_cell(-1, "print('first')", cell_type="code")
        notebook.insert_cell(-1, "# Title", cell_type="markdown")
        notebook.insert_cell(-1, "raw text", cell_type="raw")
        
        # Verify cells were added at the end
        assert len(notebook) == 4
        assert notebook[-3]["source"] == "print('first')"
        assert notebook[-2]["source"] == "# Title"
        assert notebook[-1]["source"] == "raw text"


async def test_insert_cell_with_metadata(jupyter_server, notebook_factory):
    """Test inserting a cell with metadata."""
    server_url, token = jupyter_server
    path = "test_insert_metadata.ipynb"

    notebook_factory(path)

    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        # Insert cell with metadata
        notebook.insert_cell(
            0, 
            "print('tagged')", 
            cell_type="code",
            metadata={"tags": ["important", "test"]}
        )
        
        # Verify metadata was set
        cell = notebook[0]
        assert "tags" in cell["metadata"]
        assert cell["metadata"]["tags"] == ["important", "test"]


async def test_insert_cell_invalid_type(jupyter_server, notebook_factory):
    """Test that inserting with invalid cell type raises ValueError."""
    server_url, token = jupyter_server
    path = "test_invalid_type.ipynb"

    notebook_factory(path)

    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        # Try to insert with invalid cell type
        try:
            notebook.insert_cell(0, "content", cell_type="invalid")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid cell type" in str(e)


async def test_insert_cell_invalid_index(jupyter_server, notebook_factory):
    """Test that inserting with invalid index raises IndexError."""
    server_url, token = jupyter_server
    path = "test_invalid_index.ipynb"

    notebook_factory(path)

    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        # Try to insert with invalid index
        try:
            notebook.insert_cell(100, "content", cell_type="code")
            assert False, "Should have raised IndexError"
        except IndexError as e:
            assert "outside valid range" in str(e)


async def test_delete_cell(jupyter_server, notebook_factory):
    """Test deleting a cell and verifying it returns the cell content."""
    server_url, token = jupyter_server
    path = "test_delete_cell.ipynb"

    notebook_factory(path)

    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        # Add some cells
        notebook.add_code_cell("print('first')")
        notebook.add_markdown_cell("# Title")
        notebook.add_code_cell("print('third')")
        
        initial_length = len(notebook)
        assert initial_length == 4  # 1 original + 3 added
        
        # Delete the markdown cell (index 2)
        deleted_cell = notebook.delete_cell(2)
        
        # Verify the deleted cell content
        assert deleted_cell["cell_type"] == "markdown"
        assert deleted_cell["source"] == "# Title"
        
        # Verify the notebook length decreased
        assert len(notebook) == initial_length - 1
        
        # Verify remaining cells
        assert notebook[1]["source"] == "print('first')"
        assert notebook[2]["source"] == "print('third')"


async def test_delete_cell_out_of_range(jupyter_server, notebook_factory):
    """Test that deleting with invalid index raises IndexError."""
    server_url, token = jupyter_server
    path = "test_delete_invalid.ipynb"

    notebook_factory(path)

    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        # Try to delete with invalid index
        try:
            notebook.delete_cell(100)
            assert False, "Should have raised IndexError"
        except IndexError as e:
            assert "out of range" in str(e)


async def test_delete_cell_negative_index(jupyter_server, notebook_factory):
    """Test that deleting with negative index raises IndexError."""
    server_url, token = jupyter_server
    path = "test_delete_negative.ipynb"

    notebook_factory(path)

    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        # Try to delete with negative index
        try:
            notebook.delete_cell(-1)
            assert False, "Should have raised IndexError"
        except IndexError as e:
            assert "out of range" in str(e)


async def test_insert_raw_cell(jupyter_server, notebook_factory):
    """Test inserting a raw cell using insert_raw_cell method."""
    server_url, token = jupyter_server
    path = "test_insert_raw_cell.ipynb"

    notebook_factory(path)

    async with NbModelClient(
        get_jupyter_notebook_websocket_url(server_url=server_url, path=path, token=token)
    ) as notebook:
        # Insert a raw cell using the specific method
        notebook.insert_raw_cell(0, "Raw text content")
        
        # Verify the cell was inserted correctly
        assert len(notebook) == 2
        cell = notebook[0]
        assert cell["cell_type"] == "raw"
        assert cell["source"] == "Raw text content"