---
name: coursework-scaffold
description: Create exercise directory structures with sections, problems, solutions, and explainers that pass linting. Use when user wants to scaffold exercises, create exercise stubs, or set up a new course section.
---

# Coursework Scaffold

Builds exercise directories that pass `pnpm ai-hero-cli internal lint` on the first try, then commits them.

**Naming.** Sections are `XX-section-name/` under `exercises/` (`01-retrieval-skill-building`). Exercises inside a section are `XX.YY-exercise-name/` (`01.03-retrieval-with-bm25`) — section number, then exercise number, dash-case throughout.

**Variants.** Every exercise carries at least one of `problem/` (student workspace, TODOs), `solution/` (reference implementation), `explainer/` (concept only, no TODOs). When stubbing without a stated preference, default to `explainer/`.

**What every subfolder needs.** A `readme.md` that isn't empty (a title line clears the bar) and has no broken links. When stubbing:

```md
# Exercise Title

Description here
```

Code in the subfolder means it also needs a `main.ts` with real content (>1 line) — but a readme-only stub is fine on its own.

**The lint rules, summarized:** subfolders exist per exercise; at least one of `problem/`, `explainer/`, or `explainer.1/` is present; the primary subfolder's `readme.md` exists and isn't empty; no `.gitkeep`, no `speaker-notes.md`, no broken links, no `pnpm run exercise` commands inside readmes; `main.ts` required per subfolder unless it's readme-only.

## Building from a plan

1. Parse the plan for section names, exercise names, and which variants each one needs.
2. `mkdir -p` every path.
3. Drop a titled stub `readme.md` into each variant folder.
4. Run `pnpm ai-hero-cli internal lint`.
5. Fix whatever it flags, and lint again until clean.

A plan that reads:

```
Section 05: Memory Skill Building
- 05.01 Introduction to Memory
- 05.02 Short-term Memory (explainer + problem + solution)
- 05.03 Long-term Memory
```

becomes:

```bash
mkdir -p exercises/05-memory-skill-building/05.01-introduction-to-memory/explainer
mkdir -p exercises/05-memory-skill-building/05.02-short-term-memory/{explainer,problem,solution}
mkdir -p exercises/05-memory-skill-building/05.03-long-term-memory/explainer
```

with a titled readme dropped into each leaf folder — `# Introduction to Memory`, `# Short-term Memory` (×3, one per variant), `# Long-term Memory`.

## Renumbering later

Use `git mv`, never plain `mv` — it's the only way the rename keeps its git history. Update the numeric prefix as part of the same move, and re-lint once the dust settles:

```bash
git mv exercises/01-retrieval/01.03-embeddings exercises/01-retrieval/01.04-embeddings
```
