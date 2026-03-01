from unittest.mock import patch

import anthropic
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

HEADERS = {"X-API-Key": "test-key", "Content-Type": "application/json"}

VALID_RESULT = {
    "edge_cases": ["Rate limit hit"],
    "failure_scenarios": ["API timeout"],
    "assumptions_flagged": ["Always-on connectivity"],
    "summary": "Moderate risk pipeline.",
}


# ── Happy path ───────────────────────────────────────────────────────


class TestAnalyzeEndpoint:
    @patch("modules.ecg.router.analyze_pipeline", return_value=VALID_RESULT)
    def test_valid_request(self, mock_analyze):
        resp = client.post("/ecg/analyze", json={
            "pipeline_description": "Send email on new row",
            "platform": "zapier",
        }, headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["edge_cases"] == VALID_RESULT["edge_cases"]
        assert body["summary"] == VALID_RESULT["summary"]

    @patch("modules.ecg.router.analyze_pipeline", return_value=VALID_RESULT)
    def test_with_context(self, mock_analyze):
        resp = client.post("/ecg/analyze", json={
            "pipeline_description": "Send email",
            "platform": "make",
            "context": "High volume expected",
        }, headers=HEADERS)
        assert resp.status_code == 200
        mock_analyze.assert_called_once_with(
            pipeline_description="Send email",
            platform="make",
            context="High volume expected",
        )

    @patch("modules.ecg.router.analyze_pipeline", return_value=VALID_RESULT)
    def test_all_platforms_accepted(self, mock_analyze):
        for platform in ["zapier", "make", "n8n"]:
            resp = client.post("/ecg/analyze", json={
                "pipeline_description": "test",
                "platform": platform,
            }, headers=HEADERS)
            assert resp.status_code == 200


# ── Request validation ───────────────────────────────────────────────


class TestRequestValidation:
    @patch("modules.ecg.router.analyze_pipeline", return_value=VALID_RESULT)
    def test_empty_description_returns_400(self, mock_analyze):
        resp = client.post("/ecg/analyze", json={
            "pipeline_description": "   ",
            "platform": "zapier",
        }, headers=HEADERS)
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    @patch("modules.ecg.router.analyze_pipeline", return_value=VALID_RESULT)
    def test_too_long_description_returns_400(self, mock_analyze):
        resp = client.post("/ecg/analyze", json={
            "pipeline_description": "x" * 5001,
            "platform": "zapier",
        }, headers=HEADERS)
        assert resp.status_code == 400
        assert "5000" in resp.json()["detail"]

    def test_invalid_platform_returns_422(self):
        resp = client.post("/ecg/analyze", json={
            "pipeline_description": "test",
            "platform": "invalid",
        }, headers=HEADERS)
        assert resp.status_code == 422

    def test_missing_description_returns_422(self):
        resp = client.post("/ecg/analyze", json={
            "platform": "zapier",
        }, headers=HEADERS)
        assert resp.status_code == 422


# ── Error propagation ────────────────────────────────────────────────


class TestErrorPropagation:
    @patch("modules.ecg.router.analyze_pipeline", side_effect=ValueError("malformed JSON"))
    def test_value_error_returns_500(self, mock_analyze):
        resp = client.post("/ecg/analyze", json={
            "pipeline_description": "test",
            "platform": "zapier",
        }, headers=HEADERS)
        assert resp.status_code == 500
        assert "malformed JSON" in resp.json()["detail"]

    @patch("modules.ecg.router.analyze_pipeline",
           side_effect=anthropic.APIConnectionError(request=None))
    def test_api_error_returns_502(self, mock_analyze):
        resp = client.post("/ecg/analyze", json={
            "pipeline_description": "test",
            "platform": "zapier",
        }, headers=HEADERS)
        assert resp.status_code == 502


# ── Auth ─────────────────────────────────────────────────────────────


class TestAuth:
    def test_missing_api_key_returns_422(self):
        resp = client.post("/ecg/analyze", json={
            "pipeline_description": "test",
            "platform": "zapier",
        })
        assert resp.status_code == 422

    def test_invalid_api_key_returns_401(self):
        resp = client.post("/ecg/analyze", json={
            "pipeline_description": "test",
            "platform": "zapier",
        }, headers={"X-API-Key": "wrong-key", "Content-Type": "application/json"})
        assert resp.status_code == 401
