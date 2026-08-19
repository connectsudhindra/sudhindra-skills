---
name: handrail
description: Generate an interactive bash wizard that walks a human through steps only they can perform. Use when provisioning infrastructure, setting up credentials or CI secrets, walking an unfamiliar third-party dashboard, or running a one-off migration or cutover. Don't invoke this for steps the agent can perform itself.
---

# Handrail

A **wizard** is a bash script that walks a human, one step at a time, through a manual procedure that's tedious by hand and just as tedious to re-explain to an agent every single time. It opens each URL, says exactly what to click and copy, captures the value, writes it where it belongs (`.env`, a GitHub secret), confirms at every stage, and always shows how many stages remain. Configuring a third-party service, running a one-off migration, moving a project from one state to another — all the same shape underneath.

The UX itself is already solved, in [script.template.sh](script.template.sh): stage-by-stage progress, confirmation gates, cross-platform URL opening (WSL included), hidden secret entry, idempotent `.env` upserts, `gh secret`/`gh variable` writes, a closing summary. **The only job left is scoping the procedure and writing its stages.** Everything above the `STAGES` marker is identical across every wizard on purpose — never hand-edit it.

A wizard defaults to ephemeral: built for one run, parked in scratch or `scripts/`, deleted once the job's done. Commit it only when the user actually wants a repeatable path living in the repo.

## Stage A — scope the procedure

Work out every manual step the human has to take and every value that gets captured along the way, and read the repo before asking anything cold:

- For a **setup**: `.env`, `.env.example`, `.env.*`, `README`, `docker-compose*`, framework config, `.github/workflows/*` — every `secrets.*` / `vars.*` reference names a value the wizard has to produce.
- For a **migration or transition**: the current state, the target state, and whatever's irreversible in between.

Then hand the user the ordered stage list and the values each one produces, and let them add, drop, or reorder before you write anything.

This stage is finished once every stage is named in order, and for each captured value you know where the human gets it, where it's written (`.env`, a GitHub secret, both, or nowhere for pure-action stages), and whether it's secret or public.

## Stage B — map each stage's actual journey

For every stage, write the exact path a human follows — which URL, what to do once there, where the value shows up, which variable it fills. "Dashboard → Developers → API keys → Reveal test key → copy" is the right level of precision. Where the current UI or exact command isn't something you actually know, say so and check with the user or the docs — never invent a step that might not exist.

Finished once every stage traces to instructions concrete enough for a stranger to follow cold.

## Stage C — write the wizard

Copy `script.template.sh` to the target path. One `stage` per step you scoped, in dependency order, replacing the example. Use the library helpers as given — `stage`, `say`/`step`, `open_url`, `ask`/`ask_secret`, `write_env`, `set_secret`/`set_var`, `pause`/`confirm` — and set `TOTAL_STAGES` to match.

Hold the template's own bar: open the URL before asking for what's on it, `ask_secret` for anything secret, `write_env` every persisted value, `set_secret` only what CI actually consumes, `confirm` ahead of anything irreversible. Each `stage` clears the screen so only the current step is visible — keep one focused task per stage so nothing the human needs scrolls out of view. The library above the marker stays untouched.

## Stage D — verify, then hand off

Run `bash -n <script>`, and `shellcheck` if it's available. `chmod +x` the result. Don't execute it end-to-end yourself — it opens browsers and blocks on a human — trace it statically instead: confirm every value from Stage A gets captured and lands where Stage A said, and every `set_secret` name matches a real `secrets.*` reference in CI.

Tell the user how to run it. If it's meant to be a repeatable setup path, commit it and link it from the README, so the next person runs the script instead of re-explaining the procedure to an agent all over again.
