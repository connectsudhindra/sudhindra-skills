---
name: precommit-rig
description: Set up Husky pre-commit hooks with lint-staged (Prettier), type checking, and tests in the current repo. Use when user wants to add pre-commit hooks, set up Husky, configure lint-staged, or add commit-time formatting/typechecking/testing.
---

# Precommit Rig

Wires up **Husky** as the pre-commit hook, **lint-staged** running Prettier across staged files, a **Prettier** config if none exists yet, and a **typecheck** + **test** pass inside the hook itself.

Detect the package manager before touching anything — `package-lock.json` means npm, `pnpm-lock.yaml` means pnpm, `yarn.lock` means yarn, `bun.lockb` means bun, and npm is the fallback when none of them are present.

Install `husky lint-staged prettier` as devDependencies, then `npx husky init` — this creates `.husky/` and adds `prepare: "husky"` to `package.json` on its own.

Write `.husky/pre-commit` (no shebang needed on Husky v9+):

```
npx lint-staged
npm run typecheck
npm run test
```

Swap `npm` for whichever package manager step 1 detected. If the repo has no `typecheck` or `test` script, drop those lines and tell the user why.

Write `.lintstagedrc`:

```json
{
  "*": "prettier --ignore-unknown --write"
}
```

Write `.prettierrc` — only if no Prettier config already exists:

```json
{
  "useTabs": false,
  "tabWidth": 2,
  "printWidth": 80,
  "singleQuote": false,
  "trailingComma": "es5",
  "semi": true,
  "arrowParens": "always"
}
```

**Before calling it done, confirm:** `.husky/pre-commit` exists and is executable; `.lintstagedrc` exists; `package.json`'s `prepare` script reads `"husky"`; a Prettier config exists; `npx lint-staged` actually runs clean.

**Commit last**, with everything staged and the message `Add pre-commit hooks (husky + lint-staged + prettier)` — the commit itself runs straight through the new hook, which doubles as the smoke test that the whole rig works.

A couple of things worth knowing going in: Husky v9+ genuinely doesn't need a shebang in its hook files; `prettier --ignore-unknown` quietly skips whatever Prettier can't parse (images and the like); and the ordering inside the hook is deliberate — lint-staged first because it's fast and staged-only, typecheck and the full test suite after.
