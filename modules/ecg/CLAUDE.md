# ECG — Edge Case Generator
# Module CLAUDE.md

> "Know what could go wrong before it does."

Read the root CLAUDE.md before this file. This file governs ECG-specific implementation only.

---

## What ECG Does

ECG is the AI-powered utility in DataSentry. It takes a description of an automation pipeline design and returns a structured analysis of edge cases, failure scenarios, and exceptions the user may not have considered — before the pipeline ever goes live.

ECG does not execute, test, or transform any pipeline data. It is pure analytical thinking work powered by the Anthropic API.

---

## Files in This Module

```
modules/ecg/
├── CLAUDE.md       # This file
├── router.py       # FastAPI endpoint — handles request/response, auth dependency
└── core.py         # Anthropic API call, prompt logic, response parsing
```

Keep all ECG logic inside this folder. Do not import ECG logic from outside this module. Do not let ECG logic leak into main.py beyond router registration.

---

## API Endpoint

```
POST /ecg/analyze
```

**Required header:** `X-API-Key` with `ecg` or `bundle` scope

**Request body:**
```json
{
  "pipeline_description": "string",
  "platform": "zapier | make | n8n",
  "context": "string (optional — additional notes about the pipeline)"
}
```

**Response body:**
```json
{
  "edge_cases": ["string", "..."],
  "failure_scenarios": ["string", "..."],
  "assumptions_flagged": ["string", "..."],
  "summary": "string"
}
```

---

## Anthropic API Integration

### Key Rules

- ECG is the ONLY module that calls the Anthropic API. DV and DCloak are fully deterministic — never add AI calls to them.
- Use the `anthropic` Python SDK — do not make raw HTTP calls.
- The API key is loaded from the environment variable `ANTHROPIC_API_KEY`. Never hardcode it.
- Model: use `claude-3-5-haiku-20241022` for cost efficiency at this price point ($7–12 one-time purchase). Do not use Opus.
- Always set a `max_tokens` limit. Start at 1024 — increase only if response quality requires it.

### Prompt Design

The system prompt must instruct the model to:
- Act as an automation pipeline risk analyst
- Focus on The A3 platforms: Zapier, Make, and n8n
- Return structured output only (no conversational filler)
- Cover three categories: edge cases, failure scenarios, and flagged assumptions

The user prompt passes the pipeline description and platform directly.

Structure the prompt in `core.py` — do not build prompts inside `router.py`.

### Response Parsing

The model response must be parsed into the structured response body defined above before it is returned to the user. Do not return raw model output.

If the model returns malformed or unparseable output, return a `500` with a clear error message — do not return partial data.

---

## Error Handling

| Scenario | HTTP Status | Behaviour |
|---|---|---|
| Missing or invalid API key | 401 | Reject at auth dependency, before core.py is called |
| Missing `pipeline_description` | 422 | FastAPI validation handles automatically |
| Anthropic API error | 502 | Log the error, return a clean message to the user |
| Unparseable model response | 500 | Log the raw response, return a clean error |
| Empty `pipeline_description` | 400 | Validate in router.py before calling core.py |

---

## What ECG Must Never Do

- Call any external API other than the Anthropic API
- Store, log, or cache pipeline descriptions — user data is not retained
- Return raw Anthropic API responses directly to the user
- Accept pipeline descriptions over 5,000 characters without truncating or rejecting
- Add streaming responses at this stage — return complete responses only

---

## Dependencies

Add to `requirements.txt`:
```
anthropic
```

No other external dependencies should be needed for this module.

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API authentication |

Load via `os.environ` or a `.env` file using `python-dotenv`. Never hardcode.

---

*ECG — AI-powered edge case analysis for The A3.*
