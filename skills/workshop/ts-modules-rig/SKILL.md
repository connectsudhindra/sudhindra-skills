---
name: ts-modules-rig
description: Wire dependency-cruiser into a TypeScript repo so each package is a deep module — implementation hidden in subfolders, reachable only through its entry-point files. User-invoked.
disable-model-invocation: true
---

# TS Modules Rig

Makes every package in the repo a **deep module**: a lot of behavior behind a small interface. A package's public surface is its **entry points** — the files sitting at its root — everything in a subfolder is hidden. Installs [dependency-cruiser](https://github.com/sverweij/dependency-cruiser) and the rules that make entry points the only door in, then proves the door actually locks.

For the vocabulary — deep module, interface, seam, depth — call the Skill tool with "workbench" and use its language throughout.

## The shape this enforces

```
src/packages/
  <name>/
    index.ts        ← an entry point (public). Import this from outside.
    client.ts       ← another entry point. Packages may expose SEVERAL.
    lib/             ← implementation: hidden from outside, free to import each other.
    tests/           ← co-located tests + fixtures (a subfolder, so private).
```

The public surface is every **root file** — not one designated `index.ts`. Implementation conventionally lives in `lib/`, tests in `tests/`, giving every package the same two-folder shape — but the underlying rule is general: anything in any subfolder is private, so a new folder never needs a config change.

Four rules, all `error`: **entry-point boundary** (code outside a package may import only that package's root files, never its subfolders); **intra-package freedom** (a package's own files import each other without restriction); **tests through the entry points** (`<pkg>/tests/` may import any package's entry points and its own `tests/` fixtures, never any package's subfolder internals — including its own; cross-package integration tests are fine, deep imports aren't); **no cycles**.

Public surface being *every* root file, not a barrel, means a package can expose several small entry points (`index.ts`, `client.ts`, `server.ts`) instead of funneling everything through one giant `index.ts` — barrel files re-exporting a whole subtree are actively discouraged; keep entry points small, hide the rest.

Layering — which packages may depend on which — is a separate concern, left as a commented stub in the config for this repo to fill in.

## Setting it up

**Read the environment before writing anything.** Package manager from the lockfile present (`pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, `bun.lockb` → bun, else npm) — use it for every command that follows. Packages root: `src/packages` if `src/` exists, else `packages`, confirmed with the user if the repo already leans toward a different convention. And check for an existing `.dependency-cruiser.*` — if one's there, merge the four rules in rather than overwrite, and say exactly what got added.

**Install `dependency-cruiser`** as a devDependency, via whichever package manager step above detected.

**Write the config.** Copy [`dc-rules.template.cjs`](./dc-rules.template.cjs) to the repo root as `.dependency-cruiser.cjs`, set `PACKAGES_ROOT` to what was detected. The rules are path-depth-based and extension-agnostic — nothing else needs adapting.

**Wire it into CI.** Add a `lint:boundaries` script (`depcruise <packages-root>`, or `depcruise src`). Fold it into whatever umbrella check already runs typecheck — a `check`/`ci`/`validate` script, typically — without touching `tsconfig` or adding path aliases. No umbrella script yet? Add `lint:boundaries` on its own and tell the user to wire it into CI themselves.

**Scaffold one example package**, committed, at `<packages-root>/example/` — an `index.ts` entry point exporting one function that delegates to an internal file (so it's visibly deep, not a pass-through), a `lib/impl.ts` doing the real work from inside a subfolder, and `tests/example.test.ts` importing only `../index` and asserting against the public function. Tell the user it's a starter template, theirs to copy or delete.

## Proving it actually bites

This is the completion criterion for the whole rig — a config that never fails on a violation isn't doing anything. Run `lint:boundaries` and watch it **pass** on the clean example. Add a deep import to `tests/example.test.ts` on purpose (`import { thing } from "../lib/impl"`), run it again, watch it **fail** with `tests-through-entrypoints`. Revert the import, run once more, watch it **pass** again. If the middle run doesn't fail, the rules aren't actually wired — that's not done, that's broken.

## Writing it down

A `README.md` **inside the packages folder itself** (`<packages-root>/README.md`, next to what it governs) covering the layout, "import only through a package's entry points," how to run `lint:boundaries`, and an explicit discouragement of barrel files — several small entry points beat one re-exported subtree. Keep each of the four rules to one paragraph.

Then point to it from the repo's agent-instructions file — `CLAUDE.md` if it exists, else `AGENTS.md` (created fresh if neither does). One line is enough: `Packages are deep modules — see [src/packages/README.md](./src/packages/README.md) before adding or importing one.` That line is what makes an agent discover the boundary rule instead of tripping over it mid-edit.

## Notes worth keeping in mind

The config's `$1` back-references (dependency-cruiser's group matching) are what let a package reach its own internals while outsiders can't — don't flatten them into separate per-package rules. Public versus private is decided purely by depth: root files are entry points, anything in a subfolder is private; `lib/` and `tests/` are convention, not hardcoded, so a new subfolder never needs a config change, and a new entry point is just a new root file, never a barrel. Packages stay flat — one tier of immediate children under the root; internals may nest arbitrarily deep, but a package may never contain another package. And the config uses `.cjs`, not `.js`, so `module.exports` still works even inside a `"type": "module"` repo.
