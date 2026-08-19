This repo's skills live in four bucket folders under `skills/`, and the bucket tells you how much to trust what's inside:

- `craft/` — the daily-driver engineering skills. Load-bearing.
- `flow/` — non-code workflow tools. Load-bearing.
- `toolbox/` — narrow, occasional-use utilities. Kept, not promoted.
- `workshop/` — beta. Public on purpose, feedback wanted, not shipped in the plugin.

`craft/` and `flow/` are the **promoted** buckets: every skill inside one needs an entry in the top-level `README.md` *and* a path in `.claude-plugin/plugin.json`'s `skills` array — the Claude Code plugin ships exactly this set, nothing from `toolbox/` or `workshop/` leaks in.

Install instructions live once, in `README.md`. `.claude-plugin/marketplace.json` turns the repo into its own single-plugin marketplace, which is the actual documented install route here (there's no official-marketplace listing to fall back on). After touching either manifest, run `claude plugin validate . --strict` before calling it done.

Every top-level `README.md` entry links the skill's name to its `SKILL.md`. Each bucket folder carries its own `README.md` doing the same at bucket scope — one line per skill. In the promoted buckets that list splits into **User-invoked** and **Model-invoked**; `toolbox/` and `workshop/` don't bother with the split, they're just flat lists.

The invocation split itself — which skills the human must type versus which the model can reach for on its own — is `.agents/invocation.md`'s job to define. Read it before adding a skill to either camp.

[`compass`](./skills/craft/compass/SKILL.md) is the map: it's the one place that names every user-reachable skill and how the flows between them connect. Treat it as load-bearing documentation, not a nice-to-have — a skill `compass` doesn't mention is invisible to anyone who doesn't already know to look for it, and a route it still describes after that route changed is actively misleading. Re-open and fix `compass/SKILL.md` in the same change that adds, renames, removes, or re-routes anything user-reachable.

Local dev: `scripts/link-skills.sh` symlinks every skill folder in this repo into `~/.claude/skills` and `~/.agents/skills`, so changes here are live without a publish step. Re-run it any time a skill gets added, dropped, or renamed — stale symlinks left behind from an old name won't clean themselves up.

`coach/` at the repo root is the one thing here that isn't a skill: a Postgres + FastAPI + React system that auto-registers Claude Code hooks (via `coach/hooks/hooks.json`, referenced from the `hooks` field in `.claude-plugin/plugin.json`) to score every submitted prompt and track GCCF growth. Its two user-facing skills, `levelset` and `standing`, live under `skills/workshop/` since it's the first infrastructure of its kind in this repo — everything else about it, including the constraints that shaped its design, is documented in [`coach/README.md`](./coach/README.md).
