"""Client to interact with Jupyter notebook model."""

from nbformat import NotebookNode

from .client import NbModelClient
from .model import KernelClient, NotebookModel

__version__ = "0.1.1"

__all__ = ["KernelClient", "NbModelClient", "NotebookModel", "NotebookNode"]
