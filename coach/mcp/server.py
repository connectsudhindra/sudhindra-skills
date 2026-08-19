"""MCP server for the GCCF coach -- exposes every capability the REST API
has (coach/api/) as an MCP tool, over Streamable HTTP, so any MCP client
(Claude Desktop, Claude Code via `claude mcp add`, a custom agent) can read
coaching data or score a prompt directly, without going through the
dashboard or the hooks.

This is a thin adapter, not a second implementation: every tool below is a
direct HTTP call to the same FastAPI backend the hooks and dashboard use.
There is exactly one source of truth for scoring, leveling, and progress
logic (coach/api/); this file owns none of it. See coach/README.md's
"What data gets sent, and how often" for the wire format each of these
tools produces on the API side.

Run via `python server.py` (reads COACH_API_BASE_URL, COACH_API_TOKEN,
COACH_MCP_HOST, COACH_MCP_PORT from the environment) or via
coach/docker-compose.yml's `mcp` service.
"""
from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer

API_BASE_URL = os.environ.get("COACH_API_BASE_URL", "http://localhost:8787")
API_TOKEN = os.environ.get("COACH_API_TOKEN", "")
MCP_HOST = os.environ.get("COACH_MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("COACH_MCP_PORT", "8788"))

app = MCPServer(
    "gccf-coach",
    instructions=(
        "Tools for the GCCF (Goal/Context/Constraints/Format) prompt coach: score a prompt "
        "before sending it, read a user's or team's coaching data, and check whether they're "
        "actually improving. See coach/README.md in the sudhindra-skills repo for the full "
        "design -- the scoring rules, the level thresholds, and what each tool's data means."
    ),
)


def _headers() -> dict[str, str]:
    return {"X-Coach-Token": API_TOKEN} if API_TOKEN else {}


async def _request(method: str, path: str, **kwargs: Any) -> dict | list:
    """Every tool below funnels through here so error handling (a clear
    message back to the MCP client, not a raw exception) lives in one
    place. Timeouts are deliberately generous (10s) compared to the hooks'
    -- an MCP tool call is a human or agent waiting on a direct answer, not
    a fire-and-forget background signal, so it's fine to actually wait."""
    url = f"{API_BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(method, url, headers=_headers(), **kwargs)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        raise RuntimeError(f"{method} {path} -> HTTP {exc.response.status_code}: {detail}") from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"{method} {path} -> could not reach the coach API at {API_BASE_URL}: {exc}") from exc


async def _request_list(method: str, path: str, **kwargs: Any) -> dict:
    """Same as _request, but for endpoints that return a bare JSON array.
    Wrapped as {"items": [...], "count": N} rather than returned as a raw
    list -- the MCP SDK represents a list return value as one content
    block *per item*, which is easy for a client to misread as "only the
    first result" (this bit an early manual test of this exact server).
    One object, one content block, every time."""
    items = await _request(method, path, **kwargs)
    return {"items": items, "count": len(items)}


# --- Scoring -----------------------------------------------------------


@app.tool()
async def score_prompt(prompt_text: str, include_llm: bool = False) -> dict:
    """Score a draft prompt on GCCF (Goal/Context/Constraints/Format) WITHOUT
    persisting anything -- no row is written, no user's level is affected.
    Use this to check a prompt before sending it. Returns the heuristic
    score (always) and, if include_llm=True, a live Claude Haiku comparison
    score (requires ANTHROPIC_API_KEY configured on the API; silently
    omitted with an error note if unavailable). Each dimension in the
    result carries a status (strong/developing/weak), the specific issue
    if not strong, and one concrete tip to fix it -- not just a number."""
    return await _request("POST", "/score", json={"prompt_text": prompt_text, "include_llm": include_llm})


@app.tool()
async def submit_prompt(
    user_email: str,
    claude_session_id: str,
    prompt_text: str,
    user_name: str | None = None,
    is_scorable: bool = True,
    request_llm_score: bool = True,
) -> dict:
    """Score AND PERSIST a prompt for a real user/session -- this is the
    same endpoint the UserPromptSubmit hook calls for every prompt in a
    real Claude Code session, and it DOES affect the user's rolling level.
    Use score_prompt instead for a check that shouldn't count. Creates the
    user and session on first sight if they don't exist yet."""
    return await _request(
        "POST",
        "/prompts",
        json={
            "user_email": user_email,
            "user_name": user_name,
            "claude_session_id": claude_session_id,
            "prompt_text": prompt_text,
            "is_scorable": is_scorable,
            "request_llm_score": request_llm_score,
        },
    )


@app.tool()
async def end_session(user_email: str, claude_session_id: str) -> dict:
    """Close a session -- computes its session_level and, if the user is in
    end_of_session coaching mode, queues their summary for next time. This
    is the same call the SessionEnd hook's detached worker makes."""
    return await _request(
        "POST", "/sessions/end", json={"user_email": user_email, "claude_session_id": claude_session_id}
    )


# --- Users ---------------------------------------------------------------


@app.tool()
async def list_users(level: int | None = None, team_id: str | None = None) -> dict:
    """List every user the coach knows about, optionally filtered to one
    level (1-5) and/or one team. Each entry has their current level,
    rolling GCCF composite, scored prompt count, and coaching mode."""
    params = {k: v for k, v in {"level": level, "team_id": team_id}.items() if v is not None}
    return await _request_list("GET", "/users", params=params)


@app.tool()
async def get_user(user_id: str) -> dict:
    """Full detail for one user: summary, level_history (every level-up
    with its timestamp), and their all-time GCCF averages per dimension."""
    return await _request("GET", f"/users/{user_id}")


@app.tool()
async def get_user_by_email(email: str) -> dict:
    """Resolve a user by their email -- the same lookup the dashboard's
    'My Coaching' page uses. Useful when you have an email but not a
    user_id yet."""
    return await _request("GET", f"/users/by-email/{email}")


@app.tool()
async def get_user_prompts(user_id: str, limit: int = 50, offset: int = 0) -> dict:
    """A user's prompt history, most recent first, each with its full
    per-method (heuristic and, if available, llm) score breakdown --
    including the structured dimension_feedback (issue codes, messages,
    tips) behind each number."""
    return await _request_list("GET", f"/users/{user_id}/prompts", params={"limit": limit, "offset": offset})


@app.tool()
async def get_user_sessions(user_id: str, limit: int = 30) -> dict:
    """A user's sessions, most recent first: start/end time, the level
    that session landed at, prompt count, and average composite. The unit
    between one prompt and a user's whole history."""
    return await _request_list("GET", f"/users/{user_id}/sessions", params={"limit": limit})


@app.tool()
async def get_user_feedback(user_id: str, limit: int = 20) -> dict:
    """The coaching_feedback a user has actually received -- in-session
    block reasons and end-of-session summaries, most recent first."""
    return await _request_list("GET", f"/users/{user_id}/feedback", params={"limit": limit})


@app.tool()
async def get_user_progress(user_id: str) -> dict:
    """Is this specific person actually getting better, dimension by
    dimension -- compares their most recent 15 scored prompts against the
    15 before that. Returns a direction (improving/flat/declining) per
    dimension, the most common issue still holding a weak dimension back,
    and a one-line headline summarizing all of it."""
    return await _request("GET", f"/users/{user_id}/progress")


# --- Sessions --------------------------------------------------------------


@app.tool()
async def get_session(session_id: str) -> dict:
    """Full detail for one session: its summary plus every prompt in it,
    each with a complete score breakdown."""
    return await _request("GET", f"/sessions/{session_id}")


# --- Teams -----------------------------------------------------------------


@app.tool()
async def list_teams() -> dict:
    """Every team, with member count, average level, and average rolling
    GCCF composite -- for cross-team comparison at a glance."""
    return await _request_list("GET", "/teams")


@app.tool()
async def get_team_progress(team_id: str) -> dict:
    """Is this team actually getting better, dimension by dimension -- the
    team-scoped twin of get_user_progress. Pooled across the team's most
    recent 15 scored prompts, so it skews toward whoever's most active."""
    return await _request("GET", f"/teams/{team_id}/progress")


# --- Reference / dashboard-wide -------------------------------------------


@app.tool()
async def list_levels() -> dict:
    """The five GCCF levels in order (Operator, Composer, Delegator,
    Orchestrator, Architect), each with its rolling-composite threshold,
    description, and the tip for reaching the next one."""
    return await _request_list("GET", "/levels")


@app.tool()
async def get_level_distribution() -> dict:
    """How many users currently sit at each of the five levels."""
    return await _request_list("GET", "/dashboard/level-distribution")


@app.tool()
async def get_scoring_comparison() -> dict:
    """Heuristic-vs-LLM agreement across every prompt scored by both
    methods -- sample size, mean absolute difference, and the raw pairs.
    An empty result means no prompt has a real or simulated LLM score yet."""
    return await _request("GET", "/dashboard/scoring-comparison")


@app.tool()
async def get_trend(team_id: str | None = None, days: int = 30) -> dict:
    """Daily average GCCF score per dimension over the trailing `days` --
    org-wide, or scoped to one team_id. This is what shows WHICH dimension
    is actually moving over time, not just a flat current snapshot."""
    params: dict[str, Any] = {"days": days}
    if team_id is not None:
        params["team_id"] = team_id
    return await _request("GET", "/dashboard/trend", params=params)


if __name__ == "__main__":
    app.run(transport="streamable-http", host=MCP_HOST, port=MCP_PORT)
