"""Project-wide constants shared across backend modules."""

import re
from pathlib import Path

PROJECT_ROOT_PATH = Path(__file__).resolve().parent.parent

TASK_ID_PATTERN = re.compile(r"^[a-z0-9_]{1,64}$")
