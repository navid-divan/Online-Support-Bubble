from __future__ import annotations

import os

DEFAULT_SUBJECT_TOKENS = int(os.environ.get("OSB_SUBJECT_TOKENS", "8"))
DEFAULT_ADVISOR_TOKENS = int(os.environ.get("OSB_ADVISOR_TOKENS", "32"))

TRANSPORT = os.environ.get("OSB_TRANSPORT", "inproc")
