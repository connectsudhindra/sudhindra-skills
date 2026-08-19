---
name: compass
description: Ask which skill or flow fits your situation. A router over the skills in this repo.
disable-model-invocation: true
---

# Compass

Nobody holds thirty-five skill names in their head. That's what this one is for — point it at your situation, it points back at a flow.

Everything below sits on one spine, the **main flow**, with two **on-ramps** that feed into it, a **health check** that runs beside it, a **vocabulary layer** underneath it, and a shelf of **standalone** tools that never join it at all.

## Spine: idea → shipped

1. **Interview the idea.** In a repo, that's **`/cross-examine`** — it keeps what it learns in `CONTEXT.md` and ADRs as it goes, so start here whenever there's a working directory under you. No repo yet? Jump to `/interrogate` under Standalone instead; both wrap the same `/interview` primitive, `cross-examine` is just the one with a paper trail, which is why it wins whenever there's somewhere to leave one.

2. **Hit a question conversation can't settle?** State, business logic, a UI you'd have to look at — detour through code you'll throw away:
   - **`/relay`** out to a scratch directory,
   - **`/sketch`** the answer as disposable code,
   - **`/relay`** back in with what you learned, cited from the original thread.

3. **Size the build.**
   - **Multi-session** → **`/blueprint`** turns the thread into a spec, **`/breakdown`** splits the spec into tracer-bullet tickets with their **blocking edges** made explicit (one file per ticket in `.scratch/<feature>/issues/` on a local tracker; native blocking links on a real one — either way, anything unblocked is gettable). Take each ticket into **`/build`**, `/clear`ing between tickets since each one is self-contained.
   - **Fits in this window** → straight to **`/build`**, no detour through tickets at all.

   Either path lands in the same place: `/build` drives **`/redgreen`** internally, one slice at a time, then closes with **`/gatekeeper`** — a Standards-and-Spec review of the diff — before it lets you commit. Either half also stands alone: `/redgreen` on its own for a test-first change with no spec behind it, `/gatekeeper` on its own to review a branch that's already up.

**Don't break the spine mid-build.** Steps 1 through 3 want to sit in one unbroken context — no `/compact`, no `/clear` — until `/breakdown` is done, so the interview, the spec, and the tickets all reason from the same material. `/build` is what starts fresh, per ticket, after that. The ceiling on this is the **smart zone** (~150k tokens of sharp reasoning on current models) — approaching it before `/breakdown` means `/compact` at the next boundary, not push through degraded (see Boundaries, below).

## On-ramps

Things that generate work and feed it onto the spine.

**A backlog forming from outside** → **`/intake`**. Walks incoming issues through triage roles until they're agent-ready, then `/build` picks them up. Reserved for issues you *didn't* write — bug reports, cold feature requests. A ticket `/breakdown` already produced is already agent-ready; running it through `/intake` too is redundant.

**Something's broken and won't explain itself** → **`/unravel`**. For the bug that survives a first glance: the flake, the regression wedged between two good states. Refuses to theorize before it has a loop that reliably goes red on *this* bug, fixes it, then locks the fix down with a regression test. If the post-mortem finds no clean seam to pin the fix to, it hands off to `/foundation-check`.

**Fog — a greenfield build or a feature too big to see the end of** → **`/trailmap`**, the heaviest flow here. Charts a shared map of decision tickets and burns through them one at a time, producing decisions rather than deliverables, until the way is visible. `/cross-examine` is for an idea one session can hold; `/trailmap` is for the idea that can't fit — reach for it only there, it's too slow for a well-scoped feature. When the fog clears, it hands off rather than builds: rejoin the spine at `/blueprint`, which folds the map's decisions into a buildable plan. Skipping straight to `/build` throws that linked reasoning away — fine only if the effort turned out smaller than it looked.

## Standing upkeep

**`/foundation-check`** — not feature work, maintenance. Run it whenever there's a spare moment; it surfaces deepening opportunities in the existing codebase, and picking one is itself an idea to carry into `/cross-examine`. It's the scout that finds candidates — `/workbench`, below, is the bench you design the chosen one on.

## The vocabulary underneath

Two model-invoked skills that other skills quietly lean on. Go to them directly when the problem is the *words*, not the process.

- **`/lexicon`** — sharpens the project's domain language: a fuzzy term challenged, an overloaded word split apart, a hard call written down as an ADR. It's the active discipline behind `CONTEXT.md` staying a clean glossary instead of a stale one; `/cross-examine` drives it.
- **`/workbench`** — the vocabulary for a module's *shape*: interface, depth, seam, adapter, leverage, locality. `/redgreen` and `/foundation-check` both assume you speak it.

## Boundaries between phases

Five ways to end a phase, and the fuzziest call in this whole map: **Continue** (free), **`/clear`** (empty the window), **`/relay`** (a portable file — new harness, new directory, a colleague, or a mid-phase side quest), a **subagent** (AFK-scoped work, its own window, a report back), or **`/compact`** (the default, and deliberately the last resort rather than the first).

[BOUNDARY-TREE.md](BOUNDARY-TREE.md) has the ordered walk through all five, and the case for why Continue gets ruled out first. The decision belongs at the boundary — mid-phase, just continue, or split what's left to a subagent.

## Off the spine entirely

- **`/interrogate`** — `/cross-examine`'s stateless twin: same interview, nothing saved, no `CONTEXT.md`. For when there's no working directory to leave a trail in — a plan, a design, a piece of writing. Inside a repo, `/cross-examine` is strictly the better pick.
- **`/interview`** — the primitive itself, unwrapped: rounds, the frontier, facts are the agent's job, decisions are yours. `/interrogate`, `/cross-examine`, `/intake`, `/trailmap`, and `/foundation-check` all run it under the hood.
- **`/peacemaker`** — an in-progress merge or rebase conflict, resolved hunk by hunk by traced intent, never by `--abort`. Reach for it mid-conflict; it's on no flow.
- **`/sketch`** — throwaway code built to answer exactly one design question. "Throwaway" constrains how it's written, not its fate: the answer folds back into the real code, and the sketch itself survives as a primary source on a `prototype/<name>` branch, linked from the implementation ticket. It's the spine's step-2 detour, but works any time a design question resists paper.
- **`/scout`** — reading legwork handed to a background agent: it chases primary sources and leaves a cited Markdown file behind while you keep working. What it produces feeds `/cross-examine`; it doesn't replace the thinking.
- **`/envoy`** — for when the blocker lives in someone *else's* head. Writes them a questionnaire — the inverse of `/interrogate`: it interviews you about the send (who, what you need back), not the subject. What comes back feeds `/cross-examine` or `/blueprint`.
- **`/handrail`** — for steps only a human can take: provisioning, credentials, a third-party dashboard, a one-off cutover. Generates an interactive script that opens each URL, captures each value, writes it to `.env` and GitHub secrets. Model-invoked — the agent reaches for it the moment it hits a wall only a human can cross.
- **`/clarify`** — fired mid-conversation when something you just said didn't land; re-pitches it in plain English using the `CONTEXT.md` vocabulary. The after-the-fact fix, where `/cross-examine` is the upfront one — a shared language agreed early is what keeps the jargon from showing up at all.
- **`/mentor`** — a concept learned over several sessions, the working directory doubling as the notebook.
- **`/styleguide`** — how to write anything meant for an agent to read: skills, AGENTS.md, any doc reached by a pointer.

## Before any of this

**`/bootstrap`** — run once, before the first engineering flow in a repo, to set the issue tracker, triage labels, and doc layout everything above assumes. Custom trackers work too.
