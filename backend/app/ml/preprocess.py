"""Text normalization helpers.

Purpose: Normalize raw message text before ML/rule processing.
Callers: ML scoring and rule hint modules.
Deps: Python re.
API: normalize_text(text: str) -> str.
Side effects: None.
"""

import re

_SPACE_RE = re.compile(r'\s+')


def normalize_text(text: str) -> str:
    return _SPACE_RE.sub(' ', text.strip().lower())
