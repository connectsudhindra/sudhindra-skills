# Who's allowed to press the button

Every skill in this repo answers one design question up front: can the model reach for it on its own, or does a human have to name it?

- **User-invoked.** Fires only when a human types its name. Mark it with `disable-model-invocation: true` in the frontmatter, and mirror that in `agents/openai.yaml` with `policy.allow_implicit_invocation: false`. Its `description` is written for the person scanning a slash-command list — plain summary, no trigger bait ("Use when the user says…").
- **Model-invoked.** The default shape: no `disable-model-invocation`, no `policy` block. Its `description` is written for the *model* instead — trigger phrasing on purpose ("Use when the user wants…, mentions…, asks for…") so the harness's own matching picks it up unprompted. Ask one question when deciding: would the model ever have a good reason to reach for this without being told to? If yes, model-invoked. Being reusable isn't the test — being autonomously useful is.

Both harnesses enforce the boundary their own way, but the boundary itself is universal: nothing but a human can fire a user-invoked skill, full stop — not even another skill. A user-invoked skill is free to call into model-invoked ones underneath it; it can never call a sibling orchestrator.

`agents/openai.yaml` rides next to every `SKILL.md` and carries the Codex-side metadata: `interface.display_name`, `interface.short_description`, and — only for the user-invoked half — the `policy.allow_implicit_invocation: false` twin of `disable-model-invocation`. Keep the pair honest: a skill can't be user-invoked in one harness and open in the other.

Every bucket `README.md`, and the top-level one, reflect this split directly — a **User-invoked** heading and a **Model-invoked** heading, nothing left ungrouped.

## How one skill pulls in another

Say it as an instruction to invoke a named tool, not as a cross-reference to go read. Write "call the Skill tool with `interview`," never a bare `/interview` dropped into prose and left for the model to infer as a command, and never a deep link straight into another skill's file. The tool-call phrasing is what actually fires reliably across harnesses — a name on its own is ambiguous about whose command syntax it belongs to, which is exactly why every mention here drops the leading slash. If a doc file is genuinely shared material, it lives inside the skill that owns it, and anyone who needs it gets there by invoking that skill — not by linking across folder boundaries.

That phrasing is for **operative** dependencies only — a skill's own steps telling the agent to go do something right now. A router just listing skills by name for a *person* to choose from (`compass`, any bucket `README.md`) isn't invoking anything, so plain labels are fine there.

One call, one skill. Needing two means two separate calls ("call the Skill tool for `interview`, then again for `lexicon`"), never one call carrying both names — that reads as a single call that somehow takes two arguments, which isn't the contract.

And this entire convention is scoped to model-invoked targets. A user-invoked skill can't be reached this way under any phrasing — that's the whole point of the boundary above. When a step's precondition is a user-invoked skill (`bootstrap`, say), write it as something for the *human* to go do — "tell the user to run `/bootstrap`" — never dress it up as a tool call.

## One more distinction: reading vocabulary vs. building it

Pulling a term out of `CONTEXT.md` to use it correctly is just reading — a one-line pointer, not an invocation of `lexicon`. `lexicon` is specifically the *active* discipline: challenging a fuzzy term, stress-testing it against an edge case, writing the decision down, updating `CONTEXT.md` in place. If nothing gets written, it wasn't `lexicon`.
