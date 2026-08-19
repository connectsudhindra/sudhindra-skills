# Sudhindra's Skills For Real Engineering

Agent skills for real engineering — not vibe coding.

Developing real applications is hard. Approaches like GSD, BMAD, and Spec-Kit try to help by owning the whole process for you. In doing so they take away your control, and make it hard to untangle things when the process itself produces a bug.

These skills take the opposite bet: small, legible, easy to adapt, composable, model-agnostic. Read one before you run it. Fork it the moment it stops fitting how you work.

## Installation

Two philosophies, pick one. **The Claude Code plugin** is a managed, read-only bundle — you get the whole set, updated in place. **[skills.sh](https://skills.sh)** copies the raw skill files into your project instead, so you own and can edit every line. Installing both just duplicates everything.

<details>
<summary><strong>Claude Code — as a plugin</strong></summary>

This repo is its own single-plugin marketplace, so there's no official listing to add first:

```
/plugin marketplace add connectsudhindra-gif/sudhindra-skills
/plugin install sudhindra-skills@sudhindra-skills
```

</details>

<details>
<summary><strong>Codex, and other agents — skills.sh</strong></summary>

```bash
npx skills@latest add connectsudhindra-gif/sudhindra-skills
```

You'll be asked which skills to take and which agents to wire them into. **Take `bootstrap`** — the rest lean on it.

</details>

<details>
<summary><strong>Working on this repo itself</strong></summary>

No push required — this makes the skills live on your machine straight from the working tree:

```bash
./scripts/link-skills.sh
```

Symlinks every skill into `~/.claude/skills` and `~/.agents/skills`. Re-run it whenever a folder gets added, dropped, or renamed.

</details>

### First command in any repo: `/bootstrap`

Run it once per project, before reaching for anything else here. It figures out:

- which issue tracker you're using (GitHub, GitLab, Linear, plain local files),
- what your triage labels actually say (`/intake` reads them back),
- where it should file the docs it writes.

## Why this exists

Four failure modes, four fixes.

### 1 — The build didn't match the brief

Misalignment is the oldest failure in software, agent or human. You think the brief landed. Then the diff shows up and it's clear the brief never landed at all.

The countermeasure is an interview before the keyboard, not after: make the agent interrogate the plan until nothing's left assumed.

- [`interrogate`](./skills/flow/interrogate/SKILL.md) — for anything that isn't code
- [`cross-examine`](./skills/craft/cross-examine/SKILL.md) — the same interrogation, run inside a repo, leaving a paper trail behind it

Reach for one of these before any change big enough to regret getting wrong.

### 2 — Every answer is three paragraphs long

Early in a project, you and the agent don't share a vocabulary yet — so it spells everything out, every time, because it has no shorthand to reach for.

The fix is building that shorthand deliberately: a small glossary that turns "the thing where a lesson gets promoted into a real file on disk" into one word both sides now recognize.

`cross-examine` does this as a side effect of the interview — sharpening the shared vocabulary and writing down the hard calls as decision records while the conversation is still live, not after.

> [!TIP]
> A shared vocabulary pays for itself beyond just shorter answers:
>
> - names in the codebase stop drifting, because there's one word for each thing
> - the agent navigates faster, because the map has fewer synonyms on it
> - less of every reply is spent re-deriving what a term means

### 3 — It compiles and it's still wrong

Alignment doesn't guarantee correctness. If the agent can't see how its own output behaves, it's guessing — and guesses compound.

Close the loop with the standard tools: types, a runnable check, tests that fail before they pass.

[`redgreen`](./skills/craft/redgreen/SKILL.md) drives red-green-refactor on whatever you're building, one thin vertical slice at a time. [`unravel`](./skills/craft/unravel/SKILL.md) does the same discipline for the bug that resists a first glance — refuses to theorize until it has a loop that reliably reproduces the failure.

### 4 — The codebase got harder to move in every week

Speed of typing isn't the bottleneck agents remove — speed of *entangling* is what they add. A codebase can rot faster than any team ever rotted it by hand.

Two skills push back on that directly:

- [`blueprint`](./skills/craft/blueprint/SKILL.md) makes you name the modules you're about to touch before it writes the spec
- [`foundation-check`](./skills/craft/foundation-check/SKILL.md) walks the codebase looking for places a small interface would hide a lot of mess, and hands you the list. Run it every few days — it's a scout, not a cleanup crew: on an old codebase it'll find real candidates, but it won't fix them for you.

## What's in here

Every skill splits on one question: does a human have to type it, or can the model reach for it on its own? **User-invoked** skills only fire when named — they're the orchestrators. **Model-invoked** skills carry the actual discipline and can be pulled in either way. An orchestrator can call a model-invoked skill; it never calls another orchestrator.

Full lists, same grouping: [`skills/craft/README.md`](./skills/craft/README.md) and [`skills/flow/README.md`](./skills/flow/README.md).

### craft/ — the engineering set

Start at [`compass`](./skills/craft/compass/SKILL.md) — it's the router, and it knows the rest. Everything it can point you at: `cross-examine`, `intake`, `foundation-check`, `bootstrap`, `blueprint`, `breakdown`, `build`, `trailmap`, `sketch`, `unravel`, `scout`, `redgreen`, `lexicon`, `workbench`, `gatekeeper`, `peacemaker`, `handrail`.

### flow/ — everything else you do with an agent

`interrogate`, `relay`, `mentor`, `envoy`, `clarify`, `interview`, `styleguide`.

### The unpromoted buckets

- **[`skills/toolbox/`](./skills/toolbox/README.md)** — narrow tools, kept around, not part of the plugin.
- **[`skills/workshop/`](./skills/workshop/README.md)** — beta work, shared on purpose, promoted only once it earns it.

## Prompt coaching, built in

Installing this plugin also activates a GCCF (Goal/Context/Constraints/Format) prompt coach: every prompt gets scored, weak ones get a live nudge to sharpen before they burn a turn, and growth tracks through five levels — Operator, Composer, Delegator, Orchestrator, Architect. It starts working the moment the plugin installs, no setup step required. The same data is also reachable as 17 MCP tools (`coach/mcp/`) — score a draft prompt, check anyone's progress, pull a team trend — for any MCP client, not just the dashboard. See [`coach/README.md`](./coach/README.md) for how it's built and why; [`levelset`](./skills/workshop/levelset/SKILL.md) to point it at a shared team backend; [`standing`](./skills/workshop/standing/SKILL.md) to check where you stand on demand.

## Contributing to this repo

The rules for where a skill lives, how buckets and the plugin manifest stay in sync, and what a new skill owes the router, are in [`AGENTS.md`](./AGENTS.md).
