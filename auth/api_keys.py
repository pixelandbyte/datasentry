import os
from typing import Dict, List

from fastapi import Depends, Header, HTTPException


# Dev key store: maps API key string -> list of scopes.
# Loaded from environment: DS_API_KEYS="key1:ecg,dv;key2:bundle"
def _load_keys() -> Dict[str, List[str]]:
    raw = os.environ.get("DS_API_KEYS", "test-key:bundle")
    keys: Dict[str, List[str]] = {}
    for entry in raw.split(";"):
        entry = entry.strip()
        if not entry or ":" not in entry:
            continue
        key, scopes_str = entry.split(":", 1)
        keys[key.strip()] = [s.strip() for s in scopes_str.split(",")]
    return keys


def _get_api_key_scopes(x_api_key: str = Header()) -> List[str]:
    keys = _load_keys()
    scopes = keys.get(x_api_key)
    if scopes is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return scopes


def require_scope(scope: str):
    """Return a FastAPI dependency that checks the key has the given scope or 'bundle'."""

    def _check(scopes: List[str] = Depends(_get_api_key_scopes)) -> List[str]:
        if scope not in scopes and "bundle" not in scopes:
            raise HTTPException(
                status_code=401,
                detail=f"API key does not have '{scope}' scope",
            )
        return scopes

    return _check
