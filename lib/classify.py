"""Task type classification from prompt text.

Uses keyword heuristics to classify prompts into one of six task types:
debugging, refactoring, generation, review, analysis, testing.
"""

import re
from enum import Enum


class TaskType(str, Enum):
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    GENERATION = "generation"
    REVIEW = "review"
    ANALYSIS = "analysis"
    TESTING = "testing"


# Keyword sets for classification (ordered by priority)
_DEBUGGING_KEYWORDS = [
    r"\bfix\b", r"\bbug\b", r"\berror\b", r"\bfail(?:s|ed|ure)?\b",
    r"\bexception\b", r"\bstack\s*trace\b", r"\bnpe\b", r"\bnull\s*pointer\b",
    r"\btrace\b", r"\broot\s*cause\b", r"\bdebug\b", r"\bissue\b",
    r"\bcrash(?:es|ed)?\b", r"\b500\s*error\b", r"\bthrow\s*(new\s+)?\w*exception\b",
]

_REFACTORING_KEYWORDS = [
    r"\brefactor\b", r"\brestructure\b", r"\brename\b", r"\breorganize\b",
    r"\bextract\b", r"\bsimplify\b", r"\bclean\s*up\b", r"\bdecompose\b",
    r"\bcomposition\s*(over|vs)\s*inheritance\b", r"\bapply\s*\w+\s*pattern\b",
    r"\bmove\s*(method|class|field)\b", r"\breplace\s*inheritance\b",
]

_GENERATION_KEYWORDS = [
    r"\b(add|create|build|implement|write|develop|scaffold|draft|generate|design)\b",
    r"\bnew\s+(class|service|endpoint|controller|resource|handler|module)\b",
    r"\bendpoint\b", r"\bcrud\b", r"\bapi\b",
]

_REVIEW_KEYWORDS = [
    r"\breview\b", r"\bcode\s*review\b", r"\bpr\b", r"\bpull\s*request\b",
    r"\bdiff\b", r"\bsecurity\s*(issue|vuln|audit|check)\b",
    r"\bsolid\s*principle", r"\bbest\s*practic",
]

_TESTING_KEYWORDS = [
    r"\btests?\b", r"\bspec\b", r"\bassert\b", r"\bmock\b", r"\bstub\b",
    r"\bunit\s*tests?\b", r"\bintegration\s*tests?\b", r"\be2e\b",
    r"\btdd\b", r"\btest\s*cases?\b", r"\bcoverage\b",
]


_KEYWORD_MAP = [
    (TaskType.DEBUGGING, _DEBUGGING_KEYWORDS),  # First - most critical
    (TaskType.REFACTORING, _REFACTORING_KEYWORDS),
    (TaskType.REVIEW, _REVIEW_KEYWORDS),
    (TaskType.TESTING, _TESTING_KEYWORDS),
    (TaskType.GENERATION, _GENERATION_KEYWORDS),
]


def classify_task(prompt: str) -> TaskType:
    """Classify a prompt into one of six task types using keyword heuristics.

    Priority order: debugging > refactoring > review > testing > generation > analysis (default).
    Returns TaskType.ANALYSIS as the fallback for ambiguous or generic prompts.
    """
    text = prompt.lower()

    for task_type, patterns in _KEYWORD_MAP:
        for pattern in patterns:
            if re.search(pattern, text):
                return task_type

    return TaskType.ANALYSIS


def is_root_prompt(prompt: str) -> bool:
    """Detect whether a prompt initiates a new request vs. answers a clarification.

    Root prompts are typically longer and contain action-oriented keywords.
    Clarification answers are short responses (single words, "yes", "no",
    multiple-choice selections like "A", or approval phrases).
    """
    text = prompt.strip().lower()

    # Very short responses are almost always clarifications
    if len(text) <= 5:
        return False

    # Common approval/continuation phrases
    approval_phrases = [
        "yes", "no", "looks good", "approved", "done", "perfect",
        "go ahead", "proceed", "sounds good", "that works",
        "let me know", "i think", "i would", "i will implement",
        "i'll", "sure", "ok", "okay",
    ]
    if text in approval_phrases:
        return False
    for phrase in approval_phrases:
        if text == phrase or text.startswith(phrase + " "):
            # But "I will implement later" is a deferral, not a root
            if "implement later" in text or "implement when" in text:
                return False
            return False

    # Root prompts typically contain action verbs or task keywords
    root_keywords = [
        r"\b(add|create|build|implement|write|fix|change|update|remove|delete|design|scaffold|generate|refactor|review|test)\b",
        r"\b(how|why|what|where|when|can you|could you|please)\b",
        r"\b(make|set up|configure|install|deploy|run)\b",
    ]
    for pattern in root_keywords:
        if re.search(pattern, text):
            return True

    # Default: if it's longer than a short answer AND has no root keywords,
    # treat as clarification (e.g., "Gradle with Kotlin DSL" is a selection,
    # not a new request). Require both sufficient length AND action keywords
    # to qualify as a root prompt by default.
    return False
