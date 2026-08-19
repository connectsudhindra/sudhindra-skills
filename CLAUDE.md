Four buckets, one convention. `skills/` splits into `craft/` (daily engineering work), `flow/` (workflow tools that aren't code-specific), `toolbox/` (small utilities, kept but not promoted), and `workshop/` (beta — public on purpose, not yet in the plugin).

`craft/` and `flow/` are **promoted**: everything in either one gets a line in the top-level `README.md` and a path in `.claude-plugin/plugin.json`. That array is exactly what the Claude Code plugin ships — a skill in `toolbox/` or `workshop/` that sneaks into it is a bug, not a feature.

`.claude-plugin/marketplace.json` is what makes this repo installable on its own, since there's no official marketplace listing backing it. Run `claude plugin validate . --strict` any time you touch a manifest, before you consider the change finished.

Documentation nests the same way skills do: a bucket `README.md` lists every skill it holds, one line each, name linked to `SKILL.md`; the promoted buckets additionally split that list into **User-invoked** and **Model-invoked** (see `.agents/invocation.md` for what draws that line).

The one skill that has to stay accurate no matter what else changes is [`compass`](./skills/craft/compass/SKILL.md) — it's the router, the single document that says which skill to reach for and how they chain together. Adding, renaming, retiring, or rewiring a user-reachable skill without going back to update `compass/SKILL.md` leaves the map wrong, which is worse than no map.

To work on this repo locally without publishing anything, run `scripts/link-skills.sh`. It symlinks every skill into `~/.claude/skills` and `~/.agents/skills` so edits here take effect immediately — rerun it whenever a skill's folder name changes, or the old symlink just sits there stale.
