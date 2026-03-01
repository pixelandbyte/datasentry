import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

VALID_TYPES = {"string", "number", "boolean", "email", "url", "date", "phone"}


def _truncate(value: Any, limit: int = 100) -> str:
    s = str(value)
    return s[:limit] if len(s) > limit else s


def _check_type(value: Any, field_type: str) -> Optional[str]:
    if field_type == "string":
        if not isinstance(value, str):
            return "Expected a string"
        if len(value) == 0:
            return "String must not be empty"
        return None

    if field_type == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "Expected a number"
        return None

    if field_type == "boolean":
        if not isinstance(value, bool):
            return "Expected a boolean"
        return None

    if field_type == "email":
        if not isinstance(value, str):
            return "Expected a string for email"
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
            return "Invalid email format"
        return None

    if field_type == "url":
        if not isinstance(value, str):
            return "Expected a string for URL"
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            return "Invalid URL (must include scheme and host)"
        return None

    if field_type == "date":
        if not isinstance(value, str):
            return "Expected a date string"
        formats = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"]
        for fmt in formats:
            try:
                datetime.strptime(value, fmt)
                return None
            except ValueError:
                continue
        return "Invalid date format (ISO 8601 expected)"

    if field_type == "phone":
        if not isinstance(value, str):
            return "Expected a string for phone"
        if not re.match(r"^\+?[\d\s\-()]+$", value):
            return "Invalid phone format (digits, spaces, dashes, parentheses, and leading + only)"
        return None

    return None  # unreachable if VALID_TYPES is checked first


def validate_data(data: Dict[str, Any], rules: List[Dict[str, Any]]) -> dict:
    errors: List[dict] = []

    # Check for invalid rule types up front
    for rule in rules:
        field_type = rule.get("type", "")
        if field_type not in VALID_TYPES:
            raise ValueError(f"Invalid rule type: '{field_type}'")

    for rule in rules:
        field = rule["field"]
        field_type = rule["type"]
        required = rule.get("required", False)
        value = data.get(field)

        # If field is missing or None
        if value is None or field not in data:
            if required:
                errors.append({
                    "field": field,
                    "issue": "Field is required but missing",
                    "value_received": "null",
                })
            # Skip all other rules for this field
            continue

        # Type check
        type_issue = _check_type(value, field_type)
        if type_issue:
            errors.append({
                "field": field,
                "issue": type_issue,
                "value_received": _truncate(value),
            })

        # allowed_values
        allowed = rule.get("allowed_values")
        if allowed is not None and value not in allowed:
            errors.append({
                "field": field,
                "issue": f"Value not in allowed values: {allowed}",
                "value_received": _truncate(value),
            })

        # min_length / max_length — applies to strings and arrays
        if isinstance(value, (str, list)):
            min_len = rule.get("min_length")
            if min_len is not None and len(value) < min_len:
                errors.append({
                    "field": field,
                    "issue": f"Length {len(value)} is below minimum {min_len}",
                    "value_received": _truncate(value),
                })
            max_len = rule.get("max_length")
            if max_len is not None and len(value) > max_len:
                errors.append({
                    "field": field,
                    "issue": f"Length {len(value)} exceeds maximum {max_len}",
                    "value_received": _truncate(value),
                })

        # pattern — applies to string values only
        pat = rule.get("pattern")
        if pat is not None and isinstance(value, str):
            if not re.search(pat, value):
                errors.append({
                    "field": field,
                    "issue": f"Value does not match pattern: {pat}",
                    "value_received": _truncate(value),
                })

    total = len(rules)
    failed = len({e["field"] for e in errors})
    valid = len(errors) == 0

    if valid:
        summary = f"All {total} field(s) passed validation."
    else:
        summary = f"{failed} of {total} fields failed validation."

    return {
        "valid": valid,
        "errors": errors,
        "summary": summary,
    }
