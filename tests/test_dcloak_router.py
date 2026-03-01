from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

HEADERS = {"X-API-Key": "test-key", "Content-Type": "application/json"}


# ── Happy path ───────────────────────────────────────────────────────


class TestObfuscateEndpoint:
    def test_mask_returns_200(self):
        resp = client.post("/dcloak/obfuscate", json={
            "data": {"email": "john@example.com"},
            "fields": [{"field": "email", "strategy": "mask"}],
        }, headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert "email" in body["obfuscated_fields"]
        assert body["data"]["email"] != "john@example.com"
        assert len(body["data"]["email"]) == len("john@example.com")

    def test_redact_returns_200(self):
        resp = client.post("/dcloak/obfuscate", json={
            "data": {"ssn": "123-45-6789"},
            "fields": [{"field": "ssn", "strategy": "redact"}],
        }, headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["data"]["ssn"] == "[REDACTED]"

    def test_all_four_strategies(self):
        resp = client.post("/dcloak/obfuscate", json={
            "data": {"a": "secret", "b": "secret", "c": "secret", "d": "secret"},
            "fields": [
                {"field": "a", "strategy": "mask"},
                {"field": "b", "strategy": "redact"},
                {"field": "c", "strategy": "fake"},
                {"field": "d", "strategy": "hash"},
            ],
        }, headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["obfuscated_fields"]) == 4
        assert body["skipped_fields"] == []

    def test_response_has_summary(self):
        resp = client.post("/dcloak/obfuscate", json={
            "data": {"val": "hello"},
            "fields": [{"field": "val", "strategy": "redact"}],
        }, headers=HEADERS)
        assert resp.status_code == 200
        assert "summary" in resp.json()


# ── Skipped fields ───────────────────────────────────────────────────


class TestSkippedFields:
    def test_missing_field_in_skipped(self):
        resp = client.post("/dcloak/obfuscate", json={
            "data": {"name": "Alice"},
            "fields": [
                {"field": "name", "strategy": "mask"},
                {"field": "missing", "strategy": "redact"},
            ],
        }, headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert "name" in body["obfuscated_fields"]
        assert "missing" in body["skipped_fields"]

    def test_nested_missing_field_in_skipped(self):
        resp = client.post("/dcloak/obfuscate", json={
            "data": {"user": {"name": "Alice"}},
            "fields": [{"field": "user.email", "strategy": "redact"}],
        }, headers=HEADERS)
        assert resp.status_code == 200
        assert "user.email" in resp.json()["skipped_fields"]


# ── Empty fields list ────────────────────────────────────────────────


class TestEmptyFields:
    def test_empty_fields_returns_original_data(self):
        resp = client.post("/dcloak/obfuscate", json={
            "data": {"secret": "value"},
            "fields": [],
        }, headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] == {"secret": "value"}
        assert body["obfuscated_fields"] == []


# ── Error cases ──────────────────────────────────────────────────────


class TestErrorCases:
    def test_unknown_strategy_returns_400(self):
        resp = client.post("/dcloak/obfuscate", json={
            "data": {"val": "hello"},
            "fields": [{"field": "val", "strategy": "encrypt"}],
        }, headers=HEADERS)
        assert resp.status_code == 400
        assert "unknown strategy" in resp.json()["detail"].lower()

    def test_missing_data_returns_422(self):
        resp = client.post("/dcloak/obfuscate", json={
            "fields": [{"field": "x", "strategy": "mask"}],
        }, headers=HEADERS)
        assert resp.status_code == 422

    def test_missing_fields_returns_422(self):
        resp = client.post("/dcloak/obfuscate", json={
            "data": {"x": "y"},
        }, headers=HEADERS)
        assert resp.status_code == 422


# ── Auth ─────────────────────────────────────────────────────────────


class TestAuth:
    def test_missing_api_key_returns_422(self):
        resp = client.post("/dcloak/obfuscate", json={
            "data": {"val": "hello"},
            "fields": [{"field": "val", "strategy": "mask"}],
        })
        assert resp.status_code == 422

    def test_invalid_api_key_returns_401(self):
        resp = client.post("/dcloak/obfuscate", json={
            "data": {"val": "hello"},
            "fields": [{"field": "val", "strategy": "mask"}],
        }, headers={"X-API-Key": "wrong-key", "Content-Type": "application/json"})
        assert resp.status_code == 401
