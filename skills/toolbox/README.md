# toolbox/

Not daily drivers. Each one solves a narrow, specific problem well and then gets out of the way — reach in when the situation matches, ignore the rest of the time. None of these ship in the plugin; grab them individually if you want them.

- **[git-tripwire](./git-tripwire/SKILL.md)** — wires a Claude Code hook that stops dangerous git commands (force push, `reset --hard`, `clean -fd`, …) before they run
- **[shoehorn-migrate](./shoehorn-migrate/SKILL.md)** — converts test files off `as`-cast type assertions and onto `@total-typescript/shoehorn`
- **[coursework-scaffold](./coursework-scaffold/SKILL.md)** — lays out exercise directories: sections, problems, solutions, explainers, all at once
- **[precommit-rig](./precommit-rig/SKILL.md)** — wires up Husky + lint-staged (Prettier, typecheck, tests) as pre-commit gates
