# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

import threading

import nbformat
import pytest
from jupyter_ydoc import YNotebook

from jupyter_nbmodel_client.model import save_in_notebook_hook

# Without jupyter_kernel_client, model.py falls back to an output hook built on
# ``nbformat.output_from_msg``, which never emits transient information.
pytest.importorskip("jupyter_kernel_client")


def _new_ycell():
    ydoc = YNotebook()
    ydoc.set(nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("display(obj)")]))
    return ydoc, ydoc.ycells[0]


def _display_msg(value, display_id=None, msg_type="display_data"):
    content = {"data": {"text/plain": value}, "metadata": {}}
    if display_id is not None:
        content["transient"] = {"display_id": display_id}
    return {"header": {"msg_type": msg_type}, "content": content}


@pytest.mark.parametrize("display_id", ["abc123", None])
def test_save_in_notebook_hook__does_not_save_transient(display_id):
    """Transient information is kernel protocol; the document must stay nbformat valid."""
    ydoc, ycell = _new_ycell()
    outputs: list[dict] = []

    save_in_notebook_hook(threading.Lock(), outputs, ycell, 0, _display_msg("v1", display_id))

    document = ydoc.get()
    assert "transient" not in document["cells"][0]["outputs"][0]
    nbformat.validate(nbformat.from_dict(document))
    # The kernel client still reads it back for update_display_data matching.
    assert "transient" in outputs[0]


def test_save_in_notebook_hook__update_display_data_updates_output_in_place():
    """Keeping transient out of the document must not break display_id matching."""
    ydoc, ycell = _new_ycell()
    outputs: list[dict] = []

    save_in_notebook_hook(threading.Lock(), outputs, ycell, 0, _display_msg("v1", "abc123"))
    save_in_notebook_hook(
        threading.Lock(), outputs, ycell, 0, _display_msg("v2", "abc123", "update_display_data")
    )

    saved_outputs = ydoc.get()["cells"][0]["outputs"]
    assert len(saved_outputs) == 1
    assert saved_outputs[0]["data"] == {"text/plain": "v2"}
