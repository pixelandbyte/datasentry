import json
import os
import re
from typing import Optional

import anthropic

SYSTEM_PROMPT = """\
You are an automation pipeline risk analyst for The A3 platforms (Zapier, Make, and n8n).

Given a pipeline description, analyze it and return ONLY a JSON object with these keys:
- "edge_cases": array of strings — edge cases the pipeline may encounter
- "failure_scenarios": array of strings — ways the pipeline could fail
- "assumptions_flagged": array of strings — assumptions the designer may not have considered
- "summary": string — a concise overall risk summary

Return valid JSON only. No markdown fencing, no commentary outside the JSON object."""


def analyze_pipeline(
    pipeline_description: str, platform: str, context: Optional[str] = None
) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    user_content = f"Platform: {platform}\n\nPipeline description:\n{pipeline_description}"
    if context:
        user_content += f"\n\nAdditional context:\n{context}"

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw_text = message.content[0].text

    # Strip markdown fences if present
    stripped = re.sub(r"^```(?:json)?\s*\n?", "", raw_text.strip())
    stripped = re.sub(r"\n?```\s*$", "", stripped)

    try:
        result = json.loads(stripped)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model returned malformed JSON: {e}") from e

    required_keys = {"edge_cases", "failure_scenarios", "assumptions_flagged", "summary"}
    missing = required_keys - set(result.keys())
    if missing:
        raise ValueError(f"Model response missing keys: {missing}")

    return result
