#!/usr/bin/env python3
"""SessionEnd hook. Its total timeout budget across ALL hooks registered for
this event is ~1.5s -- nowhere near enough for a network round trip to the
API, let alone the DB work behind it. So this script does the absolute
minimum: read stdin, spawn a fully detached worker process, exit. The real
work happens in lib/end_session_worker.py, outside any hook timeout.

(Belt and suspenders: main.py also runs a periodic sweep that closes out any
session whose SessionEnd never fired at all -- crash, force-quit -- so
end-of-session coaching doesn't depend on this hook firing reliably either.)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

WORKER = Path(__file__).parent / "lib" / "end_session_worker.py"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    session_id = payload.get("session_id", "") or ""
    cwd = payload.get("cwd", ".") or "."

    if not session_id:
        return 0

    try:
        subprocess.Popen(
            [sys.executable, str(WORKER), session_id, cwd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
