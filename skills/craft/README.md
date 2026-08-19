# craft/

The skills that touch code every day. If you only install one bucket, install this one.

Split by who's allowed to pull the trigger — see `.agents/invocation.md` at the repo root for the full rule, the short version is below each heading.

## User-invoked — you type these

The model won't reach for these on its own (`disable-model-invocation: true`, mirrored in `agents/openai.yaml`). They're the orchestrators — the ones that kick off a flow rather than execute a step inside one.

| Skill | What it starts |
| --- | --- |
| **[compass](./compass/SKILL.md)** | Doesn't know your answer, only the map — points you at whichever flow below fits what you're doing |
| **[cross-examine](./cross-examine/SKILL.md)** | An interview that also grows `CONTEXT.md` and its ADRs as it goes, so the vocabulary sharpens in the same pass |
| **[intake](./intake/SKILL.md)** | Runs incoming issues through the triage state machine until each one is labeled and ready |
| **[foundation-check](./foundation-check/SKILL.md)** | Surveys the codebase for deepening candidates, hands you an HTML report, then interviews you through whichever one you pick |
| **[bootstrap](./bootstrap/SKILL.md)** | One-time per-repo setup: issue tracker, triage labels, where domain docs live |
| **[blueprint](./blueprint/SKILL.md)** | Turns the conversation you're already in into a spec, filed to the tracker |
| **[breakdown](./breakdown/SKILL.md)** | Splits a spec or plan into tracer-bullet tickets, each one honest about what blocks it |
| **[build](./build/SKILL.md)** | Executes a spec or ticket set — drives `redgreen` at the agreed seams, closes with `gatekeeper` before commit |
| **[trailmap](./trailmap/SKILL.md)** | For work too large for one session: a shared map of decision tickets, resolved one at a time until the fog clears |

## Model-invoked — either of you can start these

No `disable-model-invocation` flag, so the model can reach for these unprompted when a task calls for the discipline they hold — you can also name them directly.

| Skill | The discipline it holds |
| --- | --- |
| **[sketch](./sketch/SKILL.md)** | Throwaway code that answers one design question — a single HTML file, or several UI variants side by side |
| **[unravel](./unravel/SKILL.md)** | Hard-bug diagnosis: reproduce → minimize → hypothesize → instrument → fix → lock in with a regression test |
| **[scout](./scout/SKILL.md)** | Sends a background agent after primary sources, comes back with a cited Markdown file |
| **[redgreen](./redgreen/SKILL.md)** | Red-green-refactor, one vertical slice of behavior at a time |
| **[lexicon](./lexicon/SKILL.md)** | Actively sharpens the project's domain language and writes the hard calls down as ADRs |
| **[workbench](./workbench/SKILL.md)** | Vocabulary and discipline for deep modules — small interface, a lot behind it, a clean seam to place it at |
| **[gatekeeper](./gatekeeper/SKILL.md)** | Two parallel reviews of a diff — does it meet the repo's standards, does it match the spec — so neither pollutes the other |
| **[peacemaker](./peacemaker/SKILL.md)** | Resolves an in-progress merge or rebase hunk by hunk, by intent, never by `--abort` |
| **[handrail](./handrail/SKILL.md)** | Builds an interactive script for the steps only a human can actually do — credentials, dashboards, one-off cutovers |
