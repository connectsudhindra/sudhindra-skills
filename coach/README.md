# coach/ — GCCF prompt coaching

Scores every prompt submitted in a Claude Code session on four dimensions — **G**oal, **C**ontext, **C**onstraints, **F**ormat — and tracks growth through five levels: **Operator → Composer → Delegator → Orchestrator → Architect**. Ships as part of installing the `sudhindra-skills` plugin: the hooks auto-register on install, and a first-run `SessionStart` writes working local defaults with no setup step required. See [`skills/workshop/levelset`](../skills/workshop/levelset/SKILL.md) to point at a shared team backend instead, and [`skills/workshop/standing`](../skills/workshop/standing/SKILL.md) for an on-demand "how am I doing" check.

## What data gets sent, and how often

Event-driven, not polled — one HTTP call per Claude Code hook event, fired inline as it happens. No batching, no background upload queue.

| Trigger | Fires | Request |
| --- | --- | --- |
| `UserPromptSubmit` | Every prompt you submit | `POST /prompts` |
| `SessionEnd` | Once, when a session closes | `POST /sessions/end` (detached background process, see below) |
| `SessionStart` | Once per session begin/resume/clear | `GET /health`; `GET /users/{email}/undelivered-feedback` if you're in `end_of_session` mode |

**`POST /prompts`** — the payload sent on every single prompt (`hooks/on_prompt_submit.py`):

```json
{
  "user_email": "you@example.com",
  "user_name": null,
  "claude_session_id": "<claude's session id>",
  "prompt_text": "<the full prompt text you typed>",
  "is_scorable": true,
  "request_llm_score": true
}
```

**`prompt_text` is sent in full and unredacted.** If you paste a secret into a prompt, it goes to this endpoint and is stored in Postgres verbatim — there's no scrubbing. Worth knowing before pointing `api_base_url` at anything other than your own machine (see Teams and the auth caveat below). 2-second timeout, best-effort: dropped silently on any failure, never retried, never queued locally (see "Why this is built the way it is").

**`POST /sessions/end`** — fired once per session close, from the detached worker, not the hook itself:

```json
{ "user_email": "you@example.com", "claude_session_id": "<claude's session id>" }
```

