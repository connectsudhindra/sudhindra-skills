# The boundary tree

A **phase** is a chunk of work inside one session — grilling, implementing, QA — and it's deliberately fuzzy: a phase ends the moment you think *"okay, that part's done."* The **boundary** is the gap right after that moment, and it's the only place any of this decision belongs. Mid-phase there's nothing to decide — you either keep going or peel off a subagent. Compacting mid-phase is how an agent loses the thread it was just holding.

Five moves exist at a boundary: **Continue**, **`/clear`**, **`/relay`**, hand off to a **subagent**, or **`/compact`**. Walk the questions below in order, at the boundary, and take the first **yes**.

## 1. Can you just continue?

Ask it before anything else, because Continue is free — no context switch, nothing lost. Two things make the answer yes: the next phase needs *this* phase as a primary source, or the smart zone (~150k tokens of sharp reasoning on current models) still has room for what's next. Grilling into implementation is the standard case — the build wants the reasoning itself, not a summary of it, so continuing costs nothing and loses nothing. Rule this out before considering anything more expensive.

## 2. Is everything here disposable?

Not "did it go well" — is the exploration, the dead ends, the decisions all irrelevant to what happens next? If so, **`/clear`**: the cheapest real move on the board, instant, and it hands the whole window back. It isn't even terminal — the cleared session stays resumable if you need to go back.

Getting this one wrong is one-way, though. Clear a context that actually mattered and the **why** behind what you built is gone — no amount of reading the diff afterward brings it back.

## 3. Does something need to travel?

`/relay` is narrow by design — reach for it only when you're doing one of:

- switching harness (Claude → Codex),
- moving to a new directory or repo,
- handing the work to a colleague,
- or splitting off a side task you found mid-phase, without derailing what you're already doing.

That's the entire list. What `/relay` buys is **portability** — a file that survives the trip. Nothing traveling means nothing to write.

## 4. Can it run with you gone?

Scoped tight enough to execute with no steering, no you in the loop? Send it to a **subagent** and leave this session exactly where it is. Automated review is the textbook case — it reads the diff, reports back, needs nothing from you while it works.

## 5. Otherwise: `/compact`

If you got this far — the context is relevant, the harness and directory aren't changing, and you need to stay in the loop — this is where you land, and it's where most boundaries land. Give it an instruction (`/compact we're moving into QA on this area`) so the summary keeps what the next phase actually needs.

`/compact` sits at the **bottom** of this list on purpose, not the top. Everything above it is cheaper, or more precise, or both. The failure mode when people reach for it first is a fresh session that's confidently wrong about something the summary flattened into false certainty.

## Why order matters here: primary vs. secondary sources

Every move except Continue turns a **primary source** — the session as it actually happened — into a **secondary source**: a summary of it. The trade is always the same shape:

- **Primary** (Continue): all the information, all the noise, very little room left to move.
- **Secondary** (`/compact`, `/relay`): lossy, quieter, lots of room.

That's the whole reason question 1 comes first — lossiness is a cost, and you only pay it once staying costs more than it saves.

## None of this is mechanical

Every one of these five questions has taste built into it, and the same boundary can reasonably go two different ways on two different days. What actually matters is asking them **in this order**, **at the boundary** — not mid-sentence, and not skipped because `/compact` felt like the obvious default.
