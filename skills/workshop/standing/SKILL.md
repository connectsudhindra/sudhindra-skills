---
name: standing
description: Check current GCCF level, recent prompt scores, and the tip for reaching the next level. Use when the user asks how they're doing with their prompts, what level they're at, or how to prompt better.
---

Where the user actually stands right now, on demand — independent of `coaching_mode`. Someone on `end_of_session` or even `off` can still ask this any time; it's a read, not a delivery mechanism.

1. Load `$CLAUDE_PLUGIN_DATA/coach/config.json` (fallback `~/.sudhindra-skills/coach/config.json`) for the API URL and email. No config file yet means the coaching system has never run in this environment — say so plainly and stop; don't fabricate a level.

2. `GET {api_base_url}/users/by-email/{email}`. Unreachable API or unknown email (no scored prompts yet) both mean there's nothing to report — say so, don't guess a level from thin air.

3. Present, briefly:
   - **Current level and name** (e.g. "Level 3 — Delegator").
   - **Rolling GCCF composite** — the average behind the current level, out of 100.
   - **The single weakest dimension** — Goal, Context, Constraints, or Format, whichever the four-way split is lowest on. Naming the *one* thing to work on beats a flat readout of all four.
   - **The next-level tip**, pulled from the level's own `next_level_tip` — via `GET /users/{id}` for the full detail if the summary endpoint doesn't already carry it.

4. Keep it to a few lines. This is a status check the user asked for mid-work, not a performance review — the full breakdown lives on the dashboard (`coach/ui`), not in this reply.
