import re

_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"disregard\s+all\s+prior",
    r"system\s*:\s*you\s+are",
    r"<\s*system\s*>",
    r"\bjailbreak\b",
    r"act\s+as\s+(?:dan|jailbreak|unrestricted)",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _PATTERNS]


class InjectionDetected(Exception):
    pass


def check_prompt(text: str) -> None:
    for pattern in _COMPILED:
        if pattern.search(text):
            raise InjectionDetected("Prompt injection detectado")
