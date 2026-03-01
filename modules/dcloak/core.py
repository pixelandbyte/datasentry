import copy
import hashlib
import random
import re
import string
from typing import Any, Dict, List

VALID_STRATEGIES = {"mask", "redact", "fake", "hash"}

FAKE_NAMES = [
    "Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Hank",
    "Iris", "Jack", "Karen", "Leo", "Mia", "Nate", "Olivia", "Paul",
]


def _resolve_field(data: dict, path: str) -> Any:
    """Walk dot-separated path into nested dicts. Raises KeyError on miss."""
    keys = path.split(".")
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            raise KeyError(path)
        current = current[key]
    return current


def _set_field(data: dict, path: str, value: Any) -> None:
    """Set a value at a dot-separated path in nested dicts."""
    keys = path.split(".")
    current = data
    for key in keys[:-1]:
        current = current[key]
    current[keys[-1]] = value


# ── Strategies ───────────────────────────────────────────────────────


def _mask(value: str) -> str:
    s = str(value)
    if len(s) <= 2:
        return "*" * len(s)
    return s[0] + "*" * (len(s) - 2) + s[-1]


def _redact(_value: Any) -> str:
    return "[REDACTED]"


def _fake(value: Any) -> Any:
    s = str(value)

    # Email
    if isinstance(value, str) and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s):
        num = random.randint(1000, 9999)
        return f"user_{num}@placeholder.com"

    # Phone — digits with optional +, spaces, dashes, parens
    if isinstance(value, str) and re.match(r"^\+?[\d\s\-()]+$", s) and len(s) >= 7:
        result = []
        for ch in s:
            if ch.isdigit():
                result.append(str(random.randint(0, 9)))
            else:
                result.append(ch)
        return "".join(result)

    # URL
    if isinstance(value, str) and re.match(r"^https?://", s):
        num = random.randint(1000, 9999)
        return f"https://placeholder.com/{num}"

    # Name — single capitalised word
    if isinstance(value, str) and re.match(r"^[A-Z][a-z]+$", s):
        return random.choice(FAKE_NAMES)

    # Integer
    if isinstance(value, int) and not isinstance(value, bool):
        magnitude = max(1, abs(value))
        return random.randint(0, magnitude * 2)

    # Float
    if isinstance(value, float):
        decimal_str = str(value)
        if "." in decimal_str:
            decimal_places = len(decimal_str.split(".")[1])
        else:
            decimal_places = 1
        magnitude = max(1.0, abs(value))
        return round(random.uniform(0, magnitude * 2), decimal_places)

    # String fallback
    length = len(s) if len(s) > 0 else 8
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _hash(value: Any) -> str:
    s = str(value)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


STRATEGY_FNS = {
    "mask": _mask,
    "redact": _redact,
    "fake": _fake,
    "hash": _hash,
}


# ── Public API ───────────────────────────────────────────────────────


def obfuscate_data(data: Dict[str, Any], fields: List[Dict[str, str]]) -> dict:
    # Validate strategies up-front
    for f in fields:
        strategy = f.get("strategy", "")
        if strategy not in VALID_STRATEGIES:
            raise ValueError(f"Unknown strategy: '{strategy}'")

    result = copy.deepcopy(data)
    obfuscated_fields: List[str] = []
    skipped_fields: List[str] = []

    for f in fields:
        field_path = f["field"]
        strategy = f["strategy"]

        try:
            original = _resolve_field(result, field_path)
        except KeyError:
            skipped_fields.append(field_path)
            continue

        fn = STRATEGY_FNS[strategy]
        new_value = fn(original)
        _set_field(result, field_path, new_value)
        obfuscated_fields.append(field_path)

    total = len(fields)
    obfuscated = len(obfuscated_fields)
    skipped = len(skipped_fields)

    if total == 0:
        summary = "No fields specified; data unchanged."
    elif skipped == 0:
        summary = f"Obfuscated {obfuscated} field(s)."
    else:
        summary = f"Obfuscated {obfuscated} field(s), skipped {skipped}."

    return {
        "data": result,
        "obfuscated_fields": obfuscated_fields,
        "skipped_fields": skipped_fields,
        "summary": summary,
    }
