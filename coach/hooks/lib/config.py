"""Local, per-machine config for the coaching hooks. Lives under
$CLAUDE_PLUGIN_DATA (a directory Claude Code guarantees persists across
plugin updates) so it survives a `claude plugin update`. Falls back to
~/.sudhindra-skills/coach/ when CLAUDE_PLUGIN_DATA isn't set -- e.g. when a
hook script is run by hand for testing, outside a real Claude Code session.

Every field here is safe to be missing: get_config() always returns a
usable dict, defaulting to "coaching is on, pointed at localhost" rather
than raising, because a hook that can't read its own config must still not
block the user's actual work.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "api_base_url": "http://localhost:8787",
    "user_email": None,
    "user_name": None,
    "coaching_mode": "in_session",
    "enabled": True,
    "block_floor": 35,
    "api_token": None,
    "notice_shown": False,
}


def config_dir() -> Path:
    base = os.environ.get("CLAUDE_PLUGIN_DATA")
    if base:
        return Path(base) / "coach"
    return Path.home() / ".sudhindra-skills" / "coach"


def config_path() -> Path:
    return config_dir() / "config.json"


def load_config() -> dict[str, Any]:
    path = config_path()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        merged = {**DEFAULTS, **data}
        return merged
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return dict(DEFAULTS)


def save_config(data: dict[str, Any]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp_path.replace(path)


def config_exists() -> bool:
    return config_path().exists()


def derive_user_email(cwd: str) -> str:
    """Best-effort local git identity; falls back to $USER@local. Never
    raises -- called from a hook's first-run path, where failure must still
    leave the hook able to proceed."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "config", "--get", "user.email"],
            cwd=cwd or ".",
            capture_output=True,
            text=True,
            timeout=2,
        )
        email = result.stdout.strip()
        # git config returning something doesn't guarantee it's a usable
        # email -- a malformed/placeholder value ("=", empty, no "@") is
        # worse than the $USER@local fallback, not better.
        if email and "@" in email and not email.startswith("="):
            return email
    except Exception:
        pass
    return f"{os.environ.get('USER', 'unknown')}@local"
