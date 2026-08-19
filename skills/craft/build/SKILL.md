---
name: build
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Build what the spec or tickets describe.

Drive `/redgreen` at whatever seams were already agreed — don't invent new ones mid-build.

Typecheck often. Run the single test file you're working against often. Run the whole suite once, at the end, not before.

When it's done, hand it to `/gatekeeper` before you consider it done — that's the review gate, not optional polish.

Commit to the current branch once `/gatekeeper` is satisfied.
