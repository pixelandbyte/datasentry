import pytest

from modules.dv.core import validate_data


# ── Helpers ──────────────────────────────────────────────────────────


def rule(field, type_, **kwargs):
    return {"field": field, "type": type_, **kwargs}


def errors_for(result):
    return {e["field"]: e["issue"] for e in result["errors"]}


# ── Type: string ─────────────────────────────────────────────────────


class TestStringType:
    def test_valid_string(self):
        r = validate_data({"name": "Alice"}, [rule("name", "string")])
        assert r["valid"] is True

    def test_empty_string_fails(self):
        r = validate_data({"name": ""}, [rule("name", "string")])
        assert r["valid"] is False
        assert "empty" in errors_for(r)["name"].lower()

    def test_non_string_fails(self):
        r = validate_data({"name": 123}, [rule("name", "string")])
        assert r["valid"] is False


# ── Type: number ─────────────────────────────────────────────────────


class TestNumberType:
    def test_integer(self):
        r = validate_data({"age": 25}, [rule("age", "number")])
        assert r["valid"] is True

    def test_float(self):
        r = validate_data({"price": 9.99}, [rule("price", "number")])
        assert r["valid"] is True

    def test_string_fails(self):
        r = validate_data({"age": "old"}, [rule("age", "number")])
        assert r["valid"] is False

    def test_bool_is_not_number(self):
        r = validate_data({"age": True}, [rule("age", "number")])
        assert r["valid"] is False


# ── Type: boolean ────────────────────────────────────────────────────


class TestBooleanType:
    def test_true(self):
        r = validate_data({"active": True}, [rule("active", "boolean")])
        assert r["valid"] is True

    def test_false(self):
        r = validate_data({"active": False}, [rule("active", "boolean")])
        assert r["valid"] is True

    def test_string_fails(self):
        r = validate_data({"active": "yes"}, [rule("active", "boolean")])
        assert r["valid"] is False


# ── Type: email ──────────────────────────────────────────────────────


class TestEmailType:
    def test_valid_email(self):
        r = validate_data({"email": "user@example.com"}, [rule("email", "email")])
        assert r["valid"] is True

    def test_missing_at(self):
        r = validate_data({"email": "userexample.com"}, [rule("email", "email")])
        assert r["valid"] is False

    def test_missing_domain(self):
        r = validate_data({"email": "user@"}, [rule("email", "email")])
        assert r["valid"] is False

    def test_non_string_fails(self):
        r = validate_data({"email": 42}, [rule("email", "email")])
        assert r["valid"] is False


# ── Type: url ────────────────────────────────────────────────────────


class TestUrlType:
    def test_valid_https(self):
        r = validate_data({"url": "https://example.com"}, [rule("url", "url")])
        assert r["valid"] is True

    def test_valid_http(self):
        r = validate_data({"url": "http://example.com/path"}, [rule("url", "url")])
        assert r["valid"] is True

    def test_missing_scheme(self):
        r = validate_data({"url": "example.com"}, [rule("url", "url")])
        assert r["valid"] is False

    def test_bare_string_fails(self):
        r = validate_data({"url": "not a url"}, [rule("url", "url")])
        assert r["valid"] is False


# ── Type: date ───────────────────────────────────────────────────────


class TestDateType:
    def test_iso_date(self):
        r = validate_data({"d": "2024-01-15"}, [rule("d", "date")])
        assert r["valid"] is True

    def test_iso_datetime(self):
        r = validate_data({"d": "2024-01-15T10:30:00"}, [rule("d", "date")])
        assert r["valid"] is True

    def test_iso_datetime_z(self):
        r = validate_data({"d": "2024-01-15T10:30:00Z"}, [rule("d", "date")])
        assert r["valid"] is True

    def test_invalid_date(self):
        r = validate_data({"d": "not-a-date"}, [rule("d", "date")])
        assert r["valid"] is False

    def test_non_string_fails(self):
        r = validate_data({"d": 20240115}, [rule("d", "date")])
        assert r["valid"] is False


# ── Type: phone ──────────────────────────────────────────────────────


