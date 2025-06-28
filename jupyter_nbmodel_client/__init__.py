# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

"""Client to interact with Jupyter notebook model."""

from nbformat import NotebookNode

from jupyter_nbmodel_client._version import VERSION as __version__  # noqa: N811
from jupyter_nbmodel_client.agent import AIMessageType, BaseNbAgent
from jupyter_nbmodel_client.client import NbModelClient
from jupyter_nbmodel_client.helpers import (
    get_notebook_websocket_url,
    get_datalayer_notebook_websocket_url,
    get_jupyter_notebook_websocket_url,
)
from jupyter_nbmodel_client.model import KernelClient, NotebookModel


__all__ = [
    "AIMessageType",
    "BaseNbAgent",
    "KernelClient",
    "NbModelClient",
    "NotebookModel",
    "NotebookNode",
    "__version__",
    "get_notebook_websocket_url",
    "get_datalayer_notebook_websocket_url",
    "get_jupyter_notebook_websocket_url",
]
