# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

from __future__ import annotations

import threading
import typing as t
import warnings
from collections.abc import MutableSequence
from copy import deepcopy
from functools import partial
from uuid import uuid4

import pycrdt
from jupyter_ydoc import YNotebook
from nbformat import NotebookNode, current_nbformat, versions

current_api = versions[current_nbformat]

try:
    from jupyter_kernel_client.client import output_hook
except ImportError:

    def output_hook(outputs: list[dict[str, t.Any]], message: dict[str, t.Any]) -> set[int]:
        # This is a very simple version - we highly recommend
        # having `jupyter_kernel_client` installed
        msg_type = message["header"]["msg_type"]
        if msg_type == "update_display_data":
            message = deepcopy(message)
            msg_type = "display_data"
            message["header"]["msg_type"] = msg_type

        if msg_type in ("display_data", "stream", "execute_result", "error"):
            output = current_api.output_from_msg(message)
            index = len(outputs)
            outputs.append(output)
            return {index}

        elif msg_type == "clear_output":
            size = len(outputs)
            outputs.clear()
            return set(range(size))

        return set()


class KernelClient(t.Protocol):
    """Interface to be implemented by the kernel client."""

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

        Args:
            code: A string of code in the kernel's language.
            silent: optional (default False)
                If set, the kernel will execute the code as quietly possible, and
                will force store_history to be False.
            store_history: optional (default True)
                If set, the kernel will store command history.  This is forced
                to be False if silent is True.
            user_expressions: optional
                A dict mapping names to expressions to be evaluated in the user's
                dict. The expression values are returned as strings formatted using
                :func:`repr`.
            allow_stdin: optional (default self.allow_stdin)
                Flag for whether the kernel can send stdin requests to frontends.
            stop_on_error: optional (default True)
                Flag whether to abort the execution queue, if an exception is encountered.
            timeout: (default None)
                Timeout to use when waiting for a reply
            output_hook: Function to be called with output messages.
            stdin_hook: Function to be called with stdin_request messages.

        Returns:
            The reply message for this request
        """
        ...


def save_in_notebook_hook(
    lock: threading.Lock, outputs: list[dict], ycell: pycrdt.Map, origin: int, msg: dict
) -> None:
    """Callback on execution request when an output is emitted.

    Args:
        outputs: A list of previously emitted outputs
        ycell: The cell being executed
        origin: Document modification origin
        msg: The output message
    """
    indexes = output_hook(outputs, msg)
    cell_outputs = t.cast(pycrdt.Array, ycell["outputs"])
    if len(indexes) == len(cell_outputs):
        with lock:
            with cell_outputs.doc.transaction(origin=origin):
                cell_outputs.clear()
                cell_outputs.extend(outputs)
    else:
        with lock:
            with cell_outputs.doc.transaction(origin=origin):
                for index in indexes:
                    if index >= len(cell_outputs):
                        cell_outputs.append(outputs[index])
                    else:
                        cell_outputs[index] = outputs[index]


class NotebookModel(MutableSequence):
    """Notebook model.

    Its API is based on a mutable sequence of cells.
    """

    # FIXME add notebook state (TBC)
    # FIXME add API to clear code cell; aka execution count and outputs

    def __init__(self) -> None:
        self._doc: YNotebook
        self._lock = threading.Lock()
        """Lock to prevent updating the document in multiple threads simultaneously.

        That may induce a Panic error; see https://github.com/datalayer/jupyter-nbmodel-client/issues/12
        """
        self._changes_origin = hash(
            uuid4().hex
        )  # hashed ID for doc modification origin - as pycrdt 0.10 return hashed origin and hash(hashed) == hashed

        # Initialize _doc
        self._reset_y_model()

    def __delitem__(self, index: int) -> NotebookNode:
        with self._lock:
            with self._doc._ydoc.transaction(origin=self._changes_origin):
                raw_ycell = self._doc.ycells.pop(index)
        cell: dict[str, t.Any] = raw_ycell.to_py()
        nbcell = NotebookNode(**cell)
        return nbcell

    def __getitem__(self, index: int) -> NotebookNode:
        raw_ycell = self._doc.ycells[index]
        with self._lock:
            cell = raw_ycell.to_py()
        nbcell = NotebookNode(**cell)
        return nbcell

    def __setitem__(self, index: int, value: dict[str, t.Any]) -> None:
        with self._lock:
            with self._doc._ydoc.transaction(origin=self._changes_origin):
                self._doc.set_cell(index, value)

    def __len__(self) -> int:
        """Number of cells"""
        return self._doc.cell_number

    @property
    def nbformat(self) -> int:
        """Notebook format major version."""
        with self._lock:
            return int(self._doc._ymeta.get("nbformat") or current_api.nbformat_minor)

    @property
    def nbformat_minor(self) -> int:
        """Notebook format minor version."""
        with self._lock:
            return int(self._doc._ymeta.get("nbformat_minor") or current_api.nbformat_minor)

    @property
    def metadata(self) -> dict[str, t.Any]:
        """Notebook metadata."""
        with self._lock:
            return t.cast(pycrdt.Map, self._doc._ymeta["metadata"]).to_py() or {}

    @metadata.setter
    def metadata(self, value: dict[str, t.Any]) -> None:
        metadata = t.cast(pycrdt.Map, self._doc._ymeta["metadata"])
        with self._lock:
            with metadata.doc.transaction(origin=self._changes_origin):
                metadata.clear()
                metadata.update(value)

    def add_code_cell(self, source: str, **kwargs) -> int:
        """Add a code cell

        Args:
            source: Code cell source

        Returns:
            Index of the newly added cell
        """
        cell = current_api.new_code_cell(source, **kwargs)

        with self._lock:
            with self._doc._ydoc.transaction(origin=self._changes_origin):
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

        with self._lock:
            with self._doc._ydoc.transaction(origin=self._changes_origin):
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

        with self._lock:
            with self._doc._ydoc.transaction(origin=self._changes_origin):
                self._doc.append_cell(cell)

        return len(self) - 1

    def as_dict(self) -> dict[str, t.Any]:
        """Export the notebook as dictionary.

        Returns:
            The dictionary
        """
        with self._lock:
            return self._doc.source

    def execute_cell(
        self,
        index: int,
        kernel_client: KernelClient,
        silent: bool = False,
        store_history: bool = True,
        stop_on_error: bool = True,
        timeout: float | None = None,
    ) -> dict:
        """Execute a cell given by its index with the provided kernel client.

        The outputs will directly be stored within the notebook model.

        Args:
            index: Index of the cell to be executed
            kernel_client: Kernel client to use
            silent: optional (default False)
                If set, the kernel will execute the code as quietly possible, and
                will force store_history to be False.
            store_history: optional (default True)
                If set, the kernel will store command history.  This is forced
                to be False if silent is True.
            stop_on_error: optional (default True)
                Flag whether to abort the execution queue, if an exception is encountered.
            timeout: (default None)
                Timeout to use when waiting for a reply

        Returns:
            Execution results {"execution_count": int | None, "status": str, "outputs": list[dict]}

            The outputs will follow the structure of nbformat outputs.
        """
        try:
            import jupyter_kernel_client
        except ImportError:
            warnings.warn(
                "We recommend installing `jupyter_kernel_client` for a better execution behavior.",
                stacklevel=2,
            )

        ycell = t.cast(pycrdt.Map, self._doc.ycells[index])
        with self._lock:
            source = ycell["source"].to_py()

        # Reset cell
        with self._lock:
            with ycell.doc.transaction(origin=self._changes_origin):
                del ycell["outputs"][:]
                ycell["execution_count"] = None
                ycell["execution_state"] = "running"

        outputs = []
        reply_content = {}
        try:
            reply = kernel_client.execute_interactive(
                source,
                output_hook=partial(
                    save_in_notebook_hook, self._lock, outputs, ycell, self._changes_origin
                ),
                allow_stdin=False,
                silent=silent,
                store_history=False if silent else store_history,
                stop_on_error=stop_on_error,
                timeout=timeout,
            )

            reply_content = reply["content"]
        finally:
            with self._lock:
                with ycell.doc.transaction(origin=self._changes_origin):
                    ycell["execution_count"] = reply_content.get("execution_count")
                    ycell["execution_state"] = "idle"

        return {
            "execution_count": reply_content.get("execution_count"),
            "outputs": outputs,
            "status": reply_content["status"],
        }

    def get_cell_metadata(self, index: int, key: str, default: t.Any = None) -> t.Any:
        """Set a cell metadata.

        Args:
            index: Cell index
            key: Metadata key
        Returns:
            Metadata value or the default value if key is not found.
        """
        return self.__getitem__(index)["metadata"].get(key, default)

    def get_cell_source(self, index: int) -> None:
        """Get cell source.

        Args:
            index: Cell index
        Returns:
            The cell source
        """
        return self.__getitem__(index)["source"]

    def get_notebook_metadata(self, key: str, default: t.Any = None) -> None:
        """Get a notebook metadata.

        Args:
            key: Metadata key
        Returns:
            Metadata value or the default value if not found
        """
        return self.metadata.get(key, default)

    def insert(self, index: int, value: dict[str, t.Any]) -> None:
        """Insert a new cell at position index.

        Args:
            index: The position of the inserted cell
            value: A mapping describing the cell
        """
        ycell = self._doc.create_ycell(value)
        with self._lock:
            with self._doc._ydoc.transaction(origin=self._changes_origin):
                self._doc.ycells.insert(index, ycell)

    def insert_code_cell(self, index: int, source: str, **kwargs) -> None:
        """Insert a code cell at position index.

        Args:
            index: The position of the inserted cell
            source: Code cell source
        """
        cell = current_api.new_code_cell(source, **kwargs)
        self.insert(index, cell)

    def insert_markdown_cell(self, index: int, source: str, **kwargs) -> None:
        """Insert a markdown cell at position index.

        Args:
            index: The position of the inserted cell
            source: Markdown cell source
        """
        cell = current_api.new_markdown_cell(source, **kwargs)
        self.insert(index, cell)

    def set_cell_metadata(self, index: int, key: str, value: t.Any) -> None:
        """Set a cell metadata.

        Args:
            index: Cell index
            key: Metadata key
            value: Metadata value
        """
        with self._lock:
            with self._doc._ydoc.transaction(origin=self._changes_origin):
                metadata = t.cast(
                    pycrdt.Map, t.cast(pycrdt.Map, self._doc._ycells[index])["metadata"]
                )
                if key in metadata:
                    del metadata[key]  # FIXME pycrdt only support inserting key
                metadata[key] = value

    def set_cell_source(self, index: int, source: str) -> None:
        """Set a cell source.

        Args:
            index: Cell index
            source: New cell source
        """
        with self._lock:
            with self._doc._ydoc.transaction(origin=self._changes_origin):
                # TODO check it works - if as metadata, it does not.
                t.cast(pycrdt.Map, self._doc._ycells[index])["source"] = source

    def set_notebook_metadata(self, key: str, value: t.Any) -> None:
        """Set a notebook metadata.

        Args:
            key: Metadata key
            value: Metadata value
        """
        with self._lock:
            with self._doc._ydoc.transaction(origin=self._changes_origin):
                metadata = t.cast(pycrdt.Map, self._doc._ymeta["metadata"])
                if key in metadata:
                    del metadata[key]  # FIXME pycrdt only support inserting key
                metadata[key] = value

    def _fix_model(self) -> None:
        """Fix the model to set mandatory notebook attributes."""
        with self._lock:
            with self._doc._ymeta.doc.transaction():
                if "metadata" not in self._doc._ymeta:
                    self._doc._ymeta["metadata"] = pycrdt.Map()
                if "nbformat" not in self._doc._ymeta:
                    self._doc._ymeta["nbformat"] = current_api.nbformat
                if "nbformat_minor" not in self._doc._ymeta:
                    self._doc._ymeta["nbformat_minor"] = current_api.nbformat_minor

    def _reset_y_model(self) -> None:
        """Reset the Y model."""
        doc = pycrdt.Doc()
        awareness = pycrdt.Awareness(doc)
        self._doc = YNotebook(ydoc=doc, awareness=awareness)
