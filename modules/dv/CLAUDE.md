# DV — Data Validator
# Module CLAUDE.md

> "Trust your data at every handoff."

Read the root CLAUDE.md before this file. This file governs DV-specific implementation only.

---

## What DV Does

DV validates data integrity at extraction and transfer stages within an automation pipeline. It checks that data arriving at a handoff point is the right format, type, and structure before it moves to the next step.

DV catches bad data at the source instead of letting it cause mysterious failures downstream.

DV is fully deterministic. There are no AI calls, no external API calls, and no randomness. Given the same input and ruleset, DV always produces the same output.

---

## What DV Does NOT Do

- DV does not transform data — it only validates it
- DV does not fix bad data — it reports what is wrong and where
- DV does not operate on transformation stages — extraction and transfer only
- DV does not call the Anthropic API or any other AI service — ever

---

## Files in This Module

```
modules/dv/
├── CLAUDE.md       # This file
├── router.py       # FastAPI endpoint — handles request/response, auth dependency
└── core.py         # Validation logic — all rule checking lives here
```

Keep all DV logic inside this folder. Do not import DV logic from outside this module.

---

## API Endpoint

```
POST /dv/validate
```

**Required header:** `X-API-Key` with `dv` or `bundle` scope

**Request body:**
```json
{
  "data": { },
  "rules": [
    {
      "field": "string",
      "type": "string | number | boolean | email | url | date | phone",
      "required": true,
      "allowed_values": ["optional", "list"],
      "min_length": 0,
      "max_length": 255,
      "pattern": "optional regex string"
    }
  ]
}
```

**Response body:**
```json
{
  "valid": true,
  "errors": [
    {
      "field": "string",
      "issue": "string",
      "value_received": "string"
    }
  ],
  "summary": "string"
}
```

If `valid` is `true`, `errors` is an empty array. If `valid` is `false`, `errors` contains one entry per failed rule.

---

## Validation Rule Types

Implement support for these field types in `core.py`:

| Type | What to Check |
|---|---|
| `string` | Value is a non-empty string (unless not required) |
| `number` | Value is an integer or float |
| `boolean` | Value is `true` or `false` |
| `email` | Value matches standard email format |
| `url` | Value is a valid URL with scheme |
| `date` | Value is a parseable date string (ISO 8601 preferred) |
| `phone` | Value contains only digits, spaces, dashes, parentheses, and leading `+` |

Additional rule options that apply to any type:
- `required` — if `true` and field is missing or null, fail
- `allowed_values` — if provided, value must be in the list
- `min_length` / `max_length` — applies to strings and arrays
- `pattern` — optional regex, applied to string values only

---

## Validation Behaviour

- Validate ALL fields before returning — do not stop at the first error
- One error object per failed rule per field
- If a field is not `required` and is missing, skip all other rules for that field
- `value_received` in the error should show what was actually received (truncated to 100 characters if long)
- The `summary` field should be a single plain-English sentence: e.g. "3 of 7 fields failed validation."

---

## Error Handling

| Scenario | HTTP Status | Behaviour |
|---|---|---|
| Missing or invalid API key | 401 | Reject at auth dependency |
| Missing `data` or `rules` | 422 | FastAPI validation handles automatically |
| Empty `rules` array | 400 | Reject in router.py with a clear message |
| Invalid rule `type` value | 400 | Reject in core.py before processing |
| Valid request, failing data | 200 | Return `valid: false` with errors — this is not an HTTP error |

A validation failure is a successful API response, not an error. Only return non-200 status codes for request problems.

---

## What DV Must Never Do

- Call the Anthropic API or any external service
- Modify or transform the data it receives
- Infer or guess what a rule should be — only apply what is explicitly provided
- Return a 200 with partial results if the request itself was malformed
- Store or log the data payload — user data is not retained

---

## Dependencies

No external dependencies beyond FastAPI and standard Python libraries (`re`, `urllib`, `datetime`). Do not add third-party validation libraries — keep this module self-contained and lightweight.

---

*DV — Deterministic data validation for The A3.*