class TestPhoneType:
    def test_digits_only(self):
        r = validate_data({"p": "5551234567"}, [rule("p", "phone")])
        assert r["valid"] is True

    def test_with_country_code(self):
        r = validate_data({"p": "+1 555-123-4567"}, [rule("p", "phone")])
        assert r["valid"] is True

    def test_with_parens(self):
        r = validate_data({"p": "(555) 123-4567"}, [rule("p", "phone")])
        assert r["valid"] is True

    def test_letters_fail(self):
        r = validate_data({"p": "call me maybe"}, [rule("p", "phone")])
        assert r["valid"] is False


# ── Required / optional ─────────────────────────────────────────────


class TestRequiredOptional:
    def test_required_missing_fails(self):
        r = validate_data({}, [rule("name", "string", required=True)])
        assert r["valid"] is False
        assert r["errors"][0]["value_received"] == "null"

    def test_required_none_fails(self):
        r = validate_data({"name": None}, [rule("name", "string", required=True)])
        assert r["valid"] is False

    def test_optional_missing_skipped(self):
        r = validate_data({}, [rule("name", "string", required=False)])
        assert r["valid"] is True
        assert r["errors"] == []

    def test_optional_present_still_validated(self):
        r = validate_data({"name": 123}, [rule("name", "string", required=False)])
        assert r["valid"] is False


# ── Rule options ─────────────────────────────────────────────────────


class TestRuleOptions:
    def test_allowed_values_pass(self):
        r = validate_data(
            {"status": "active"},
            [rule("status", "string", allowed_values=["active", "inactive"])],
        )
        assert r["valid"] is True

    def test_allowed_values_fail(self):
        r = validate_data(
            {"status": "deleted"},
            [rule("status", "string", allowed_values=["active", "inactive"])],
        )
        assert r["valid"] is False
        assert "allowed" in errors_for(r)["status"].lower()

    def test_min_length_pass(self):
        r = validate_data({"name": "Alice"}, [rule("name", "string", min_length=3)])
        assert r["valid"] is True

    def test_min_length_fail(self):
        r = validate_data({"name": "Al"}, [rule("name", "string", min_length=3)])
        assert r["valid"] is False

    def test_max_length_pass(self):
        r = validate_data({"name": "Alice"}, [rule("name", "string", max_length=10)])
        assert r["valid"] is True

    def test_max_length_fail(self):
        r = validate_data(
            {"name": "A very long name indeed"},
            [rule("name", "string", max_length=5)],
        )
        assert r["valid"] is False

    def test_pattern_pass(self):
        r = validate_data(
            {"code": "ABC-123"},
            [rule("code", "string", pattern=r"^[A-Z]+-\d+$")],
        )
        assert r["valid"] is True

    def test_pattern_fail(self):
        r = validate_data(
            {"code": "abc"},
            [rule("code", "string", pattern=r"^[A-Z]+-\d+$")],
        )
        assert r["valid"] is False


# ── Multiple errors / no short-circuit ───────────────────────────────


class TestMultipleErrors:
    def test_all_fields_validated(self):
        """All fields checked even when earlier ones fail."""
        r = validate_data(
            {"email": "bad", "age": "old", "active": "nope"},
            [
                rule("email", "email", required=True),
                rule("age", "number", required=True),
                rule("active", "boolean", required=True),
            ],
        )
        assert r["valid"] is False
        failed_fields = {e["field"] for e in r["errors"]}
        assert failed_fields == {"email", "age", "active"}

    def test_summary_counts_fields(self):
        r = validate_data(
            {"a": "ok", "b": "bad"},
            [rule("a", "string"), rule("b", "number")],
        )
        assert "1 of 2" in r["summary"]

    def test_all_pass_summary(self):
        r = validate_data(
            {"a": "hello", "b": 5},
            [rule("a", "string"), rule("b", "number")],
        )
        assert "passed" in r["summary"].lower()


# ── value_received truncation ────────────────────────────────────────


class TestTruncation:
    def test_long_value_truncated(self):
        long_val = "x" * 200
        r = validate_data({"name": long_val}, [rule("name", "string", max_length=10)])
        err = r["errors"][0]
        assert len(err["value_received"]) == 100


# ── Invalid rule type ────────────────────────────────────────────────


class TestInvalidRuleType:
    def test_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid rule type"):
            validate_data({}, [rule("x", "bogus")])

    def test_unknown_type_in_mixed_rules(self):
        with pytest.raises(ValueError, match="Invalid rule type"):
            validate_data(
                {"a": "ok"},
                [rule("a", "string"), rule("b", "faketype")],
            )
