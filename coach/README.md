# coach/ — GCCF prompt coaching

Scores every prompt submitted in a Claude Code session on four dimensions — **G**oal, **C**ontext, **C**onstraints, **F**ormat — and tracks growth through five levels: **Operator → Composer → Delegator → Orchestrator → Architect**. Ships as part of installing the `sudhindra-skills` plugin: the hooks auto-register on install, and a first-run `SessionStart` writes working local defaults with no setup step required. See [`skills/workshop/levelset`](../skills/workshop/levelset/SKILL.md) to point at a shared team backend instead, and [`skills/workshop/standing`](../skills/workshop/standing/SKILL.md) for an on-demand "how am I doing" check.

## Running it locally

```bash
cd coach
cp .env.example .env   # fill in ANTHROPIC_API_KEY if you want LLM-comparison scoring
docker compose up -d
curl localhost:8787/health
```

That brings up Postgres (host port `5433`, deliberately not `5432` — avoids colliding with a dev's own local instance), the FastAPI backend (`8787`), and a Vite dev server for the dashboard (`5173`). Schema and the five seeded levels apply automatically on first boot via `docker-entrypoint-initdb.d`; for schema changes against an already-running database, add a file under `db/migrations/` and run `python db/migrate.py`.

Point a Claude Code session at this local stack by leaving `$CLAUDE_PLUGIN_DATA/coach/config.json`'s `api_base_url` at its default (`http://localhost:8787`) — which is also what a fresh install writes automatically.

## Running the tests

```bash
cd coach/api
pip install -r requirements-dev.txt
pytest tests/test_heuristic.py            # pure, no DB needed
docker compose -f ../docker-compose.yml up -d postgres
pytest tests/test_level_engine.py         # needs the live Postgres above
```

## Why this is built the way it is

Three real constraints from Claude Code's hook system shaped every design decision here — worth reading before changing any of it.

**`UserPromptSubmit` can only block by erasing the prompt and showing a reason.** There's no interactive checklist, no in-place edit, nothing richer than plain text in `reason`. So the GCCF breakdown *is* the coaching on this path (`services/coaching.py`'s `block_reason`), and "revise, or send anyway" became **resubmit the same text unchanged** (tracked by a local hash cache with a 5-minute TTL in `hooks/on_prompt_submit.py`) rather than a new command syntax to learn.

**`SessionEnd`'s total hook budget across every hook registered for it is about 1.5 seconds** — nowhere near enough for a network round trip to the API, let alone the DB work behind it. `hooks/on_session_end.py` does the only thing that fits in that budget: spawn a fully detached worker process (`hooks/lib/end_session_worker.py`) and exit in under 50ms. The worker does the real `POST /sessions/end` outside any hook timeout, with nothing waiting on it either way. Because even a detached process can be skipped entirely by a crash or a force-quit, `api/main.py` also runs a five-minute sweep that closes out any session with no prompt in the last 20 minutes, so end-of-session coaching never depends on one hook firing reliably.

**The blocking decision never touches the network.** `hooks/on_prompt_submit.py` scores every prompt with the pure, stdlib-only function in `api/scoring/heuristic.py` (imported directly, zero I/O, sub-5ms) — the block/allow call is made entirely locally before anything is sent anywhere. Persistence and the (optional, slower) LLM comparison score happen via a best-effort POST with an aggressive ~2-second timeout that's silently dropped on any failure: no retry, no local queue. That's a real trade-off, stated plainly rather than hidden: **if the backend is unreachable when a prompt is submitted, that prompt's row is simply lost.** A local spool-and-flush would fix that, but it's a distinct reliability feature, not part of this version — every hook script in this system is written to fail open, because a coaching tool that can block or crash real work on its own bugs is worse than no coaching tool at all.

## Scoring: two independent methods, not one

`api/scoring/heuristic.py` (rule-based, instant, zero cost) and `api/scoring/llm.py` (Claude Haiku, ~300–800ms, needs `ANTHROPIC_API_KEY`) both score every prompt and both persist — one row each per `(prompt_id, scoring_method)` in `prompt_scores` — specifically so they can be compared (`GET /dashboard/scoring-comparison`) rather than forcing a single method to win. **Leveling always uses the heuristic score.** It's the one guaranteed to exist synchronously; the LLM score runs as a `BackgroundTask` after the API has already responded to the hook, so it's never on any latency-sensitive path and a user's level never depends on LLM availability, cost, or rate limits.

## Leveling policy

A user's rolling average over their last 20 scored prompts (`config.ROLLING_WINDOW_SIZE`) is compared against each level's `min_score`, and they need at least 5 scored prompts (`config.MIN_SCORABLE_PROMPTS_TO_LEVEL`) before ever leaving level 1 — one good prompt shouldn't jump someone to Architect. `users.current_level` is **sticky upward-only**: a bad stretch never demotes the badge. `sessions.session_level` still captures a per-session dip independently, so a rough session is visible without being punitive.

## What's deliberately out of scope for this version

**No real authentication.** A shared `X-Coach-Token` header on write endpoints (`COACH_API_TOKEN` in `.env`) is the only guard, and it's off by default. Anyone who can reach the API can read the whole team's data and could POST fabricated prompts. Fine for a trusted-network pilot; real per-user auth is a distinct follow-up, not an oversight.

**No delivery guarantee for individual prompts.** Covered above — a dropped POST means a lost row, not a retry.

**No demotion.** Also covered above, and deliberate: this is meant to read as growth-oriented, not punitive.
