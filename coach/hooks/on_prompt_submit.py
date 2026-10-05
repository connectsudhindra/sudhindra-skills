#!/usr/bin/env python3
"""UserPromptSubmit hook: local, zero-network blocking decision + best-effort
persistence. Wired via coach/hooks/hooks.json, so this runs on every prompt
submitted in a session where the sudhindra-skills plugin is installed.

Contract with Claude Code (see coach/README.md for the sourced details):
exit 0 with nothing printed lets the prompt through silently. Exit 0 while
printing `{"decision":"block","reason":"..."}` to stdout blocks the prompt
and ERASES it, showing `reason` to the user -- there is no interactive
checklist UI or in-place edit available to a hook, so the reason text IS
the coaching. Every other path in this script also exits 0: a coaching
system that can crash the terminal or eat a prompt on its own bugs is worse
than no coaching system at all.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "api"))
sys.path.insert(0, str(Path(__file__).parent / "lib"))

RESUBMIT_CACHE_TTL_SECONDS = 5 * 60
RESUBMIT_CACHE_PATH = Path(__file__).parent.parent / "logs" / "recent_blocks.json"

# Short conversational continuations aren't asks worth scoring or blocking --
# scoring "yes" as a weak GCCF prompt would just be noise.
_CONTINUATION_PREFIXES = (
    "yes", "no", "ok", "okay", "sure", "continue", "go", "go ahead", "that",
    "looks good", "lgtm", "do it", "fix it", "try again", "keep going",
    "sounds good", "yep", "yeah", "correct", "right", "proceed",
)


def _is_continuation(prompt: str) -> bool:
    words = prompt.strip().split()
    if len(words) >= 6:
        return False
    lower = prompt.strip().lower()
    return any(lower == p or lower.startswith(p + " ") for p in _CONTINUATION_PREFIXES)


def _is_slash_command(prompt: str) -> bool:
    # An explicit skill/command invocation hands its args to that skill --
    # often one (like /interview) whose whole job is sharpening a rough ask.
    # Gating it on GCCF would block the very tool meant to fix the prompt.
    stripped = prompt.lstrip()
    return stripped.startswith("/") and len(stripped) > 1 and not stripped[1].isspace()


def _normalize(text: str) -> str:
    return " ".join(text.split()).strip().lower()


def _prompt_hash(session_id: str, text: str) -> str:
    return hashlib.sha256(f"{session_id}:{_normalize(text)}".encode("utf-8")).hexdigest()


def _was_recently_blocked(prompt_hash: str) -> bool:
    try:
        with RESUBMIT_CACHE_PATH.open("r", encoding="utf-8") as f:
            cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return False
    entry = cache.get(prompt_hash)
    if entry is None:
        return False
    return (time.time() - entry) < RESUBMIT_CACHE_TTL_SECONDS


def _record_block(prompt_hash: str) -> None:
    now = time.time()
    try:
        with RESUBMIT_CACHE_PATH.open("r", encoding="utf-8") as f:
            cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        cache = {}
    cache = {h: t for h, t in cache.items() if (now - t) < RESUBMIT_CACHE_TTL_SECONDS}
    cache[prompt_hash] = now
    try:
        RESUBMIT_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with RESUBMIT_CACHE_PATH.open("w", encoding="utf-8") as f:
            json.dump(cache, f)
    except OSError:
        pass


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # unreadable stdin -- never block on a parse failure

    prompt_text = payload.get("prompt", "") or ""
    session_id = payload.get("session_id", "") or "unknown-session"
    cwd = payload.get("cwd", ".") or "."

    try:
        import config as hook_config  # coach/hooks/lib/config.py

        cfg = hook_config.load_config()
    except Exception:
        return 0  # config layer itself failed -- fail open, never block

    if not cfg.get("enabled", True) or cfg.get("coaching_mode") == "off":
        return 0

    if not prompt_text.strip():
        return 0

    is_scorable = not (_is_continuation(prompt_text) or _is_slash_command(prompt_text))

    score = None
    if is_scorable:
        try:
            from scoring.heuristic import score_prompt  # coach/api/scoring/heuristic.py

            score = score_prompt(prompt_text)
        except Exception:
            is_scorable = False  # scorer itself failed -- treat as unscored, still persist attempt

    if is_scorable and score is not None and cfg.get("coaching_mode") == "in_session":
        block_floor = float(cfg.get("block_floor", 35))
        if score.composite < block_floor:
            prompt_hash = _prompt_hash(session_id, prompt_text)
            if not _was_recently_blocked(prompt_hash):
                _record_block(prompt_hash)
                try:
                    from services.coaching import block_reason  # coach/api/services/coaching.py

                    reason = block_reason(score, block_floor)
                except Exception:
                    reason = (
                        f"This prompt scored {score.composite:.0f}/100 on GCCF "
                        f"(floor: {block_floor:.0f}). Sharpen it, or send it again "
                        "unchanged to proceed anyway."
                    )
                print(json.dumps({"decision": "block", "reason": reason}))
                return 0
            # Recently blocked and resubmitted unchanged -- let it through, no re-block.

    # Persistence + leveling: best-effort, never blocks, never raises past this point.
    try:
        from client import post_json  # coach/hooks/lib/client.py

        post_json(
            f"{cfg['api_base_url']}/prompts",
            {
                "user_email": cfg.get("user_email") or hook_config.derive_user_email(cwd),
                "user_name": cfg.get("user_name"),
                "claude_session_id": session_id,
                "prompt_text": prompt_text,
                "is_scorable": is_scorable,
                "request_llm_score": True,
            },
            token=cfg.get("api_token"),
            timeout=2.0,
        )
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
