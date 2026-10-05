#!/usr/bin/env python3
"""SessionStart hook: first-run config bootstrap, a local API health check
(starting the bundled Docker stack if it's down and pointed at localhost),
and end-of-session feedback delivery for users in `end_of_session` mode.

Always exits 0 -- see on_prompt_submit.py's module docstring for why every
hook in this system fails open rather than ever blocking a session start.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lib"))

COMPOSE_FILE = Path(__file__).parent.parent / "docker-compose.yml"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    cwd = payload.get("cwd", ".") or "."

    try:
        import config as hook_config
    except Exception:
        return 0

    context_lines: list[str] = []

    first_run = not hook_config.config_exists()
    if first_run:
        cfg = dict(hook_config.DEFAULTS)
        cfg["user_email"] = hook_config.derive_user_email(cwd)
        try:
            hook_config.save_config(cfg)
        except Exception:
            pass
        context_lines.append(
            "Tell the user, once, at the start of your first reply: "
            "\"GCCF prompt coaching is now active (mode: end_of_session -- nothing "
            "is blocked; a score summary shows up next session). Run the `levelset` "
            "skill any time to change the mode or turn it off.\""
        )
    else:
        cfg = hook_config.load_config()

    if not cfg.get("enabled", True) or cfg.get("coaching_mode") == "off":
        _emit(context_lines)
        return 0

    try:
        from client import get_json
    except Exception:
        _emit(context_lines)
        return 0

    api_base = cfg.get("api_base_url", "http://localhost:8787")
    health = get_json(f"{api_base}/health", timeout=1.0)

    if health is None and ("localhost" in api_base or "127.0.0.1" in api_base):
        if COMPOSE_FILE.exists():
            try:
                subprocess.Popen(
                    ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            except Exception:
                pass
            # Not awaited: first-ever image pull/build can take far longer than
            # any hook timeout allows. Prompts submitted while it warms up just
            # get silently dropped by on_prompt_submit.py's own health handling
            # (a failed POST is a no-op there), which is an acceptable v1 gap.

    if health is not None and cfg.get("coaching_mode") == "end_of_session" and cfg.get("user_email"):
        try:
            from urllib.parse import quote

            feedback = get_json(
                f"{api_base}/users/{quote(cfg['user_email'])}/undelivered-feedback", timeout=1.0
            )
        except Exception:
            feedback = None

        items = (feedback or {}).get("items") or []
        for item in items:
            text = item.get("feedback_text")
            if text:
                context_lines.append(
                    f'Tell the user this verbatim at the start of your first reply: "{text}"'
                )

    _emit(context_lines)
    return 0


def _emit(context_lines: list[str]) -> None:
    if not context_lines:
        return
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(context_lines),
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    sys.exit(main())
