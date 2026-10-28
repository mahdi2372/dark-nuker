"""Secret storage using .env and OS keyring."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    import keyring
except Exception:  # pragma: no cover - optional at import time
    keyring = None  # type: ignore[assignment]

SERVICE_NAME = "discord-nuke-bot"


def load_dotenv(path: str | Path = ".env") -> None:
    p = Path(path)
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_token(mode: str, profile: str = "default", cli_token: Optional[str] = None) -> Optional[str]:
    if cli_token:
        return cli_token.strip() or None
    env_key = "BOT_TOKEN" if mode == "bot" else "USER_TOKEN"
    if os.getenv(env_key):
        return os.getenv(env_key)
    if keyring is not None:
        try:
            value = keyring.get_password(SERVICE_NAME, f"{mode}:{profile}")
            if value:
                return value
        except Exception:
            return None
    return None


def set_token(mode: str, token: str, profile: str = "default") -> bool:
    if keyring is None:
        return False
    try:
        keyring.set_password(SERVICE_NAME, f"{mode}:{profile}", token)
        return True
    except Exception:
        return False


def delete_token(mode: str, profile: str = "default") -> bool:
    if keyring is None:
        return False
    try:
        keyring.delete_password(SERVICE_NAME, f"{mode}:{profile}")
        return True
    except Exception:
        return False


import json

REGISTRY_PATH = Path("profiles.json")


def _load_registry() -> dict[str, list[str]]:
    if not REGISTRY_PATH.exists():
        return {"bot": [], "selfbot": [], "user": []}
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"bot": [], "selfbot": [], "user": []}
    for mode in ("bot", "selfbot", "user"):
        data.setdefault(mode, [])
    return data


def _save_registry(registry: dict[str, list[str]]) -> None:
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def list_profiles(mode: str) -> list[str]:
    registry = _load_registry()
    return sorted(set(registry.get(mode, [])))


def save_profile(mode: str, profile: str, token: str) -> bool:
    if not set_token(mode, token, profile):
        return False
    registry = _load_registry()
    registry.setdefault(mode, [])
    if profile not in registry[mode]:
        registry[mode].append(profile)
    _save_registry(registry)
    return True


def delete_profile(mode: str, profile: str) -> bool:
    deleted = delete_token(mode, profile)
    registry = _load_registry()
    if mode in registry and profile in registry[mode]:
        registry[mode].remove(profile)
        _save_registry(registry)
    return deleted
