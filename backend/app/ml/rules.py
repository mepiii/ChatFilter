"""Rule-based scam hint detection.

Purpose: Detect explainable text hints and map model probabilities to labels.
Callers: ML scoring and API response formatting.
Deps: Python re.
API: detect_rule_hints(text: str) -> list[str]; map_label(probability: float, hints: list[str]) -> str.
Side effects: None.
"""

import re

_HINT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ('url present', re.compile(r'https?://|www\.', re.IGNORECASE)),
    ('money language', re.compile(r'\$|\b(pay|payment|cash|money|fee|transfer|bank|wallet)\b', re.IGNORECASE)),
    ('urgency language', re.compile(r'\b(urgent|immediately|now|limited time|act fast|suspend|locked)\b', re.IGNORECASE)),
    ('reward claim', re.compile(r'\b(prize|reward|lottery|won|winner|claim|free)\b', re.IGNORECASE)),
    ('credential request', re.compile(r'\b(password|otp|code|verify|recovery phrase|login)\b', re.IGNORECASE)),
    ('off-platform contact request', re.compile(r'\b(whatsapp|telegram|text me|call me|contact support)\b', re.IGNORECASE)),
)

_SCAM_HINTS = {'money language', 'credential request', 'off-platform contact request'}


def detect_rule_hints(text: str) -> list[str]:
    return [name for name, pattern in _HINT_PATTERNS if pattern.search(text)]


def map_label(probability: float, hints: list[str]) -> str:
    strong_scam = bool(_SCAM_HINTS.intersection(hints))
    if probability >= 0.7 and (strong_scam or 'urgency language' in hints):
        return 'scam'
    if strong_scam:
        return 'scam'
    if probability >= 0.4 or hints:
        return 'spam'
    return 'safe'
