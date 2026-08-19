"""Pure, dependency-free GCCF scorer.

Deliberately stdlib-only (`re`, `dataclasses`) so this module can be imported
directly by coach/hooks/on_prompt_submit.py without pulling in the API's own
dependency set -- the in-session blocking decision must never wait on a pip
environment resolving, let alone a network call. The API imports this same
module for the "heuristic" row in prompt_scores, so there is exactly one
implementation of the rules, never two copies to keep in sync.

Each dimension is scored 0-100 from a small set of independent, named
checks. This is the single source of truth for the *coaching* this system
gives, not just the score: every check that doesn't fire produces a
specific issue code, a plain-English explanation of what's missing, and one
concrete, actionable tip -- not just a number. `score_prompt` picks the
highest-leverage tip per dimension (the heaviest-weighted failing check),
because one clear next step beats a bulleted list nobody reads.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

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

STRONG_THRESHOLD = 65.0
WEAK_THRESHOLD = 35.0


def _status(score: float) -> str:
    if score >= STRONG_THRESHOLD:
        return "strong"
    if score >= WEAK_THRESHOLD:
        return "developing"
    return "weak"


@dataclass(frozen=True)
class Issue:
    code: str
    weight: float
    message: str
    tip: str


@dataclass(frozen=True)
class DimensionFeedback:
    score: float
    status: str
    issues: list[Issue] = field(default_factory=list)

    @property
    def top_tip(self) -> str | None:
        """The single highest-leverage fix -- the heaviest-weighted issue
        still open. None when the dimension is already strong."""
        if not self.issues:
            return None
        return max(self.issues, key=lambda i: i.weight).tip

    @property
    def message(self) -> str:
        if not self.issues:
            return "solid -- no changes needed here"
        return "; ".join(i.message for i in self.issues)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "status": self.status,
            "issues": [i.code for i in self.issues],
            "message": self.message,
            "tip": self.top_tip,
            # Per-issue detail (code/message/tip/weight), not just the codes
            # above -- this is what lets progress tracking attribute "most
            # common issue" to its own specific message and tip, rather than
            # falling back to the whole dimension's combined message.
            "issue_detail": [
                {"code": i.code, "weight": i.weight, "message": i.message, "tip": i.tip} for i in self.issues
            ],
        }


@dataclass(frozen=True)
class GCCFScore:
    goal: float
    context: float
    constraints: float
    format: float
    rationale: str
    dimensions: dict[str, DimensionFeedback] = field(default_factory=dict)

    @property
    def composite(self) -> float:
        return round((self.goal + self.context + self.constraints + self.format) / 4, 2)

    def dimensions_json(self) -> dict:
        return {name: fb.to_dict() for name, fb in self.dimensions.items()}


def _score_goal(text: str, words: list[str]) -> DimensionFeedback:
    score = 0.0
    issues: list[Issue] = []

    first_chunk = " ".join(words[:4]).lower()
    if any(v in first_chunk for v in _IMPERATIVE_VERBS):
        score += 35
    else:
        issues.append(Issue(
            "no_verb", 35,
            "doesn't open with a clear action verb",
            "Start with an imperative verb -- 'Fix', 'Add', 'Refactor', 'Investigate' -- "
            "naming exactly what you want done.",
        ))

    if any(n in " ".join(words).lower() for n in _ARTIFACT_NOUNS) or bool(_BACKTICK_RE.search(text)):
        score += 35
    else:
        issues.append(Issue(
            "no_artifact", 35,
            "doesn't name a concrete artifact",
            "Name the specific file, function, or component this targets.",
        ))

    if len(words) >= 6:
        score += 30
    elif len(words) >= 3:
        score += 15
        issues.append(Issue(
            "terse", 15,
            "states the goal very tersely",
            "Spell out what 'done' looks like in a full sentence, not a fragment.",
        ))
    else:
        issues.append(Issue(
            "too_short", 30,
            "doesn't say enough to state a real goal",
            "Spell out what 'done' looks like in a full sentence, not a fragment.",
        ))

    return DimensionFeedback(score=min(score, 100.0), status=_status(score), issues=issues)


def _score_context(text: str, lower: str) -> DimensionFeedback:
    score = 0.0
    issues: list[Issue] = []

    if _FILE_PATH_RE.search(text) or _BACKTICK_RE.search(text):
        score += 40
    else:
        issues.append(Issue(
            "no_reference", 40,
            "doesn't reference a file path or code identifier",
            "Point to the file, function, or identifier involved -- e.g. "
            "`src/services/user.py` or `getUserById`.",
        ))

    if any(w in lower for w in _CONTEXT_ERROR_WORDS) or _QUOTED_RE.search(text):
        score += 30
    else:
        issues.append(Issue(
            "no_detail", 30,
            "doesn't include error text or a specific example",
            "Paste the actual error message, stack trace, or a concrete example of the "
            "wrong output.",
        ))

    if any(lower.startswith(w) or f" {w}" in lower for w in _CONTEXT_CONDITIONAL):
        score += 30
    else:
        issues.append(Issue(
            "no_framing", 30,
            "doesn't give situational framing (when/given/after...)",
            "Describe the situation that triggers this -- e.g. 'when the cart is empty' "
            "or 'after the recent migration'.",
        ))

    return DimensionFeedback(score=min(score, 100.0), status=_status(score), issues=issues)


def _score_constraints(lower: str) -> DimensionFeedback:
    score = 0.0
    issues: list[Issue] = []

    if any(p in lower for p in _NEGATION_SCOPE):
        score += 50
    else:
        issues.append(Issue(
            "no_scope_limit", 50,
            "doesn't say what must stay unchanged",
            "State what shouldn't change -- e.g. 'don't touch the public API' or "
            "'keep the existing schema'.",
        ))

    if any(w in lower for w in _REQUIREMENT_WORDS):
        score += 50
    else:
        issues.append(Issue(
            "no_requirement", 50,
            "doesn't include any must/should/limit language",
            "Add a hard requirement if one exists -- e.g. 'must not exceed 3 retries' or "
            "'should preserve backward compatibility'.",
        ))

    return DimensionFeedback(score=min(score, 100.0), status=_status(score), issues=issues)


def _score_format(lower: str) -> DimensionFeedback:
    hits = sum(1 for w in _FORMAT_WORDS if w in lower)
    tip = "Ask for a specific format -- a diff, a table, a short summary, a checklist."

    if hits >= 2:
        return DimensionFeedback(score=100.0, status="strong", issues=[])
    if hits == 1:
        score = 60.0
        issues = [Issue("weak_format", 40, "gives only one format cue", tip)]
    else:
        score = 0.0
        issues = [Issue("no_format", 100, "doesn't request an output shape", tip)]

    return DimensionFeedback(score=score, status=_status(score), issues=issues)


def score_prompt(text: str) -> GCCFScore:
    """Score a single prompt 0-100 on each of Goal, Context, Constraints, Format,
    with structured, actionable feedback behind every number."""
    text = text or ""
    lower = text.lower()
    words = text.split()

    goal_fb = _score_goal(text, words)
    context_fb = _score_context(text, lower)
    constraints_fb = _score_constraints(lower)
    format_fb = _score_format(lower)

    dimensions = {"goal": goal_fb, "context": context_fb, "constraints": constraints_fb, "format": format_fb}
    rationale = (
        f"Goal: {goal_fb.message}. Context: {context_fb.message}. "
        f"Constraints: {constraints_fb.message}. Format: {format_fb.message}."
    )
    return GCCFScore(
        goal=goal_fb.score, context=context_fb.score,
        constraints=constraints_fb.score, format=format_fb.score,
        rationale=rationale, dimensions=dimensions,
    )
