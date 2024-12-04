import os
import typing as t
from collections.abc import MutableSequence
from functools import partial

import nbformat
import pycrdt
from jupyter_ydoc import YNotebook
from nbformat import NotebookNode, current_nbformat, versions

current_api = versions[current_nbformat]


def output_hook(ycell: pycrdt.Map, msg: dict) -> None:
    """Callback on execution request when an output is emitted.

    Args:
        outputs: A list of previously emitted outputs
        ycell: The cell being executed
        msg: The output message
    """
    msg_type = msg["header"]["msg_type"]
    if msg_type in ("display_data", "stream", "execute_result", "error"):
        # FIXME support for version
        output = nbformat.v4.output_from_msg(msg)

        if ycell is not None:
            cell_outputs = ycell["outputs"]
            if msg_type == "stream":
                with cell_outputs.doc.transaction():
                    text = output["text"]

                    # FIXME Logic is quite complex at https://github.com/jupyterlab/jupyterlab/blob/7ae2d436fc410b0cff51042a3350ba71f54f4445/packages/outputarea/src/model.ts#L518
                    if text.endswith((os.linesep, "\n")):
                        text = text[:-1]

                    if (not cell_outputs) or (cell_outputs[-1]["name"] != output["name"]):
                        output["text"] = [text]
                        cell_outputs.append(output)
                    else:
                        last_output = cell_outputs[-1]
                        last_output["text"].append(text)
                        cell_outputs[-1] = last_output
            else:
                with cell_outputs.doc.transaction():
                    cell_outputs.append(output)

    elif msg_type == "clear_output":
        # FIXME msg.content.wait - if true should clear at the next message
        del ycell["outputs"][:]

    elif msg_type == "update_display_data":
        # FIXME
        ...


class NotebookModel(MutableSequence):
    def __init__(self) -> None:
        self._doc = YNotebook()

    def __delitem__(self, index: int) -> NotebookNode:
        raw_ycell = self._doc.ycells.pop(index)
        cell: dict[str, t.Any] = raw_ycell.to_py()
        nbcell = NotebookNode(**cell)
        return nbcell

    def __getitem__(self, index: int) -> NotebookNode:
        raw_ycell = self._doc.ycells[index]
        cell = raw_ycell.to_py()
        nbcell = NotebookNode(**cell)
        return nbcell

    def __setitem__(self, index: int, value: NotebookNode) -> None:
        self._doc.set_cell(index, value)

    def __len__(self) -> int:
        """Number of cells"""
        return self._doc.cell_number

    def add_code_cell(self, source: str, **kwargs) -> int:
        cell = current_api.new_code_cell(source, **kwargs)

        self._doc.append_cell(cell)

        return len(self) - 1

    def add_markdown_cell(self, source: str, **kwargs) -> int:
        cell = current_api.new_markdown_cell(source, **kwargs)

        self._doc.append_cell(cell)

        return len(self) - 1

    def add_raw_cell(self, source: str, **kwargs) -> int:
        cell = current_api.new_raw_cell(source, **kwargs)

        self._doc.append_cell(cell)

        return len(self) - 1

    def _reset_y_model(self) -> None:
        """Reset the Y model."""
        self._doc = YNotebook()

    def execute_cell(self, index: int, kernel_client: t.Any) -> None:
        ycell = t.cast(pycrdt.Map, self._doc.ycells[index])
        source = ycell["source"].to_py()

        # Reset cell
        with ycell.doc.transaction():
            del ycell["outputs"][:]
            ycell["execution_count"] = None
            ycell["execution_state"] = "running"

        reply = kernel_client.execute_interactive(
            source, output_hook=partial(output_hook, ycell), allow_stdin=False
        )

        reply_content = reply["content"]

        with ycell.doc.transaction():
            ycell["execution_count"] = reply_content.get("execution_count")
            ycell["execution_state"] = "idle"

    def insert(self, index: int, value: NotebookNode) -> None:
        ycell = self._doc.create_ycell(value)
        self._doc.ycells.insert(index, ycell)
