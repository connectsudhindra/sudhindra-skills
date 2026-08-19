---
name: breakdown
description: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker — edges as text in one file per ticket locally, or native blocking links on a real tracker.
disable-model-invocation: true
---

# Breakdown

Turns a plan, spec, or open conversation into **tickets** — tracer-bullet vertical slices, each one honest about which other tickets have to land first.

The issue tracker and triage label vocabulary should already be available to you. If not, send the user to `/bootstrap`.

**Step 1 — gather what's already there.** Work from the conversation context first. If the user hands you a reference — a spec path, an issue number, a URL — fetch it and read the whole thing, comments included.

**Step 2 — look at the codebase, if you haven't.** Ticket titles and descriptions borrow the project's domain glossary and respect whatever ADRs already govern the area. While you're in there, look for a prefactor that would make the eventual implementation easier — make the change easy, *then* make the easy change.

**Step 3 — draft the vertical slices.** Every slice cuts a narrow but complete path through every layer it touches — schema, API, UI, tests — never a horizontal slice of just one layer. A finished slice is demoable or verifiable entirely on its own, and sized to fit inside one fresh context window. Any prefactoring from step 2 goes first, ahead of the slices it unblocks.

Give each ticket its **blocking edges**: the tickets that must finish before this one starts. No blockers means it's startable right now.

*Wide refactors don't fit this shape, and that's fine.* A wide refactor — rename a column, retype a shared symbol — has a blast radius that fans across the whole codebase, so one edit breaks thousands of call sites and no vertical slice can land green. Don't force it into a tracer bullet. Sequence it **expand → migrate → contract** instead: expand adds the new form beside the old so nothing breaks yet; migrate moves call sites over in batches sized to the blast radius (per package, per directory), each batch its own ticket blocked by expand, CI staying green batch to batch because the old form is still there; contract deletes the old form once nothing references it, blocked by every migrate batch. If even the batches can't stay green in isolation, let them share an integration branch that all block one final integrate-and-verify ticket — that's the only ticket allowed to promise green.

**Step 4 — quiz the user on the shape.** Show the proposed breakdown as a numbered list — title, what blocks it, what it delivers end-to-end — and ask three things: does the granularity feel right, are the blocking edges actually correct (does each ticket depend only on what genuinely gates it), and should anything merge or split further. Iterate until they sign off.

**Step 5 — publish, in blocker order.** Which shape depends on what `/bootstrap` configured, though the ticket content is identical either way:

- **Local tracker** → one file per ticket under `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` in dependency order, "Blocked by" naming numbers/titles. One ticket, one file — never combined.
- **Real tracker** (GitHub, Linear, …) → one issue per ticket, published blockers-first so blocking edges can reference real IDs. Use the platform's native blocking/sub-issue link if it has one, otherwise a "Blocked by" field naming the blocking issues. Label `ready-for-agent` by default — these are agent-grabbable by construction.

Work the **frontier** — any ticket whose blockers are all done — which for a purely linear chain just means top to bottom. Never close or edit a parent issue as part of this.

<local-ticket-template>

# <NN> — <Ticket title>

**What to build:** the end-to-end behaviour this ticket makes work, from the user's perspective — not a layer-by-layer implementation list.

**Blocked by:** the numbers/titles of the tickets that gate this one, or "None — can start immediately".

**Status:** ready-for-agent

- [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2

</local-ticket-template>

<issue-template>

## Parent

A reference to the parent issue on the tracker (if the source was an existing issue, otherwise omit this section).

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective — not layer-by-layer implementation.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Blocked by

- A reference to each blocking ticket, or "None — can start immediately".

</issue-template>

Either template stays free of specific file paths or code snippets — they go stale fast. One exception: a snippet from a prototype that encodes a decision more precisely than prose can (a state machine, a reducer, a schema, a type shape) — inline just the decision-rich part, note it came from a prototype, and skip the working-demo scaffolding around it.
