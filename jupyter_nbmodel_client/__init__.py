"""Client to interact with Jupyter notebook model."""

from .client import NbModelClient
from .model import NotebookModel
from nbformat import NotebookNode

__version__ = "0.1.0"

__all__ = ["NbModelClient", "NotebookModel", "NotebookNode"]
