import os
import typing as t
from collections.abc import MutableSequence
from functools import partial

import nbformat
import pycrdt
from jupyter_ydoc import YNotebook
from nbformat import NotebookNode, current_nbformat, versions

current_api = versions[current_nbformat]


class KernelClient(t.Protocol):
    def execute_interactive(
        self,
        code: str,
        silent: bool = False,
        store_history: bool = True,
        user_expressions: dict[str, t.Any] | None = None,
        allow_stdin: bool | None = None,
        stop_on_error: bool = True,
        timeout: float | None = None,
        output_hook: t.Callable | None = None,
        stdin_hook: t.Callable | None = None,
    ) -> dict[str, t.Any]:
        """Execute code in the kernel with low-level API

        Output will be redisplayed, and stdin prompts will be relayed as well.

        You can pass a custom output_hook callable that will be called
        with every IOPub message that is produced instead of the default redisplay.

        Parameters
        ----------
        code : str
            A string of code in the kernel's language.

        silent : bool, optional (default False)
            If set, the kernel will execute the code as quietly possible, and
            will force store_history to be False.

        store_history : bool, optional (default True)
            If set, the kernel will store command history.  This is forced
            to be False if silent is True.

        user_expressions : dict, optional
            A dict mapping names to expressions to be evaluated in the user's
            dict. The expression values are returned as strings formatted using
            :func:`repr`.

        allow_stdin : bool, optional (default self.allow_stdin)
            Flag for whether the kernel can send stdin requests to frontends.

        stop_on_error: bool, optional (default True)
            Flag whether to abort the execution queue, if an exception is encountered.

        timeout: float or None (default: None)
            Timeout to use when waiting for a reply

        output_hook: callable(msg)
            Function to be called with output messages.
            If not specified, output will be redisplayed.

        stdin_hook: callable(msg)
            Function to be called with stdin_request messages.
            If not specified, input/getpass will be called.

        Returns
        -------
        reply: dict
            The reply message for this request
        """
        ...


def output_hook(outputs: list[dict], ycell: pycrdt.Map, msg: dict) -> None:
    """Callback on execution request when an output is emitted.

    Args:
        outputs: A list of previously emitted outputs
        ycell: The cell being executed
        msg: The output message
    """
    # FIXME converge with output_hook in KernelClient
    msg_type = msg["header"]["msg_type"]
    if msg_type in ("display_data", "stream", "execute_result", "error"):
        # FIXME support for version
        output = nbformat.v4.output_from_msg(msg)
        outputs.append(output)

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
        # msg.content.wait is ignored - if true should clear at the next message
        # FIXME this is to fake some animation do we care? --> probably yes if output is captured
        # in the server
        outputs.clear()
        del ycell["outputs"][:]

    elif msg_type == "update_display_data":
        # FIXME
        ...


class NotebookModel(MutableSequence):
    """Notebook model.

    Its API is based on a mutable sequence of cells.
    """

    # FIXME add notebook metadata
    # FIXME add notebook state (TBC)

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

    def __setitem__(self, index: int, value: dict[str, t.Any]) -> None:
        self._doc.set_cell(index, value)

    def __len__(self) -> int:
        """Number of cells"""
        return self._doc.cell_number

    def add_code_cell(self, source: str, **kwargs) -> int:
        """Add a code cell

        Args:
            source: Code cell source

        Returns:
            Index of the newly added cell
        """
        cell = current_api.new_code_cell(source, **kwargs)

        self._doc.append_cell(cell)

        return len(self) - 1

    def add_markdown_cell(self, source: str, **kwargs) -> int:
        """Add a markdown cell

        Args:
            source: Markdown cell source

        Returns:
            Index of the newly added cell
        """
        cell = current_api.new_markdown_cell(source, **kwargs)

        self._doc.append_cell(cell)

        return len(self) - 1

    def add_raw_cell(self, source: str, **kwargs) -> int:
        """Add a raw cell

        Args:
            source: Raw cell source

        Returns:
            Index of the newly added cell
        """
        cell = current_api.new_raw_cell(source, **kwargs)

        self._doc.append_cell(cell)

        return len(self) - 1

    def execute_cell(self, index: int, kernel_client: KernelClient) -> dict:
        """Execute a cell given by its index with the provided kernel client.

        The outputs will directly be stored within the notebook model.

        Args:
            index: Index of the cell to be executed
            kernel_client: Kernel client to use

        Returns:
            Execution results {"execution_count": int | None, "status": str, "outputs": list[dict]}

            The outputs will follow the structure of nbformat outputs.
        """
        ycell = t.cast(pycrdt.Map, self._doc.ycells[index])
        source = ycell["source"].to_py()

        # Reset cell
        with ycell.doc.transaction():
            del ycell["outputs"][:]
            ycell["execution_count"] = None
            ycell["execution_state"] = "running"

        outputs = []
        reply = kernel_client.execute_interactive(
            source, output_hook=partial(output_hook, outputs, ycell), allow_stdin=False
        )

        reply_content = reply["content"]

        with ycell.doc.transaction():
            ycell["execution_count"] = reply_content.get("execution_count")
            ycell["execution_state"] = "idle"

        return {
            "execution_count": reply_content.get("execution_count"),
            "outputs": outputs,
            "status": reply_content["status"],
        }

    def insert(self, index: int, value: dict[str, t.Any]) -> None:
        """Insert a new cell at position index.

        Args:
            index: The position of the inserted cell
            value: A mapping describing the cell
        """
        ycell = self._doc.create_ycell(value)
        self._doc.ycells.insert(index, ycell)

    def _reset_y_model(self) -> None:
        """Reset the Y model."""
        self._doc = YNotebook()
