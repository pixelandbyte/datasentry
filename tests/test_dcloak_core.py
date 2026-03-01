import re

import pytest

from modules.dcloak.core import obfuscate_data


# ── Helpers ──────────────────────────────────────────────────────────


def field(name, strategy):
    return {"field": name, "strategy": strategy}


# ── Mask strategy ────────────────────────────────────────────────────


class TestMaskStrategy:
    def test_preserves_length(self):
        r = obfuscate_data({"email": "john@example.com"}, [field("email", "mask")])
        assert len(r["data"]["email"]) == len("john@example.com")

    def test_preserves_first_and_last_char(self):
        r = obfuscate_data({"email": "john@example.com"}, [field("email", "mask")])
        masked = r["data"]["email"]
        assert masked[0] == "j"
        assert masked[-1] == "m"

    def test_middle_replaced_with_stars(self):
        r = obfuscate_data({"val": "abcdef"}, [field("val", "mask")])
        masked = r["data"]["val"]
        assert masked == "a****f"

    def test_two_char_string_all_stars(self):
        r = obfuscate_data({"val": "ab"}, [field("val", "mask")])
        assert r["data"]["val"] == "**"

    def test_single_char_string(self):
        r = obfuscate_data({"val": "x"}, [field("val", "mask")])
        assert r["data"]["val"] == "*"

    def test_field_in_obfuscated_list(self):
        r = obfuscate_data({"val": "secret"}, [field("val", "mask")])
        assert "val" in r["obfuscated_fields"]


# ── Redact strategy ──────────────────────────────────────────────────


class TestRedactStrategy:
    def test_replaces_with_redacted(self):
        r = obfuscate_data({"ssn": "123-45-6789"}, [field("ssn", "redact")])
        assert r["data"]["ssn"] == "[REDACTED]"

    def test_works_on_non_string(self):
        r = obfuscate_data({"age": 42}, [field("age", "redact")])
        assert r["data"]["age"] == "[REDACTED]"


# ── Fake strategy ────────────────────────────────────────────────────


class TestFakeStrategy:
    def test_fake_email(self):
        r = obfuscate_data({"e": "john@example.com"}, [field("e", "fake")])
        fake_val = r["data"]["e"]
        assert "@placeholder.com" in fake_val
        assert fake_val.startswith("user_")

    def test_fake_phone(self):
        r = obfuscate_data({"p": "+1 555-123-4567"}, [field("p", "fake")])
        fake_val = r["data"]["p"]
        # Format preserved: starts with +, has spaces and dashes
        assert fake_val.startswith("+")
        assert " " in fake_val
        assert "-" in fake_val
        assert fake_val != "+1 555-123-4567"

    def test_fake_url(self):
        r = obfuscate_data({"u": "https://example.com/page"}, [field("u", "fake")])
        fake_val = r["data"]["u"]
        assert fake_val.startswith("https://placeholder.com/")

    def test_fake_name(self):
        r = obfuscate_data({"n": "Alice"}, [field("n", "fake")])
        fake_val = r["data"]["n"]
        assert isinstance(fake_val, str)
        assert len(fake_val) > 0
        # Should be a capitalised name
        assert fake_val[0].isupper()

    def test_fake_integer(self):
        r = obfuscate_data({"num": 500}, [field("num", "fake")])
        fake_val = r["data"]["num"]
        assert isinstance(fake_val, int)

    def test_fake_float(self):
        r = obfuscate_data({"num": 3.14}, [field("num", "fake")])
        fake_val = r["data"]["num"]
        assert isinstance(fake_val, float)

    def test_fake_string_fallback(self):
        r = obfuscate_data({"val": "some random text"}, [field("val", "fake")])
        fake_val = r["data"]["val"]
        assert isinstance(fake_val, str)
        assert len(fake_val) == len("some random text")
        assert fake_val != "some random text"


# ── Hash strategy ────────────────────────────────────────────────────


