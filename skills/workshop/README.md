# workshop/

Public because feedback is the point, not because they're finished. Nothing here ships in the plugin, none of it gets a stability promise — folders can rename or vanish between one clone and the next.

Grab one directly, since the plugin bundle skips this whole folder:

```bash
npx skills@latest add sudhindradesai/sudhindra-skills --skill=<name>
```

- **[spec-loop](./spec-loop/SKILL.md)** *(user-invoked)* — grills you into an implementable workflow spec across multiple sessions, treating the working directory as persistent state
- **[background-relay](./background-relay/SKILL.md)** *(user-invoked)* — hands the live conversation to a fresh background agent via `claude --bg`, seeded with a handoff summary so it starts already caught up
- **[ts-modules-rig](./ts-modules-rig/SKILL.md)** *(user-invoked)* — wires `dependency-cruiser` into a TypeScript repo so every package becomes a deep module: internals hidden, entry points the only door in, tests entering through that same door
- **[beat-sheet](./beat-sheet/SKILL.md)** — shapes an article as a chain of beats, choose-your-own-adventure style: write one beat, decide the next, repeat until it lands
- **[fragment-miner](./fragment-miner/SKILL.md)** — an interview that mines you for raw fragments and appends them to one running document, material for an article that doesn't exist yet
- **[shape-draft](./shape-draft/SKILL.md)** — takes a pile of raw fragments and shapes them into an article one paragraph at a time, arguing the format choice at each step
