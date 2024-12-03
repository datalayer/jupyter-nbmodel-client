import pytest

pytest_plugins = ["jupyter_server.pytest_plugin", "jupyter_server_ydoc.pytest_plugin"]


@pytest.fixture
def jp_server_config(jp_server_config):
    return {
        "ServerApp": {
            "jpserver_extensions": {"jupyter_server_ydoc": True, "jupyter_server_fileid": True}
        }
    }
