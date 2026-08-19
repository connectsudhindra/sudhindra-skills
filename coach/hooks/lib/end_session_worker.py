#!/usr/bin/env python3
"""Runs detached from on_session_end.py, outside its 1.5s hook timeout, with
its own more generous budget. Nothing is waiting on this process either
way -- Claude Code has already moved on by the time it runs -- so a longer
timeout here costs nothing.

Usage: end_session_worker.py <session_id> <cwd>
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main() -> int:
    if len(sys.argv) < 3:
        return 0

    session_id, cwd = sys.argv[1], sys.argv[2]

    try:
        import config as hook_config
        from client import post_json
    except Exception:
        return 0

    try:
        cfg = hook_config.load_config()
    except Exception:
        return 0

    if not cfg.get("enabled", True) or cfg.get("coaching_mode") == "off":
        return 0

    post_json(
        f"{cfg['api_base_url']}/sessions/end",
        {
            "user_email": cfg.get("user_email") or hook_config.derive_user_email(cwd),
            "claude_session_id": session_id,
        },
        token=cfg.get("api_token"),
        timeout=5.0,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
