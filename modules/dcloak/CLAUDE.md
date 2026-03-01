# DCloak — Data Obfuscator
# Module CLAUDE.md

> "What they can't see can't hurt you."

Read the root CLAUDE.md before this file. This file governs DCloak-specific implementation only.

---

## What DCloak Does

DCloak masks sensitive data as it travels through an automation pipeline. It sits as an additional transformation step between pipeline stages, intercepting a data payload and replacing sensitive field values with obfuscated equivalents before the data moves to the next app.

The pipeline continues to run perfectly. Apps that don't need to see sensitive values see only noise. Apps that do need the real values receive them — DCloak is selective by field, not by payload.

DCloak is fully deterministic. There are no AI calls, no external API calls, and no randomness beyond the obfuscation output itself.

---

## What DCloak Does NOT Do

- DCloak does not validate data — that is DV's job
- DCloak does not analyze pipeline logic — that is ECG's job
- DCloak does not store original values or maintain a mapping table — obfuscation is one-way per request
- DCloak does not call the Anthropic API or any other AI service — ever
- DCloak does not encrypt data — it obfuscates it (different security model, different use case)

---

## Files in This Module

```
modules/dcloak/
├── CLAUDE.md       # This file
├── router.py       # FastAPI endpoint — handles request/response, auth dependency
└── core.py         # Obfuscation logic — all masking strategies live here
```

Keep all DCloak logic inside this folder. Do not import DCloak logic from outside this module.

---

## API Endpoint

```
POST /dcloak/obfuscate
```

**Required header:** `X-API-Key` with `dcloak` or `bundle` scope

**Request body:**
```json
{
  "data": { },
  "fields": [
    {
      "field": "string",
      "strategy": "mask | redact | fake | hash"
    }
  ]
}
```

**Response body:**
```json
{
  "data": { },
  "obfuscated_fields": ["string", "..."],
  "skipped_fields": ["string", "..."],
  "summary": "string"
}
```

The `data` in the response is the full original payload with only the specified fields replaced. All other fields pass through unchanged.

---

## Obfuscation Strategies

Implement all four strategies in `core.py`:

| Strategy | Behaviour | Example |
|---|---|---|
| `mask` | Replace characters with `*`, preserving length and first/last character | `john@example.com` → `j**************m` |
| `redact` | Replace the entire value with `[REDACTED]` | `john@example.com` → `[REDACTED]` |
| `fake` | Replace with a plausible but fake value of the same type | `john@example.com` → `user_4829@placeholder.com` |
| `hash` | Replace with a SHA-256 hash of the original value (hex, truncated to 16 characters) | `john@example.com` → `a3f2c1d9e8b74a01` |

### Strategy Selection Guidelines (for documentation — not enforced in code)

- `mask` — good for display purposes where partial visibility is acceptable
- `redact` — maximum concealment, value is completely removed
- `fake` — best for pipeline testing where downstream apps need a plausible value
- `hash` — best for correlation without exposure (e.g. tracking a user without revealing their email)

---

## Field Resolution

- If a field listed in `fields` does not exist in `data`, add it to `skipped_fields` — do not raise an error
- If `fields` is empty, return the original `data` unchanged with an empty `obfuscated_fields` list
- Support dot notation for nested fields: `"field": "user.email"` should resolve `data["user"]["email"]`
- If a nested path does not exist, add to `skipped_fields`

---

## The `fake` Strategy

The `fake` strategy must generate plausible replacements. Implement type detection to produce appropriate fakes:

| Detected Type | Fake Output |
|---|---|
| Email address | `user_XXXX@placeholder.com` (XXXX = random 4-digit number) |
| Phone number | Digits replaced with random digits, format preserved |
| URL | `https://placeholder.com/XXXX` |
| Name (single word, capitalised) | Random first name from a small hardcoded list |
| Number (integer) | Random integer of similar magnitude |
| Number (float) | Random float of similar magnitude, same decimal places |
| String (fallback) | Random alphanumeric string of same length |

Use a small hardcoded list for names — do not call any external API or name generation service.

---

## Error Handling

| Scenario | HTTP Status | Behaviour |
|---|---|---|
| Missing or invalid API key | 401 | Reject at auth dependency |
| Missing `data` or `fields` | 422 | FastAPI validation handles automatically |
| Unknown `strategy` value | 400 | Reject in router.py before calling core.py |
| Field not found in data | 200 | Add to `skipped_fields`, continue processing |
| Nested path resolution failure | 200 | Add to `skipped_fields`, continue processing |

---

## What DCloak Must Never Do

- Call the Anthropic API or any external service
- Store original values or maintain any mapping between original and obfuscated values — obfuscation is stateless and one-way per request
- Decrypt or reverse obfuscation — there is no reverse endpoint
- Modify fields that are not listed in the `fields` array
- Log or retain the data payload — user data is not retained

---

## Dependencies

No external dependencies beyond FastAPI and standard Python libraries (`hashlib`, `re`, `random`, `string`). Do not add third-party obfuscation or fake data libraries — keep this module self-contained.

---

## Pricing Note

DCloak is priced higher than ECG and DV ($9 community / $14–17 open market) because it operates directly on live data in transit. This is the highest-trust utility in the bundle. Keep the implementation clean, stateless, and auditable.

---

*DCloak — Stateless sensitive data obfuscation for The A3.*
