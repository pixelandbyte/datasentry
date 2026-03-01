import json
from unittest.mock import MagicMock, patch

import pytest

from modules.ecg.core import analyze_pipeline

VALID_RESPONSE = {
    "edge_cases": ["Rate limit hit"],
    "failure_scenarios": ["API timeout"],
    "assumptions_flagged": ["Always-on connectivity"],
    "summary": "Moderate risk pipeline.",
}


def _mock_message(text):
    """Build a mock Anthropic message response."""
    block = MagicMock()
    block.text = text
    msg = MagicMock()
    msg.content = [block]
    return msg


# ── Happy path ───────────────────────────────────────────────────────


class TestAnalyzePipeline:
    @patch("modules.ecg.core.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "fake-key"})
    def test_valid_json_response(self, mock_cls):
        mock_cls.return_value.messages.create.return_value = _mock_message(
            json.dumps(VALID_RESPONSE)
        )
        result = analyze_pipeline("Send email on new row", "zapier")
        assert result == VALID_RESPONSE

    @patch("modules.ecg.core.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "fake-key"})
    def test_with_context(self, mock_cls):
        mock_cls.return_value.messages.create.return_value = _mock_message(
            json.dumps(VALID_RESPONSE)
        )
        result = analyze_pipeline("Send email", "make", context="High volume")
        assert result == VALID_RESPONSE
        call_args = mock_cls.return_value.messages.create.call_args
        user_msg = call_args[1]["messages"][0]["content"]
        assert "High volume" in user_msg

    @patch("modules.ecg.core.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "fake-key"})
    def test_platform_in_prompt(self, mock_cls):
        mock_cls.return_value.messages.create.return_value = _mock_message(
            json.dumps(VALID_RESPONSE)
        )
        analyze_pipeline("Do something", "n8n")
        call_args = mock_cls.return_value.messages.create.call_args
        user_msg = call_args[1]["messages"][0]["content"]
        assert "n8n" in user_msg


# ── Markdown fence stripping ────────────────────────────────────────


class TestMarkdownStripping:
    @patch("modules.ecg.core.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "fake-key"})
    def test_strips_json_fences(self, mock_cls):
        fenced = f"```json\n{json.dumps(VALID_RESPONSE)}\n```"
        mock_cls.return_value.messages.create.return_value = _mock_message(fenced)
        result = analyze_pipeline("test", "zapier")
        assert result == VALID_RESPONSE

    @patch("modules.ecg.core.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "fake-key"})
    def test_strips_plain_fences(self, mock_cls):
        fenced = f"```\n{json.dumps(VALID_RESPONSE)}\n```"
        mock_cls.return_value.messages.create.return_value = _mock_message(fenced)
        result = analyze_pipeline("test", "zapier")
        assert result == VALID_RESPONSE


# ── Error handling ───────────────────────────────────────────────────


class TestErrorHandling:
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": ""})
    def test_missing_api_key_raises(self):
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            analyze_pipeline("test", "zapier")

    @patch("modules.ecg.core.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "fake-key"})
    def test_malformed_json_raises(self, mock_cls):
        mock_cls.return_value.messages.create.return_value = _mock_message(
            "this is not json"
        )
        with pytest.raises(ValueError, match="malformed JSON"):
            analyze_pipeline("test", "zapier")

    @patch("modules.ecg.core.anthropic.Anthropic")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "fake-key"})
    def test_missing_keys_raises(self, mock_cls):
        incomplete = {"edge_cases": [], "summary": "ok"}
        mock_cls.return_value.messages.create.return_value = _mock_message(
            json.dumps(incomplete)
        )
        with pytest.raises(ValueError, match="missing keys"):
            analyze_pipeline("test", "zapier")
