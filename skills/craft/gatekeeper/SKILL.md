---
name: gatekeeper
description: Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes — Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/spec asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to "review since X".
---

Reviews the diff between `HEAD` and a fixed point along two axes that never get to influence each other:

- **Standards** — does the code conform to what this repo documents about how code should be written?
- **Spec** — does the code faithfully implement whatever issue or spec started it?

Each axis runs in its own **parallel sub-agent**, kept apart on purpose so neither one's findings color the other's. This skill's own job is just pinning the inputs down and aggregating what comes back.

The issue tracker should already be available to you. If `docs/agents/issue-tracker.md` doesn't exist, send the user to `/bootstrap`.

### Pinning the fixed point

Take whatever the user names — a SHA, a branch, a tag, `main`, `HEAD~5`. Ask if they didn't say.

Capture the diff command once, `git diff <fixed-point>...HEAD` (three-dot — compare against the merge-base, not the literal tip), alongside `git log <fixed-point>..HEAD --oneline` for the commit list. Confirm the ref resolves (`git rev-parse <fixed-point>`) and the diff isn't empty *before* going further — a bad ref should fail right here, not silently inside two sub-agents you've already spawned.

### Finding the spec

Look, in order: issue references inside the commit messages (`#123`, `Closes #45`, GitLab `!67`, fetched via `docs/agents/issue-tracker.md`'s workflow); a path the user passed in directly; a spec file under `docs/`, `specs/`, or `.scratch/` matching the branch or feature name; and if none of that turns anything up, just ask. "There isn't one" is a valid answer — the Spec sub-agent then reports "no spec available" instead of running blind.

### Finding the standards

Whatever the repo documents about how code should be written — `CODING_STANDARDS.md`, `CONTRIBUTING.md`, anything like them.

Underneath whatever's documented, the Standards axis always carries a fixed **smell baseline** — Fowler's code smells (*Refactoring*, ch. 3) — so there's a floor even in a repo that documents nothing. Two rules keep it in check: the repo always overrides — where a documented standard explicitly endorses something the baseline would flag, the smell gets suppressed; and every smell is a labeled heuristic ("possible Feature Envy"), never a hard violation, same as anything else on this axis — skip whatever tooling already enforces.

Each entry below is *what it looks like* → *how you'd fix it*:

- **Mysterious Name** — a function, variable, or type whose name doesn't say what it does or holds. → Rename it; if no honest name presents itself, the design underneath is probably the actual problem.
- **Duplicated Code** — the same logic shape shows up in more than one hunk or file. → Extract the shared shape, call it from both sites.
- **Feature Envy** — a method reaching into another object's data more than its own. → Move the method to sit with the data it wants.
- **Data Clumps** — the same handful of fields or params keep traveling together. → That's a type asking to be born; bundle them, pass the bundle.
- **Primitive Obsession** — a bare primitive or string standing in for a domain concept that deserves its own type. → Give the concept a small type of its own.
- **Repeated Switches** — the same switch or if-cascade on the same type recurs across the change. → Polymorphism, or one shared map, replaces both sites.
- **Shotgun Surgery** — one logical change forces scattered edits across many files. → Gather what changes together into a single module.
- **Divergent Change** — one file or module gets edited for several unrelated reasons. → Split it so each piece changes for exactly one reason.
- **Speculative Generality** — abstraction, parameters, or hooks added for a need the spec doesn't actually have. → Delete it; inline back until a real need shows up.
- **Message Chains** — a long `a.b().c().d()` walk the caller has no business depending on. → Hide the walk behind one method on the first object.
- **Middle Man** — a class or function that mostly just forwards the call onward. → Cut it out, call the real target directly.
- **Refused Bequest** — a subclass or implementer that ignores or overrides most of what it inherits. → Drop the inheritance, reach for composition instead.

### Running both reviews

**Standards sub-agent** gets: the diff command and commit list; every standards-source file found above, *plus the smell baseline pasted in full* — it has no other way to see it; and the brief: "Report — per file/hunk where relevant — (a) every place the diff violates a documented standard, citing the standard by file and rule, and (b) any baseline smell you spot, named and quoted from the hunk. Keep hard violations (documented-standard breaches) distinct from judgement calls (baseline smells are always judgement calls, and a documented repo standard beats the baseline). Skip whatever tooling already enforces. Under 400 words."

**Spec sub-agent** gets: the diff command and commit list; the spec's path or fetched contents; and the brief: "Report: (a) requirements the spec asked for that are missing or partial, (b) behavior in the diff the spec never asked for, (c) requirements that look implemented but whose implementation looks wrong. Quote the spec line behind each finding. Under 400 words." Skip this sub-agent entirely, and note it, if there's no spec.

### Aggregating what comes back

Present both reports verbatim (or lightly cleaned) under their own `## Standards` and `## Spec` headings. Don't merge them, don't rerank across them — the separation is the point (see below). Close with one line per axis: total findings, and the worst issue *within that axis* — never a single overall winner, since picking one is exactly the reranking the two axes exist to prevent.

### Why the axes stay apart

A change can pass one and fail the other outright: code that follows every standard but builds the wrong thing is **Standards pass, Spec fail**; code that does precisely what the issue asked but breaks the project's own conventions is **Spec pass, Standards fail**. Report them together and one axis quietly buries the other.
