"""The one guard v1 has: a shared static token on write endpoints, checked
only when COACH_API_TOKEN is actually set. There is no per-user auth --
anyone who can reach this API can read the whole team's data. Acceptable for
a trusted-network pilot; real auth is out of scope for v1 (see coach/README.md).
"""
from __future__ import annotations

from fastapi import Header, HTTPException

import config


async def require_token(x_coach_token: str | None = Header(default=None)) -> None:
    if not config.API_TOKEN:
        return
    if x_coach_token != config.API_TOKEN:
        raise HTTPException(status_code=401, detail="missing or invalid X-Coach-Token")
