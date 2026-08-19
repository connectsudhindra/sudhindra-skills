# Sudhindra's Skills For Real Engineering

Agent skills for real engineering — not vibe coding.

Developing real applications is hard. Approaches like GSD, BMAD, and Spec-Kit try to help by owning the process. But while doing so, they take away your control and make bugs in the process hard to resolve.

These skills are designed to be small, easy to adapt, and composable. They work with any model. Hack around with them. Make them your own.

## Installation

Two ways in, two philosophies. **The Claude Code plugin** installs the whole set as a managed, read-only bundle. **[skills.sh](https://skills.sh)** copies editable skill files into your project, so you can hack on them directly. Pick one — installing both leaves you with every skill twice.

<details>
<summary><strong>Claude Code — as a plugin</strong></summary>

This repo ships its own single-plugin marketplace, so no official listing is required:

```
/plugin marketplace add sudhindradesai/sudhindra-skills
/plugin install sudhindra-skills@sudhindra-skills
```

</details>

<details>
<summary><strong>Codex, and other agents — skills.sh</strong></summary>

```bash
npx skills@latest add sudhindradesai/sudhindra-skills
```

Pick the skills you want, and which coding agents to install them on. **Make sure `setup-sudhindra-skills` is one of them.**

</details>

<details>
<summary><strong>Local dev — symlink straight in</strong></summary>

If you're working on this repo itself (or just want it live on this machine without pushing anywhere first):

```bash
./scripts/link-skills.sh
```

This symlinks every skill into `~/.claude/skills` and `~/.agents/skills`. A `git pull` keeps them current; re-run the script after adding, removing, or renaming a skill.

</details>

### Run `/setup-sudhindra-skills`

In your agent, run it once per repo. It will:

- Ask you which issue tracker you want to use (GitHub, GitLab, Linear, or local files)
- Ask you what labels you apply to tickets when you triage them (`/triage` uses labels)
- Ask you where you want to save any docs it creates

## Why These Skills Exist

These skills fix common failure modes in agentic coding.

### #1: The Agent Didn't Do What I Wanted

The most common failure mode in software development is misalignment. You think the agent understood the brief. Then you see what it built — and realize it didn't understand you at all.

The fix is a **grilling session** — getting the agent to ask detailed questions about what you're building, before it writes a line of code.

- [`/grill-me`](./skills/productivity/grill-me/SKILL.md) — for non-code uses
- [`/grill-with-docs`](./skills/engineering/grill-with-docs/SKILL.md) — the same thing, but it also builds a shared project vocabulary as it goes (see below)

Use these *every* time you want to make a change of any real size.

### #2: The Agent Is Way Too Verbose

At the start of a project, you and the agent are usually speaking different languages — the agent hasn't learned the project's jargon yet, so it spells everything out at length.

The fix is a shared language: a document that decodes the jargon used in the project, so both sides can talk in short, precise terms instead of long paraphrases.

This is built into [`/grill-with-docs`](./skills/engineering/grill-with-docs/SKILL.md). It runs a grilling session that also sharpens a shared vocabulary and documents hard-to-explain decisions as ADRs, inline, as you go.

> [!TIP]
> A shared language has other benefits beyond reducing verbosity:
>
> - **Variables, functions and files are named consistently**, using the shared language
> - The **codebase is easier to navigate** for the agent
> - The agent **spends fewer tokens on thinking**, because it has a more concise language to think in

### #3: The Code Doesn't Work

Even when you and the agent are aligned on what to build, it can still produce code that's broken. That means your feedback loops are too weak — without feedback on how the code actually runs, the agent is flying blind.

The fix is the usual tranche of feedback loops: static types, browser access, and automated tests.

For tests, a red-green-refactor loop is critical — the agent writes a failing test first, then makes it pass. The **[`/tdd`](./skills/engineering/tdd/SKILL.md)** skill slots into any project and encourages exactly that.

For debugging, **[`/diagnosing-bugs`](./skills/engineering/diagnosing-bugs/SKILL.md)** wraps best debugging practices into a disciplined loop, gated phase by phase, so the agent stops guessing and starts narrowing.

### #4: We Built A Ball Of Mud

Agents can radically speed up coding — which also accelerates software entropy. Codebases get more complex faster than ever.

The fix is caring about the design of the code, deliberately, at every layer:

- [`/to-spec`](./skills/engineering/to-spec/SKILL.md) quizzes you about which modules you're touching before creating a spec
- [`/improve-codebase-architecture`](./skills/engineering/improve-codebase-architecture/SKILL.md) surveys a codebase for deepening opportunities and hands you the candidates. Run it every few days. It's a survey, not a rescue: on a genuinely old codebase it finds real candidates, but it won't untangle the mud for you on its own.

## Reference

These split on one axis — who can invoke them. **User-invoked** skills are reachable only when you type them (e.g. `/grill-me`); their job is to orchestrate. **Model-invoked** skills can be invoked by you _or_ reached for automatically by the agent when the task fits; they hold the reusable discipline. A user-invoked skill may invoke model-invoked skills, but never another user-invoked one.

See [`skills/engineering/README.md`](./skills/engineering/README.md) and [`skills/productivity/README.md`](./skills/productivity/README.md) for the full list, grouped the same way.

### Engineering

Daily code work: [`ask-sudhindra`](./skills/engineering/ask-sudhindra/SKILL.md) (start here — it's the router), `grill-with-docs`, `triage`, `improve-codebase-architecture`, `setup-sudhindra-skills`, `to-spec`, `to-tickets`, `implement`, `wayfinder`, `prototype`, `diagnosing-bugs`, `research`, `tdd`, `domain-modeling`, `codebase-design`, `code-review`, `resolving-merge-conflicts`, `wizard`.

### Productivity

General workflow, not code-specific: `grill-me`, `handoff`, `teach`, `to-questionnaire`, `wait-what`, `grilling`, `writing-for-agents`.

### Other buckets

- **[`skills/misc/`](./skills/misc/README.md)** — kept around but rarely used, not promoted in the plugin.
- **[`skills/in-progress/`](./skills/in-progress/README.md)** — beta, public on purpose, excluded from the plugin until they graduate.

## Repo layout

See [`AGENTS.md`](./AGENTS.md) for how skills are organized, how buckets and the plugin manifest relate, and the conventions for adding a new one.
