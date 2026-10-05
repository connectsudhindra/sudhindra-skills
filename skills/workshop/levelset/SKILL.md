---
name: levelset
description: Point the GCCF prompt coach at a team's shared backend, and set your own coaching mode. Run once to switch off local defaults; skip it entirely for solo use.
disable-model-invocation: true
---

# Levelset

The `coach/` system starts working the moment this plugin is installed — the first `SessionStart` after install writes sane local defaults (a `localhost` API, `end_of_session` coaching, your git email) with no conversation required. This skill exists for the one case that setup can't guess: pointing your machine at a **shared team backend** instead of your own local one, or changing how coaching reaches you once you're up and running.

Skip this entirely if you're using the system solo, locally, with the defaults. Run it when you want to join a team's shared instance, or you want a mode other than the default.

## What it configures

Reads and rewrites the local config file the hooks already use — `$CLAUDE_PLUGIN_DATA/coach/config.json` (or `~/.sudhindra-skills/coach/config.json` if that variable isn't set). Never touches the database directly; it only ever talks to the API, and only for confirmation.

## Process

**1. Read the current config.** Show what's there now — API URL, email, coaching mode, block floor — so the user is confirming changes, not guessing at what's already set.

**2. Ask where the backend lives.**

> Recommended: keep the local default (`http://localhost:8787`) unless someone gave you a team URL.

If the user gives a URL other than localhost, `curl` its `/health` endpoint before writing anything. A team backend that doesn't answer is worth flagging now, not discovering the first time a prompt silently fails to score.

**3. Confirm identity.** Show the email the system derived (`git config user.email`, or whatever's already saved) and let the user override it — this is the identity the team dashboard will show them under.

**4. Ask the coaching mode.** Three options, plainly stated trade-offs:

- **`in_session`** — a weak prompt gets blocked immediately with a GCCF breakdown; resubmitting it unchanged sends it through anyway. Fast feedback, but a block does erase what you typed until you resend it.
- **`end_of_session`** (the default) — nothing interrupts you mid-session; a summary of the session's scores and the single weakest dimension shows up at the start of your *next* session instead.
- **`off`** — no scoring, no blocking, no summaries. The hooks still run but exit immediately without doing anything.

**5. If `in_session`, ask about the block floor.** Default 35/100. Lower means fewer interruptions and weaker prompts slip through unflagged; higher means more friction but a tighter bar. Most people should just take the default.

**6. Write the config file**, then read it back and show the user the result — the config file is the only thing this skill ever changes.

## What this skill deliberately does not do

It doesn't create a database, run migrations, or start Docker containers — that's `coach/docker-compose.yml`'s job, and the `SessionStart` hook already tries to bring the local stack up on its own if it's pointed at `localhost` and unreachable. It doesn't manage per-user permissions on a shared backend either; anyone with the URL and (if set) the `X-Coach-Token` can read the whole team's data in this version — see `coach/README.md` for why that's an accepted v1 trade-off, not an oversight.
