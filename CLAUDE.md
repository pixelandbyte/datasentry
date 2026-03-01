# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> "Your data belongs to you. Full stop."

---

## Build & Run Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run the dev server
uvicorn main:app --reload

# Run tests
pytest

# Run a single test file
pytest tests/test_ecg.py

# Run tests with output
pytest -v -s
```

**Environment:** Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY` (required for ECG only).

---

## What DataSentry Is

DataSentry is a privacy-first SaaS utility bundle that protects, validates, and stress-tests automation pipelines built on **Zapier, Make, and n8n** — collectively referred to as **The A3**. Part of the **JustTheDomain** ecosystem (DomainCheck, LinkCloak, DataSentry).

Three utilities, one FastAPI backend:

- **ECG (Edge Case Generator)** — AI-powered pipeline risk analysis via Anthropic API. The ONLY module that uses AI.
- **DV (Data Validator)** — Deterministic data integrity checks at extraction/transfer handoff points. No AI.
- **DCloak (Data Obfuscator)** — Stateless sensitive data masking in transit. No AI.

Each module is independent and must function without the others.

---

## Architecture

Single FastAPI app. Three independent modules under `modules/`. Each module has `router.py` (endpoint + auth) and `core.py` (business logic). Each module has its own `CLAUDE.md` — always read it before editing that module.

```
├── main.py                    # FastAPI entry point, mounts module routers
├── requirements.txt
├── modules/
│   ├── ecg/                   # POST /ecg/analyze
│   ├── dv/                    # POST /dv/validate
│   └── dcloak/                # POST /dcloak/obfuscate
├── auth/
│   └── api_keys.py            # API key scoping (ecg|dv|dcloak|bundle)
└── web/
    └── index.html             # Demo interface for all three utilities
```

### API Key Scoping

Keys are scoped per utility: `ecg`, `dv`, `dcloak`, or `bundle` (all three). Enforced as a FastAPI dependency on each router. A key with `ecg` scope cannot call `/dv/validate`.

### Tech Stack

Python, FastAPI, Anthropic SDK (ECG only). Deploy target: Railway or Fly.io.

---

## Non-Negotiable Constraints

- **No microservices** — single FastAPI backend
- **No AI in DV or DCloak** — these are fully deterministic
- **No subscription/usage-based billing** — one-time purchase model
- **No OAuth or user accounts** — API key scoping only
- **Module isolation** — each module's `core.py` must be independently runnable; no cross-module imports
- **No data retention** — never store, log, or cache user pipeline data
- **Web interface is a demo surface** — not a product dashboard

---

## Development Priority Order

1. ECG (Anthropic API integration)
2. DV (deterministic validation)
3. DCloak (obfuscation patterns)
4. API key scoping
5. Web interface

---

## Pricing Context (affects feature scoping)

| Product | Community | Open Market |
|---|---|---|
| ECG | $7 | $9–12 |
| DV | $7 | $9–12 |
| DCloak | $9 | $14–17 |
| Bundle | $20 | $27–37 |

One-time purchase. No subscription. No data harvesting.

---

## Ecosystem & Tone

DataSentry sits within JustTheDomain: DomainCheck (domain level), LinkCloak (link level), DataSentry (workflow level). User-facing copy must be direct, privacy-first, tool-oriented. No marketing fluff.

Domains: datasentry.dev (primary), datasentry.pro (redirect).
