---
name: blueprint
description: Turn the current conversation into a spec and publish it to the project issue tracker — no interview, just synthesis of what you've already discussed.
disable-model-invocation: true
---

Synthesis, not interview. Everything this skill writes down should already be sitting in the conversation and the codebase — if it isn't, that's a `/cross-examine` gap to go fix, not something to guess at here.

The issue tracker and triage label vocabulary should already be available to you. If they aren't, send the user to `/bootstrap` first.

**Before writing anything:** explore the repo enough to know its current shape, if you haven't already — use the project's domain glossary throughout, and respect whatever ADRs already govern the area you're about to touch. Then sketch the seam this feature will be tested at. Prefer a seam that already exists over inventing one; if a new seam is genuinely needed, put it as high as it'll go. Every extra seam is a cost — one, for the whole feature, is the number to aim for. Show the user the seam before moving on; it should match what they had in mind.

With that settled, write the spec below and publish it to the tracker, labeled `ready-for-agent` — it doesn't need another pass through `/intake`.

<spec-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this spec.

## Further Notes

Any further notes about the feature.

</spec-template>
