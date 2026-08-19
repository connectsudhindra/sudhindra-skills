---
name: foundation-check
description: Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick.
disable-model-invocation: true
---

# Foundation Check

Surfaces architectural friction and proposes **deepening opportunities** — refactors that turn shallow modules into deep ones, aimed at testability and AI-navigability.

Two things this skill leans on before it starts: call the Skill tool with "workbench" for the architecture vocabulary it speaks throughout — **module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality** — plus its principles (the deletion test, "the interface is the test surface," "one adapter is a hypothetical seam, two is a real one"). Use these words exactly; don't drift into "component," "service," "API," or "boundary" instead. And read `CONTEXT.md` for the names good seams already have, and the ADRs under `docs/adr/` for decisions this run shouldn't re-litigate.

## Where to look

Scope before scanning — this is a YAGNI call. Deepening pays off on the parts of the codebase that are still actively changing, so weight recency: if the user named a direction — a module, a subsystem, a pain point — take it and skip straight past the inference below. Otherwise walk back through `git log --oneline` far enough to find real hot spots — files and areas that keep recurring — and let those pull your attention first. Scattered changes with no clear hot spot mean widen the net instead of guessing.

Read `CONTEXT.md` and any ADRs in the area before spawning a sub-agent to actually walk the code. No rigid heuristics here — explore organically, and pay attention to friction:

- Understanding one concept requires bouncing between many small modules
- A module is **shallow** — its interface is nearly as complex as what's behind it
- Pure functions got extracted purely for testability, while the real bugs still hide in how they're *called* (no **locality**)
- Tightly-coupled modules leak state or behavior across their own seam
- Something's untested, or hard to test through the interface it currently has

Run the **deletion test** on anything that looks shallow: deleting it — does complexity concentrate somewhere, or just relocate? "Concentrates" is the signal worth reporting.

## What you hand back

Write a self-contained HTML file to the OS temp directory — nothing lands in the repo itself. Resolve the temp path from `$TMPDIR` (falling back to `/tmp`, or `%TEMP%` on Windows), write to `<tmpdir>/architecture-review-<timestamp>.html` so every run gets its own file, then open it (`xdg-open` / `open` / `start`, by platform) and read the absolute path back to the user.

Build it with **Tailwind via CDN** for layout, **Mermaid via CDN** for anything graph-shaped — call graphs, dependencies, sequences — and hand-built CSS/SVG for the more editorial visuals (mass diagrams, cross-sections, collapse animations). Every candidate gets a **before/after visualization**; lean visual, not just prose.

Each candidate's card carries: **Files** (which modules are involved), **Problem** (why the current shape causes friction), **Solution** (plain-English description of the change), **Benefits** (framed in locality and leverage, plus what improves for testing), a side-by-side custom **before/after diagram**, and a **Recommendation strength** badge — `Strong`, `Worth exploring`, or `Speculative`. Close the report with a **Top recommendation** section naming which one to tackle first and why.

Talk about the domain in `CONTEXT.md`'s terms and the architecture in `/workbench`'s — if `CONTEXT.md` names "Order," the card says "the Order intake module," never "the FooBarHandler" or "the Order service."

A candidate that contradicts an existing ADR is worth surfacing only when the friction is real enough to justify reopening that ADR — flag it plainly (a warning callout: *"contradicts ADR-0007 — but worth reopening because…"*) rather than silently listing every refactor an ADR technically forbids.

[REPORT-TEMPLATE.md](REPORT-TEMPLATE.md) has the full HTML scaffold, diagram patterns, and styling.

Stop short of proposing interfaces at this stage. Once the file's written, just ask: "Which of these would you like to explore?"

## After they pick one

Call the Skill tool with "interview" to walk the decision tree together — constraints, dependencies, the shape of the deepened module, what ends up behind the seam, which tests survive.

Domain side effects happen inline, as decisions actually crystallize — call the Skill tool with "lexicon" to keep the model current while you go:

- Naming the deepened module after a concept `CONTEXT.md` doesn't have yet? Add it (create the file lazily if it doesn't exist).
- Sharpened a fuzzy term mid-conversation? Update `CONTEXT.md` right there, not later.
- User rejects the candidate for a load-bearing reason? Offer an ADR — *"Want me to record this so future reviews don't re-suggest it?"* — but only when a future explorer would actually need the reasoning to avoid repeating it; skip ephemeral reasons ("not worth it right now") and self-evident ones.
- Want alternative interfaces for the deepened module explored side by side? Call the Skill tool with "workbench" and use its design-it-twice parallel sub-agent pattern.
