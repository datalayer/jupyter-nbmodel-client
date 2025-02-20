# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

import logging
import os
import re

HTTP_PROTOCOL_REGEXP = re.compile(r"^http")
"""http protocol regular expression."""
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", 10))
"""Default request timeout in seconds"""

DEFAULT_LOGGER = logging.getLogger("jupyter_nbmodel_client")
"""Default logger for the library."""
