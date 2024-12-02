"""Client to interact with Jupyter notebook model."""
from .extension import Extension
__version__ = "0.1.0"


def _jupyter_server_extension_points():
    return [{
        "module": "jupyter_nbmodel_client",
        "app": Extension
    }]
