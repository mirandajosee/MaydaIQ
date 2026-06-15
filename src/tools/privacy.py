"""Privacy redaction helpers for responder-ready but public-safe reports."""

from __future__ import annotations

import re


PRIVATE_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b"), "[email redacted]", "email address"),
    (re.compile(r"\b(?:\+?\d[\d\s().-]{7,}\d)\b"), "[phone redacted]", "phone number"),
    (re.compile(r"\b[A-Z0-9]{1,3}[-\s]?[A-Z0-9]{3,4}\b"), "[plate/id redacted]", "possible plate or ID"),
]


def redact_private_details(text: str) -> tuple[str, list[str]]:
    redactions: list[str] = []
    redacted = text
    for pattern, replacement, label in PRIVATE_PATTERNS:
        if pattern.search(redacted):
            redacted = pattern.sub(replacement, redacted)
            redactions.append(label)
    redactions.append("faces, people, license plates, and suspects are not identified")
    return redacted, sorted(set(redactions))

