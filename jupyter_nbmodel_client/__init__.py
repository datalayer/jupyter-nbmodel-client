# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Client to interact with Jupyter notebook model."""

from nbformat import NotebookNode

from .client import NbModelClient, get_jupyter_notebook_websocket_url
from .model import KernelClient, NotebookModel

__version__ = "0.6.0"

__all__ = [
    "KernelClient",
    "NbModelClient",
    "NotebookModel",
    "NotebookNode",
    "get_jupyter_notebook_websocket_url",
]
