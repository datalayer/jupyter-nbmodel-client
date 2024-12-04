#

import os
import re

HTTP_PROTOCOL_REGEXP = re.compile(r"^http")
"""http protocol regular expression."""
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", 10))
"""Default request timeout in seconds"""