class TestHashStrategy:
    def test_returns_16_char_hex(self):
        r = obfuscate_data({"val": "secret"}, [field("val", "hash")])
        hashed = r["data"]["val"]
        assert len(hashed) == 16
        assert re.match(r"^[0-9a-f]{16}$", hashed)

    def test_deterministic(self):
        r1 = obfuscate_data({"v": "hello"}, [field("v", "hash")])
        r2 = obfuscate_data({"v": "hello"}, [field("v", "hash")])
        assert r1["data"]["v"] == r2["data"]["v"]

    def test_different_inputs_different_hashes(self):
        r1 = obfuscate_data({"v": "aaa"}, [field("v", "hash")])
        r2 = obfuscate_data({"v": "bbb"}, [field("v", "hash")])
        assert r1["data"]["v"] != r2["data"]["v"]


# ── Dot notation / nested fields ─────────────────────────────────────


class TestNestedFields:
    def test_dot_notation_resolves(self):
        data = {"user": {"email": "john@example.com"}}
        r = obfuscate_data(data, [field("user.email", "redact")])
        assert r["data"]["user"]["email"] == "[REDACTED]"
        assert "user.email" in r["obfuscated_fields"]

    def test_deeply_nested(self):
        data = {"a": {"b": {"c": "secret"}}}
        r = obfuscate_data(data, [field("a.b.c", "redact")])
        assert r["data"]["a"]["b"]["c"] == "[REDACTED]"

    def test_missing_nested_path_skipped(self):
        data = {"user": {"name": "Alice"}}
        r = obfuscate_data(data, [field("user.email", "redact")])
        assert "user.email" in r["skipped_fields"]
        assert r["data"]["user"]["name"] == "Alice"


# ── Skipped / missing fields ────────────────────────────────────────


class TestSkippedFields:
    def test_missing_field_added_to_skipped(self):
        r = obfuscate_data({"a": "hello"}, [field("missing", "mask")])
        assert "missing" in r["skipped_fields"]
        assert r["obfuscated_fields"] == []

    def test_mix_of_found_and_missing(self):
        r = obfuscate_data(
            {"a": "hello"},
            [field("a", "mask"), field("b", "redact")],
        )
        assert "a" in r["obfuscated_fields"]
        assert "b" in r["skipped_fields"]

    def test_skipped_summary(self):
        r = obfuscate_data(
            {"a": "hello"},
            [field("a", "mask"), field("b", "redact")],
        )
        assert "skipped 1" in r["summary"].lower()


# ── Empty fields list ────────────────────────────────────────────────


class TestEmptyFields:
    def test_returns_original_data(self):
        data = {"secret": "value", "other": 42}
        r = obfuscate_data(data, [])
        assert r["data"] == data

    def test_empty_obfuscated_and_skipped(self):
        r = obfuscate_data({"a": 1}, [])
        assert r["obfuscated_fields"] == []
        assert r["skipped_fields"] == []

    def test_summary_mentions_no_fields(self):
        r = obfuscate_data({}, [])
        assert "no fields" in r["summary"].lower()


# ── Invalid strategy ────────────────────────────────────────────────


class TestInvalidStrategy:
    def test_unknown_strategy_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown strategy"):
            obfuscate_data({"a": "hello"}, [field("a", "encrypt")])

    def test_empty_strategy_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown strategy"):
            obfuscate_data({"a": "hello"}, [field("a", "")])


# ── Unspecified fields pass through ──────────────────────────────────


class TestPassthrough:
    def test_unmentioned_fields_unchanged(self):
        data = {"secret": "value", "public": "visible", "count": 42}
        r = obfuscate_data(data, [field("secret", "redact")])
        assert r["data"]["public"] == "visible"
        assert r["data"]["count"] == 42

    def test_original_data_not_mutated(self):
        data = {"val": "original"}
        original_copy = {"val": "original"}
        obfuscate_data(data, [field("val", "redact")])
        assert data == original_copy
