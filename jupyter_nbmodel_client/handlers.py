import json

from jupyter_server.extension.handler import ExtensionHandlerMixin
from jupyter_server.base.handlers import APIHandler
import tornado


class PingHandler(ExtensionHandlerMixin, APIHandler):
    # The following decorator should be present on all verb methods (head, get, post,
    # patch, put, delete, options) to ensure only authorized user can request the
    # Jupyter server
    @property
    def ping_response(self):
        return self.settings["ping_response"]

    @tornado.web.authenticated
    def get(self):
        self.finish(json.dumps({
            "ping_response": self.ping_response
        }))
