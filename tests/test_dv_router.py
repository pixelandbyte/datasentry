import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

HEADERS = {"X-API-Key": "test-key", "Content-Type": "application/json"}


# ── Happy path ───────────────────────────────────────────────────────


class TestValidateEndpoint:
    def test_valid_data_returns_200(self):
        resp = client.post("/dv/validate", json={
            "data": {"email": "test@example.com"},
            "rules": [{"field": "email", "type": "email", "required": True}],
        }, headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is True
        assert body["errors"] == []

    def test_invalid_data_returns_200_with_errors(self):
        resp = client.post("/dv/validate", json={
            "data": {"email": "not-an-email"},
            "rules": [{"field": "email", "type": "email", "required": True}],
        }, headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is False
        assert len(body["errors"]) == 1
        assert body["errors"][0]["field"] == "email"


# ── Error cases ──────────────────────────────────────────────────────


class TestErrorCases:
    def test_empty_rules_returns_400(self):
        resp = client.post("/dv/validate", json={
            "data": {},
            "rules": [],
        }, headers=HEADERS)
        assert resp.status_code == 400
        assert "rules" in resp.json()["detail"].lower()

    def test_invalid_rule_type_returns_400(self):
        resp = client.post("/dv/validate", json={
            "data": {},
            "rules": [{"field": "x", "type": "bogus"}],
        }, headers=HEADERS)
        assert resp.status_code == 400
        assert "invalid rule type" in resp.json()["detail"].lower()

    def test_missing_data_field_returns_422(self):
        resp = client.post("/dv/validate", json={
            "rules": [{"field": "x", "type": "string"}],
        }, headers=HEADERS)
        assert resp.status_code == 422

    def test_missing_rules_field_returns_422(self):
        resp = client.post("/dv/validate", json={
            "data": {},
        }, headers=HEADERS)
        assert resp.status_code == 422


# ── Auth ─────────────────────────────────────────────────────────────


class TestAuth:
    def test_missing_api_key_returns_422(self):
        resp = client.post("/dv/validate", json={
            "data": {},
            "rules": [{"field": "x", "type": "string"}],
        })
        assert resp.status_code == 422

    def test_invalid_api_key_returns_401(self):
        resp = client.post("/dv/validate", json={
            "data": {},
            "rules": [{"field": "x", "type": "string"}],
        }, headers={"X-API-Key": "wrong-key", "Content-Type": "application/json"})
        assert resp.status_code == 401


# ── Multiple fields ──────────────────────────────────────────────────


class TestMultipleFields:
    def test_mixed_pass_and_fail(self):
        resp = client.post("/dv/validate", json={
            "data": {"name": "Alice", "age": "not-a-number"},
            "rules": [
                {"field": "name", "type": "string", "required": True},
                {"field": "age", "type": "number", "required": True},
            ],
        }, headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is False
        assert len(body["errors"]) == 1
        assert body["errors"][0]["field"] == "age"

    def test_optional_missing_field_passes(self):
        resp = client.post("/dv/validate", json={
            "data": {},
            "rules": [{"field": "nickname", "type": "string", "required": False}],
        }, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["valid"] is True
