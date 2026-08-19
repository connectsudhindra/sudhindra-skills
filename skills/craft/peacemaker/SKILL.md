---
name: peacemaker
description: "Use when you need to resolve an in-progress git merge/rebase conflict."
---

1. **Survey the state.** Where the merge or rebase currently stands, git history on both sides, and every file still in conflict.

2. **Trace each conflict to its primary source.** Not just what changed — why. Commit messages, the PR it came from, the issue behind it. Understand the intent before touching a line.

3. **Resolve hunk by hunk, preserving both intents wherever they're compatible.** Where they genuinely aren't, pick whichever matches the merge's stated goal and write down the trade-off you made. Never invent behavior neither side asked for. Every hunk gets resolved — `--abort` is off the table.

4. **Run whatever automated checks this project already has** — typecheck, tests, format, in that order is typical. Fix anything the merge itself broke.

5. **Close it out.** Stage everything, commit. Mid-rebase, keep running `rebase --continue` until every commit in the sequence has landed.
