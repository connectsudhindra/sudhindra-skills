"""Pure, dependency-free GCCF scorer.

Deliberately stdlib-only (`re`, `dataclasses`) so this module can be imported
directly by coach/hooks/on_prompt_submit.py without pulling in the API's own
dependency set -- the in-session blocking decision must never wait on a pip
environment resolving, let alone a network call. The API imports this same
module for the "heuristic" row in prompt_scores, so there is exactly one
implementation of the rules, never two copies to keep in sync.

Each dimension is scored 0-100 from a small set of independent signals, each
worth a fixed share of the total. This is intentionally legible over clever:
every point awarded traces to one named signal, so a false positive/negative
is easy to find and fix.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_IMPERATIVE_VERBS = (
    "add", "fix", "refactor", "implement", "investigate", "write", "create",
    "update", "remove", "delete", "debug", "optimize", "review", "explain",
    "generate", "build", "migrate", "test", "design", "document", "rename",
    "extract", "move", "split", "merge", "replace", "upgrade", "configure",
    "set up", "setup", "wire", "hook up", "diagnose", "profile", "audit",
    "clean up", "cleanup", "simplify", "improve", "check", "verify",
)

_ARTIFACT_NOUNS = (
    "function", "file", "component", "bug", "test", "api", "endpoint",
    "feature", "class", "module", "hook", "script", "query", "schema",
    "migration", "route", "handler", "service", "config", "type", "interface",
    "button", "form", "page", "table", "column", "index", "job", "worker",
    "pipeline", "workflow", "skill", "prompt", "error", "exception", "bug",
)

_CONTEXT_ERROR_WORDS = ("error", "exception", "traceback", "stack trace", "failed", "failure")
_CONTEXT_CONDITIONAL = ("when ", "given ", "if ", "after ", "while ")
_FILE_PATH_RE = re.compile(r"\b[\w.-]+/[\w./-]+\.\w{1,6}\b")
_BACKTICK_RE = re.compile(r"`[^`]+`")
_QUOTED_RE = re.compile(r'"[^"]{8,}"|\'[^\']{8,}\'')

_NEGATION_SCOPE = (
    "don't touch", "do not touch", "without changing", "without modifying",
    "keep the same", "keep it the same", "must not", "should not",
    "don't break", "do not break", "don't remove", "do not remove",
    "leave alone", "no changes to", "avoid changing",
    "don't change", "do not change", "don't alter", "do not alter",
    "keep unchanged", "leave unchanged", "don't rename", "do not rename",
)
_REQUIREMENT_WORDS = (
    " must ", " should ", " only ", " within ", " limit", " avoid ",
    " preserve", "backward compat", " no more than", " at most", " at least",
)

_FORMAT_WORDS = (
    "pull request", " pr ", "diff", "table", "json", "markdown",
    "bullet point", "function signature", "respond with", "return a",
    "as a list", "summary", "checklist", "one paragraph", "one-line",
    "in the format", "formatted as", "yaml", "csv",
)


@dataclass(frozen=True)
class GCCFScore:
    goal: float
    context: float
    constraints: float
    format: float
    rationale: str

    @property
    def composite(self) -> float:
        return round((self.goal + self.context + self.constraints + self.format) / 4, 2)


def _score_goal(text: str, lower: str, words: list[str]) -> tuple[float, str]:
    score = 0.0
    notes: list[str] = []

    first_chunk = " ".join(words[:4]).lower()
    has_verb = any(v in first_chunk for v in _IMPERATIVE_VERBS)
    if has_verb:
        score += 35
    else:
        notes.append("no clear action verb up front")

    has_artifact = any(n in lower for n in _ARTIFACT_NOUNS) or bool(_BACKTICK_RE.search(text))
    if has_artifact:
        score += 35
    else:
        notes.append("no concrete artifact named")

    if len(words) >= 6:
        score += 30
    elif len(words) >= 3:
        score += 15
        notes.append("goal stated very tersely")
    else:
        notes.append("too short to state a real goal")

    return min(score, 100.0), "; ".join(notes) or "clear action + artifact"


def _score_context(text: str, lower: str) -> tuple[float, str]:
    score = 0.0
    notes: list[str] = []

    if _FILE_PATH_RE.search(text) or _BACKTICK_RE.search(text):
        score += 40
    else:
        notes.append("no file/identifier referenced")

    if any(w in lower for w in _CONTEXT_ERROR_WORDS) or _QUOTED_RE.search(text):
        score += 30
    else:
        notes.append("no error text or quoted detail")

    if any(text.lower().startswith(w) or f" {w}" in lower for w in _CONTEXT_CONDITIONAL):
        score += 30
    else:
        notes.append("no situational framing (when/given/after...)")

    return min(score, 100.0), "; ".join(notes) or "situates the request well"


def _score_constraints(lower: str) -> tuple[float, str]:
    score = 0.0
    notes: list[str] = []

    if any(p in lower for p in _NEGATION_SCOPE):
        score += 50
    else:
        notes.append("no explicit 'don't touch X'")

    if any(w in lower for w in _REQUIREMENT_WORDS):
        score += 50
    else:
        notes.append("no must/should/limit language")

    return min(score, 100.0), "; ".join(notes) or "scope is explicitly bounded"


def _score_format(lower: str) -> tuple[float, str]:
    score = 0.0
    notes: list[str] = []

    hits = sum(1 for w in _FORMAT_WORDS if w in lower)
    if hits >= 2:
        score = 100.0
    elif hits == 1:
        score = 60.0
        notes.append("only one format cue")
    else:
        notes.append("no output shape requested")

    return score, "; ".join(notes) or "output shape is specified"


def score_prompt(text: str) -> GCCFScore:
    """Score a single prompt 0-100 on each of Goal, Context, Constraints, Format."""
    text = text or ""
    lower = text.lower()
    words = text.split()

    goal, goal_note = _score_goal(text, lower, words)
    context, context_note = _score_context(text, lower)
    constraints, constraints_note = _score_constraints(lower)
    fmt, format_note = _score_format(lower)

    rationale = (
        f"Goal: {goal_note}. Context: {context_note}. "
        f"Constraints: {constraints_note}. Format: {format_note}."
    )
    return GCCFScore(goal=goal, context=context, constraints=constraints, format=fmt, rationale=rationale)
