from traitlets import Unicode

from jupyter_server.extension.application import ExtensionApp
from .handlers import PingHandler


class Extension(ExtensionApp):

    name = "jupyter_nbmodel_client"
    handlers = [
        ("jupyter-nbmodel-client/ping", PingHandler)
    ]

    # Example of a configurable trait. This is meant to be replaced
    # with configurable traits for this extension.
    ping_response = Unicode(default_value="pong").tag(config=True)

    def initialize_settings(self):
        self.settings.update({
            "ping_response": self.ping_response
        })