No prompt content in this one — it just triggers the server-side session-close computation (`session_level`, and an end-of-session summary if you're in that mode). 5-second timeout, since the detached worker isn't racing a hook budget.

**`GET /health`** and **`GET /users/{email}/undelivered-feedback`** — fired once at session start, no body, 1-second timeout each. The second one only fires in `end_of_session` mode, and only sends your email in the URL path — no prompt content.

Every request carries an `X-Coach-Token` header when `COACH_API_TOKEN` is set locally (empty by default — see the auth caveat below), and goes to whatever `api_base_url` is in `$CLAUDE_PLUGIN_DATA/coach/config.json` (`http://localhost:8787` unless you've run `levelset` to point it at a shared backend).

## Running it locally

```bash
cd coach
cp .env.example .env   # fill in ANTHROPIC_API_KEY if you want LLM-comparison scoring
docker compose up -d
curl localhost:8787/health
```

That brings up Postgres (host port `5433`, deliberately not `5432` — avoids colliding with a dev's own local instance), the FastAPI backend (`8787`), a Vite dev server for the dashboard (`5173`), and the MCP server (`8788`, see below). Schema and the five seeded levels apply automatically on first boot via `docker-entrypoint-initdb.d`; for schema changes against an already-running database, add a file under `db/migrations/` and run `python db/migrate.py`.

Point a Claude Code session at this local stack by leaving `$CLAUDE_PLUGIN_DATA/coach/config.json`'s `api_base_url` at its default (`http://localhost:8787`) — which is also what a fresh install writes automatically.

## MCP server

`mcp/` exposes every capability the REST API has as an MCP tool over Streamable HTTP, so any MCP client — Claude Desktop, Claude Code, a custom agent — can score a prompt or read coaching data directly, without going through the dashboard or the hooks. It's a thin adapter, not a second implementation: every tool is one HTTP call into the same FastAPI backend (`mcp/server.py`'s `_request`) — there's exactly one source of truth for scoring, leveling, and progress logic, and this file owns none of it.

```bash
docker compose up -d mcp   # included in the default `docker compose up -d`
```

Connect at `http://localhost:8788/mcp` (or `http://mcp:8788/mcp` from inside the docker network). With the Claude Code CLI:

```bash
claude mcp add --transport http gccf-coach http://localhost:8788/mcp
```

**17 tools**, one per API capability:

| Tool | What it does |
| --- | --- |
| `score_prompt` | Score a draft prompt on GCCF — **no persistence**, doesn't touch a user's level. The "check before you send it" tool. |
| `submit_prompt` | Score AND persist a prompt for a real user/session — same effect as the `UserPromptSubmit` hook. |
| `end_session` | Close a session — same effect as the `SessionEnd` hook's detached worker. |
| `list_users` | Every user, optionally filtered by level and/or team. |
| `get_user` | One user's summary, level history, all-time GCCF averages. |
| `get_user_by_email` | Resolve a user by email. |
| `get_user_prompts` | A user's scored prompt history, full breakdown per prompt. |
| `get_user_sessions` | A user's sessions. |
| `get_user_feedback` | The coaching feedback a user has actually received. |
| `get_user_progress` | Is this person actually improving, per dimension. |
| `get_session` | One session's full detail, every prompt in it. |
| `list_teams` | Every team, cross-team comparison. |
| `get_team_progress` | Is this team actually improving, per dimension. |
| `list_levels` | The five levels, thresholds, descriptions, next-level tips. |
| `get_level_distribution` | How many users sit at each level. |
| `get_scoring_comparison` | Heuristic-vs-LLM agreement across every doubly-scored prompt. |
| `get_trend` | Daily per-dimension averages, org-wide or team-scoped. |

Every list-returning tool wraps its result as `{"items": [...], "count": N}` rather than a bare array — the MCP SDK represents a list return value as one content block *per item*, which reads as "only got the first result" if a client (or a quick manual test, which is how this was caught) only looks at the first content block. One object, one content block, always.

Carries the same `X-Coach-Token` auth as the REST API (`COACH_API_TOKEN`) — set it in `.env` and it's honored on every tool call automatically. In `docker-compose.yml`, the `mcp` service talks to `api` over the internal docker network (`http://api:8000`), not the host-published `8787` — same reasoning as why `ui` is the odd one out and *does* use the host port: `ui` runs client-side in a browser, `mcp` runs server-side like `api` does.

### Sample data

The dashboard is empty until real usage accumulates. To see it populated immediately:

```bash
docker compose exec api python seed_sample_data.py
```

Creates 3 teams (Platform, Growth, Data) and 11 users with 28 days of backdated prompt history, each following one of four trajectories (`flat_weak`, `improving`, `strong_steady`, `dip_recover`) so the trend charts, level history, and radar all have something real to show — not just a flat line. Every row is tagged (`@sample.coach.local` emails), so it's safe to remove later:

```bash
docker compose exec api python seed_sample_data.py --wipe          # wipe, then reseed
docker compose exec api python seed_sample_data.py --wipe --wipe-only   # wipe, don't reseed
```

It talks directly to Postgres (not through the API), because backdating `submitted_at` across 28 days is what makes the trend charts worth looking at, and the real `POST /prompts` endpoint always uses `now()`. It replays the exact leveling logic from `services/level_engine.py` chronologically as it inserts each prompt, so seeded users' levels and `level_history` are what the real system would have produced, not hand-picked.

Prompt text itself is generated, not templated to a target score: `build_prompt_text()` assembles a sentence from real clauses (verb, artifact, error detail, framing, scope, requirement, format ask), each included with a probability driven by that day's target "quality," then the assembled sentence is scored through the *actual* `scoring/heuristic.py` — the same function real prompts go through. So a seeded user's `dimension_feedback`, issue codes, and tips are genuine scorer output, not fabricated to match a story. The one place the seed script *does* fabricate: about 40% of prompts also get a synthetic `llm` row, jittered ±6 points from the heuristic score (±15 about 15% of the time, to simulate real disagreement) rather than a real Claude Haiku call — labeled `"claude-haiku-4-5-20251001 (simulated for sample data)"` in `model_name` and stated as simulated in `rationale`, specifically so it's never mistaken for a real model judgment if you go looking at the raw rows.

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

**`UserPromptSubmit` can only block by erasing the prompt and showing a reason.** There's no interactive checklist, no in-place edit, nothing richer than plain text in `reason`. So the GCCF breakdown *is* the coaching on this path (`services/coaching.py`'s `block_reason`), and "revise, or send anyway" became **resubmit the same text unchanged** (tracked by a local hash cache with a 5-minute TTL in `hooks/on_prompt_submit.py`) rather than a new command syntax to learn. The default `block_floor` (`hooks/lib/config.py`'s `DEFAULTS`) is `35` — the same number as `WEAK_THRESHOLD` in `scoring/heuristic.py` — so out of the box, blocking only fires on a composite that would already read as "weak" on the dashboard; a prompt sitting in the "developing" band (35–64) is never interrupted, only flagged after the fact. `levelset` lets a user raise or lower that floor independently of the scorer's own thresholds.

**`SessionEnd`'s total hook budget across every hook registered for it is about 1.5 seconds** — nowhere near enough for a network round trip to the API, let alone the DB work behind it. `hooks/on_session_end.py` does the only thing that fits in that budget: spawn a fully detached worker process (`hooks/lib/end_session_worker.py`) and exit in under 50ms. The worker does the real `POST /sessions/end` outside any hook timeout, with nothing waiting on it either way. Because even a detached process can be skipped entirely by a crash or a force-quit, `api/main.py` also runs a five-minute sweep that closes out any session with no prompt in the last 20 minutes, so end-of-session coaching never depends on one hook firing reliably.

**The blocking decision never touches the network.** `hooks/on_prompt_submit.py` scores every prompt with the pure, stdlib-only function in `api/scoring/heuristic.py` (imported directly, zero I/O, sub-5ms) — the block/allow call is made entirely locally before anything is sent anywhere. Persistence and the (optional, slower) LLM comparison score happen via a best-effort POST with an aggressive ~2-second timeout that's silently dropped on any failure: no retry, no local queue. That's a real trade-off, stated plainly rather than hidden: **if the backend is unreachable when a prompt is submitted, that prompt's row is simply lost.** A local spool-and-flush would fix that, but it's a distinct reliability feature, not part of this version — every hook script in this system is written to fail open, because a coaching tool that can block or crash real work on its own bugs is worse than no coaching tool at all.

## Scoring: two independent methods, not one

`api/scoring/heuristic.py` (rule-based, instant, zero cost) and `api/scoring/llm.py` (Claude Haiku, ~300–800ms, needs `ANTHROPIC_API_KEY`) both score every prompt and both persist — one row each per `(prompt_id, scoring_method)` in `prompt_scores` — specifically so they can be compared (`GET /dashboard/scoring-comparison`) rather than forcing a single method to win. **Leveling always uses the heuristic score.** It's the one guaranteed to exist synchronously; the LLM score runs as a `BackgroundTask` after the API has already responded to the hook, so it's never on any latency-sensitive path and a user's level never depends on LLM availability, cost, or rate limits.

## Leveling policy

A user's rolling average over their last 20 scored prompts (`config.ROLLING_WINDOW_SIZE`) is compared against each level's `min_score`, and they need at least 5 scored prompts (`config.MIN_SCORABLE_PROMPTS_TO_LEVEL`) before ever leaving level 1 — one good prompt shouldn't jump someone to Architect. `users.current_level` is **sticky upward-only**: a bad stretch never demotes the badge. `sessions.session_level` still captures a per-session dip independently, so a rough session is visible without being punitive.

The five levels and their thresholds (`db/seed/seed_levels.sql`):

| Level | Rolling composite ≥ | Description |
| --- | --- | --- |
| 1. Operator | 0 | Uses prompts inconsistently; burns tokens and turns re-explaining goals that were never stated. |
| 2. Composer | 45 | Gets work done in a smarter, more efficient way — prompts carry real context and a shape for the answer. |
| 3. Delegator | 65 | Has the four dimensions covered solo; ready to hand scoped work to an agent instead of driving every step by hand. |
| 4. Orchestrator | 80 | Splits larger problems across delegates and supervises the result. |
| 5. Architect | 92 | Prompts read like specs, not requests. |

These thresholds and the per-dimension status thresholds below (65 = "strong", 35 = "weak") were chosen independently, as reasonable round numbers, not derived from each other or from real usage data — Delegator's `65` landing on the same number as `STRONG_THRESHOLD` is coincidence, not a coupling to rely on. **They have never been calibrated against real prompts**, only against the sample data generator's own output — expect to retune `min_score` (and `STRONG_THRESHOLD`/`WEAK_THRESHOLD` in `scoring/heuristic.py`) once real usage data exists to check them against.

## Teams

Users optionally belong to a `team` (`users.team_id`, nullable — solo use needs no team at all). `GET /teams` gives cross-team comparison (member count, average level, average rolling composite); `GET /users?team_id=` and the Team Roster's team filter chips scope down to one. `GET /dashboard/trend?team_id=&days=` returns daily average scores **per GCCF dimension**, org-wide or team-scoped — the Team Roster and Teams pages plot all four as separate lines, because a single composite average hides which dimension is actually moving.

## Every score carries structured, actionable feedback — not just a number

`scoring/heuristic.py` doesn't just compute a 0–100 per dimension; every failing check produces a named issue code, a plain-English explanation of what's missing, and one concrete tip, prioritized by which fix would move the score most (`DimensionFeedback.top_tip`). This is stored as `prompt_scores.dimension_feedback` (JSONB) alongside the numeric columns, and it's what drives the actual coaching text everywhere it appears:

- **In-session block messages** (`services/coaching.py`'s `block_reason`) show the specific issue and tip per weak dimension, not just a checkmark.
- **End-of-session summaries** name the most common issue behind the session's weakest dimension.
- **The dashboard** (`PromptHistoryTable`'s expandable rows, `DimensionBreakdown`) shows the same breakdown for any individual prompt.

### The rules themselves

Every dimension starts at 0 and accumulates points from a handful of independent, named checks — this is the actual list, not a paraphrase (`scoring/heuristic.py`):

**Goal** (verb + artifact + length, no single check is fatal on its own):
- `no_verb` (35 pts) — one of ~40 imperative verbs (fix, add, refactor, investigate, …) appears in the first 4 words.
- `no_artifact` (35 pts) — a recognized artifact noun (function, file, component, …) anywhere, or any backticked code span.
- length (30 pts full / 15 pts partial) — ≥6 words scores full; 3–5 words scores half and logs `terse`; <3 words scores zero and logs `too_short`.

**Context** (does it supply what the agent can't infer):
- `no_reference` (40 pts) — a file-path-shaped token (`src/foo/bar.py`) or a backticked identifier.
- `no_detail` (30 pts) — an error/exception/traceback/failure keyword, or an 8+ character quoted span.
- `no_framing` (30 pts) — starts with or contains `when/given/if/after/while `.

**Constraints** (does it bound the scope):
- `no_scope_limit` (50 pts) — one of ~20 negation-of-change phrases ("don't touch", "keep unchanged", "without modifying", …).
- `no_requirement` (50 pts) — one of ~11 requirement words/phrases (must, should, only, within, limit, preserve, backward compat, …).

**Format** (does it ask for a shape): counts hits against ~19 format-cue phrases (diff, table, JSON, "respond with", "return a", checklist, …) — 2+ hits scores 100, exactly 1 scores 60 and logs `weak_format`, 0 scores 0 and logs `no_format`.

Every check is a plain substring/regex match against the lowercased prompt — no NLP, no embeddings, nothing probabilistic. That's deliberate: every point awarded traces to one named signal a human can read in the source, which is what makes a false positive fixable in one place instead of requiring a retrain. It also means it's gameable (mentioning "diff" without meaning it scores the same as meaning it) — this is a coaching nudge, not a fraud detector.

**Status** on each dimension is a flat threshold on the 0–100 score: `≥65` is `strong` (no tip shown — see `DimensionFeedback.to_dict`), `35–64` is `developing`, `<35` is `weak`. The **tip** shown for a non-strong dimension is always the single highest-*weight* failing check (`top_tip` picks `max(issues, key=weight)`) — deliberately not the first check that ran, not a bulleted list of everything wrong, because one clear next step is more likely to get acted on than three.

## Progress tracking — is this person/team actually improving

`GET /users/{id}/progress` and `GET /teams/{id}/progress` (`services/progress.py`, one implementation shared by both) compare a recent window of scored prompts against the window before it, **per dimension** — recent average, prior average, delta, and a direction (`improving` / `flat` / `declining`). For any dimension still weak (`<65`, same threshold as the per-dimension `status` above) in the recent window, it also surfaces the single most common issue code and its own tip — from `dimension_feedback.issue_detail`, specifically, not the dimension's combined `message`, which would conflate two different problems into one confusing sentence if both were present. The response includes a one-line `headline` built from all of this — strongest dimension, best-moving dimension, and the weakest with its most common cause. Backs the Progress card on both `UserDetail` and `Teams`.

The two numbers driving "is this movement or noise" (`WINDOW = 15`, the recent/prior split size; `_FLAT_BAND = 3.0`, the delta a direction has to clear either way to read as `improving`/`declining` rather than `flat`) are, like the leveling thresholds above, reasonable-sounding defaults, not derived from anything — and notably **not the same window** as leveling's rolling 20 (`config.ROLLING_WINDOW_SIZE`), because the two were built in separate passes with no attempt made to reconcile them. That's a real inconsistency, not a design choice: leveling asks "what's true right now," progress asks "did the last stretch differ from the one before," and there's no principled reason those need different sample sizes — they just do, today. Worth unifying, or at least deciding deliberately, before trusting either number too far.

## Sessions

`GET /users/{id}/sessions` lists a user's sessions (start/end, `session_level`, prompt count, average composite) — the unit between one prompt and a user's whole history. `GET /sessions/{id}` drills into one, with every prompt's full score breakdown, reusing the same `PromptHistoryTable`/`DimensionBreakdown` components as the user-level prompt history.

## What's deliberately out of scope for this version

**No real authentication.** A shared `X-Coach-Token` header on write endpoints (`COACH_API_TOKEN` in `.env`) is the only guard, and it's off by default. Anyone who can reach the API can read the whole team's data and could POST fabricated prompts. Fine for a trusted-network pilot; real per-user auth is a distinct follow-up, not an oversight.

**No delivery guarantee for individual prompts.** Covered above — a dropped POST means a lost row, not a retry.

**No demotion.** Also covered above, and deliberate: this is meant to read as growth-oriented, not punitive.
