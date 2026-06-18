#!/usr/bin/env python3
"""
scripts/lint_editorial.py

Editorial linter for Auditmaton: Ads audit content. Encodes the Annielytics
writing rules (~/.claude/rules/editorial/annielytics-writing-rules.md) as
machine-checkable patterns and reports any violations in JSON content
files. With --fix, auto-applies the safe mechanical corrections.

Usage:
    python3 scripts/lint_editorial.py json/
    python3 scripts/lint_editorial.py json/ads/ad_density_placement.json
    python3 scripts/lint_editorial.py --fix json/ads/
    python3 scripts/lint_editorial.py --severity high json/
    python3 scripts/lint_editorial.py --format json json/

Exit codes:
    0 — no findings at or above the severity threshold (default: medium)
    1 — findings at or above the threshold
    2 — invalid invocation / unreadable input

The linter is meant to be called from:
  - pre-commit hook (scripts/git-hooks/pre-commit)
  - GitHub Actions (.github/workflows/lint-editorial.yml)
  - the /lint-editorial skill
  - any agent that writes or edits audit content (per the authoring brief)

Single source of truth for which patterns count as violations. Update
this file when the writing guide changes; the hook, CI, skill, and
agents pick it up automatically.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ========================================================================
#   Rule Definitions
# ========================================================================

# Generic marketese words banned in prose. Split into category-specific
# rule families (leverage, unlock, ecosystem, journey, artifact) below
# so the dashboard can filter by category. This list is the residue —
# pure marketese with no specific category.
MARKETESE_GENERIC_WORDS = [
    "seamless", "robust", "cutting-edge", "best-in-class", "comprehensive",
    "world-class", "next-generation", "next-gen", "revolutionary",
    "transformative", "holistic", "powerful", "intuitive", "supercharge",
    "empower", "scalable", "granular",
]

# Verb forms of "leverage". Noun forms ("highest-leverage", "leverage as
# a noun") tend to be legitimate, but the verb (leverage X, leveraging Y)
# is marketese. The pattern restricts to the verb forms.
LEVERAGE_VERB_FORMS = [
    "leverage", "leverages", "leveraged", "leveraging",
]

# "unlock" as a metaphor. Literal unlocking (a door, a phone) is fine but
# rare in audit prose; the metaphorical "unlock indexing" / "unlock
# value" / "unlock potential" is the actual target.
UNLOCK_FORMS = ["unlock", "unlocks", "unlocked", "unlocking"]

# Real product names that legitimately use "journey". The journey-metaphor
# rule excludes matches that fall inside one of these strings.
JOURNEY_ALLOWLIST = [
    "Customer Journey Analytics",
    "Adobe Journey Optimizer",
    "ObservePoint Journey",
    "AJO",  # Adobe Journey Optimizer abbreviation
    "CJA",  # Customer Journey Analytics abbreviation
    "buyer journey map",  # only as a concrete documented product term
]

# "artifact" used for any deliverable is banned; the historical/technical
# sense ("legacy artifact", "build artifact") is fine. Heuristic: the
# banned use co-occurs with deliverable language nearby.
ARTIFACT_DELIVERABLE_HINTS = [
    "the artifact", "this artifact", "deliverable",
    "produces an artifact", "produce an artifact",
    "output artifact", "final artifact",
]

# Verbs commonly paired with "quietly" / "silently" in AI-speak. Limiting
# the pattern to this list keeps false positives down (e.g., "silently
# fall back" in a technical sense is fine; "silently ignore" is not).
SILENTLY_VERBS = [
    "introduced", "launched", "updated", "rolled out", "added", "shipped",
    "ignore", "ignores", "ignoring",
    "prevent", "prevents", "preventing",
    "hide", "hides", "hiding",
    "drop", "drops", "dropping",
    "suppress", "suppresses", "suppressing",
    "orphan", "orphans", "orphaning",
    "erode", "erodes", "eroding",
    "disqualify", "disqualifies", "disqualifying",
    "generate", "generates", "generating",
    "cost", "costs", "costing",
    "block", "blocks", "blocking",
    "decay", "decays", "decaying",
    "remove", "removes", "removing",
    "fail", "fails", "failing",
]


def _wordlist_pattern(words):
    """
    Builds a regex alternation that matches any of `words` as whole
    tokens. Hyphenated terms are treated atomically. Case-insensitive.

    Args:
        words (list[str]): The vocabulary to match.

    Returns:
        re.Pattern: Compiled pattern.
    """

    escaped = [re.escape(w) for w in words]
    return re.compile(
        r"(?<![A-Za-z0-9])(" + "|".join(escaped) + r")(?![A-Za-z0-9])",
        re.IGNORECASE,
    )


# Field-path patterns where mid-sentence-colon checks make no sense.
# Procedural steps and titles routinely use colons as label separators
# ("Apparel: Brand + Gender + Product Type"); flagging those is noise.
COLON_SKIP_FIELDS = re.compile(
    r"\.steps\[|"
    r"\.title$|\.chart_title$|\.subcategory_title$|"
    r"\.logic$|\.fallback_message$|"
    r"\.manual\.intro$"
)


# Each rule: (id, severity, description, pattern, suggest, autofix)
#   autofix is either a callable (text -> text) or None when the fix
#   needs human judgment (most cases).
RULES = [
    {
        "id": "em-dash",
        "severity": "high",
        "description": "Em-dash (—) is banned. Replace with period or comma.",
        "pattern": re.compile(r"—"),
        "suggest": "Replace with a period, comma, or restructured sentence.",
        "autofix": None,
    },
    {
        "id": "en-dash",
        "severity": "high",
        "description": "En-dash (–) is banned. Replace with period or comma.",
        "pattern": re.compile(r"–"),
        "suggest": "Replace with a period, comma, or restructured sentence.",
        "autofix": None,
    },
    {
        "id": "horizontal-rule",
        "severity": "medium",
        "description": "Horizontal rule (---) is banned. Use headings for section breaks.",
        "pattern": re.compile(r"(?m)^---\s*$"),
        "suggest": "Remove the line; use a heading if a section break is needed.",
        "autofix": lambda t: re.sub(r"(?m)^---\s*$\n?", "", t),
    },
    {
        "id": "throat-clearing",
        "severity": "high",
        "description": '"It\'s important to note" / "This matters because" — AI framing.',
        "pattern": re.compile(
            r"it'?s important to note|this matters because",
            re.IGNORECASE,
        ),
        "suggest": "Cut the framing; state the point directly.",
        "autofix": None,
    },
    {
        "id": "not-just-framing",
        "severity": "high",
        "description": '"Not just X, it\'s Y" / "Isn\'t just X" — AI framing.',
        "pattern": re.compile(
            r"isn'?t just\b|not just\b[^.!?\n]{1,40}\b(but|it'?s)\b",
            re.IGNORECASE,
        ),
        "suggest": "Lead with the actual point; drop the contrast frame.",
        "autofix": None,
    },
    {
        "id": "silently-quietly",
        "severity": "high",
        "description": "quietly/silently + verb is banned (AI tell).",
        "pattern": re.compile(
            r"\b(quietly|silently)\s+(" + "|".join(SILENTLY_VERBS) + r")\b",
            re.IGNORECASE,
        ),
        "suggest": "Drop the adverb; describe the mechanism concretely.",
        "autofix": None,
    },
    {
        "id": "marketese-generic",
        "severity": "high",
        "description": "Banned marketese word in prose.",
        "pattern": _wordlist_pattern(MARKETESE_GENERIC_WORDS),
        "suggest": "Replace with a concrete, descriptive alternative.",
        "autofix": None,
    },
    {
        "id": "leverage-verb",
        "severity": "high",
        "description": '"leverage" as a verb is banned. Noun form is fine.',
        # Match leverage/leverages/leveraged/leveraging when followed by
        # whitespace and another word — i.e., used as a verb taking an
        # object. Avoids matching noun forms like "high-leverage".
        "pattern": re.compile(
            r"(?<![A-Za-z0-9-])(" + "|".join(LEVERAGE_VERB_FORMS) + r")\s+[a-zA-Z]",
            re.IGNORECASE,
        ),
        "suggest": 'Replace with "use", "apply", "draw on", or restructure.',
        "autofix": None,
    },
    {
        "id": "unlock-metaphor",
        "severity": "high",
        "description": '"unlock" used metaphorically is banned.',
        "pattern": _wordlist_pattern(UNLOCK_FORMS),
        "suggest": 'Replace with "enable", "release", "open", or describe the mechanism.',
        "autofix": None,
    },
    {
        "id": "ecosystem-metaphor",
        "severity": "high",
        "description": '"ecosystem" used metaphorically is banned. Biological sense is fine.',
        "pattern": _wordlist_pattern(["ecosystem", "ecosystems"]),
        "suggest": 'Replace with "stack", "landscape", "tools", or describe specifically.',
        "autofix": None,
    },
    {
        "id": "journey-metaphor",
        "severity": "high",
        "description": '"journey" used metaphorically is banned (product-name allowlist applies).',
        "pattern": _wordlist_pattern(["journey", "journeys"]),
        "suggest": 'Replace with "path", "process", "workflow", or describe the steps.',
        "autofix": None,
    },
    {
        "id": "artifact-deliverable",
        "severity": "high",
        "description": '"artifact" used for a deliverable is banned. Use "export", "brief", or "report".',
        # Match "artifact" only when deliverable-context language appears
        # within a small surrounding window. Avoids false-positives on
        # "legacy artifact", "build artifact", etc.
        "pattern": re.compile(r"\bartifacts?\b", re.IGNORECASE),
        "suggest": 'Replace with "export", "brief", "report", or describe specifically.',
        "autofix": None,
        "context_requirements": ARTIFACT_DELIVERABLE_HINTS,
    },
    {
        "id": "comma-before-because-since",
        "severity": "medium",
        "description": 'No comma before "because" or "since" introducing a reason.',
        "pattern": re.compile(r",\s+(because|since)\b"),
        "suggest": 'Remove the comma. Note: temporal "since" can rarely be a false positive.',
        "autofix": lambda t: re.sub(r",\s+(because|since)\b", r" \1", t),
    },
    {
        "id": "over-to-more-than",
        "severity": "medium",
        "description": '"Over <number>" for quantities should be "more than".',
        "pattern": re.compile(r"\bover\s+(\d)"),
        "suggest": 'Replace "over" with "more than".',
        "autofix": lambda t: re.sub(r"\bover\s+(\d)", r"more than \1", t),
    },
    {
        "id": "eg-ie-comma",
        "severity": "medium",
        "description": '"e.g." / "i.e." need a comma after.',
        "pattern": re.compile(r"\b(e\.g\.|i\.e\.)(?!,)"),
        "suggest": "Add a comma after the abbreviation.",
        "autofix": lambda t: re.sub(r"\b(e\.g\.|i\.e\.)(?!,)", r"\1,", t),
    },
    {
        "id": "mid-sentence-colon",
        "severity": "medium",
        "description": "Mid-sentence colon before a list/example/question in prose.",
        # Match a colon mid-prose followed by Cap-word, space, lowercase-
        # word. The trailing-lowercase requirement is what distinguishes
        # a real next-sentence start from a label pattern like "Apparel:
        # Brand + Gender" (no lowercase after Brand). False positives
        # from procedural steps and chart titles are filtered separately
        # via COLON_SKIP_FIELDS.
        "pattern": re.compile(r"[A-Za-z]:\s+[A-Z][a-z]+\s+[a-z]"),
        "suggest": "End the sentence with a period; start a new sentence after.",
        "autofix": None,
        "skip_field_pattern": COLON_SKIP_FIELDS,
    },
    {
        "id": "quote-comma-inside-single",
        "severity": "medium",
        "description": "Comma inside single quotes (should be outside).",
        "pattern": re.compile(r"[A-Za-z],'"),
        "suggest": "Move the comma outside the closing single quote: 'word', not 'word,'.",
        "autofix": lambda t: re.sub(r"([A-Za-z]),'", r"\1',", t),
    },
    {
        "id": "quote-question-inside-single",
        "severity": "medium",
        "description": "Question mark inside single quotes — questions belong in double quotes.",
        # Heuristic: question mark before single quote where the quoted
        # content is at least 8 characters (avoids matching short UI
        # labels like 'Own this business?').
        "pattern": re.compile(r"'[^']{12,}\?'"),
        "suggest": "Use double quotes for full sentences and questions.",
        "autofix": None,
    },
    {
        "id": "keyboard-shortcut-plus",
        "severity": "low",
        "description": "Keyboard shortcuts use hyphens, not plus signs (Ctrl-U, not Ctrl+U).",
        "pattern": re.compile(
            r"\b(Ctrl|Cmd|Command|Shift|Alt|Option|Win|Meta)\+[A-Za-z0-9]",
            re.IGNORECASE,
        ),
        "suggest": "Use hyphens between keys: Ctrl-U, not Ctrl+U.",
        "autofix": lambda t: re.sub(
            r"\b(Ctrl|Cmd|Command|Shift|Alt|Option|Win|Meta)\+(?=[A-Za-z0-9])",
            r"\1-",
            t,
            flags=re.IGNORECASE,
        ),
    },
    {
        "id": "missing-anchor-class",
        "severity": "low",
        "description": 'Anchor tag missing class="tools-link-no-padding".',
        # Match <a href=...> opening tag that DOES NOT contain
        # "tools-link-no-padding" within the same tag. Lookahead checks
        # that the rest of the opening tag (up to >) lacks the class.
        "pattern": re.compile(
            r"<a\s+(?![^>]*tools-link-no-padding)[^>]*href=", re.IGNORECASE
        ),
        "suggest": 'Add class="tools-link-no-padding" to the anchor tag.',
        "autofix": None,
    },
    {
        "id": "flag-when-semicolons",
        "severity": "medium",
        "description": '"Flag this check when: A; B; C." should be "Flag this check when A, B, C."',
        "pattern": re.compile(
            r"Flag this check when:\s+[^.]+;", re.IGNORECASE
        ),
        "suggest": 'Remove the colon and replace semicolons with commas.',
        "autofix": None,
    },
    {
        "id": "verify-colon",
        "severity": "medium",
        "description": '"Verify: A; B; C." / "Confirm: A; B; C." should drop the colon.',
        # Match "Verify:" or "Confirm:" at sentence boundaries; skip the
        # bracketed template-marker pattern "[VERIFY: ...]".
        "pattern": re.compile(
            r"(?<!\[)(?:^|[\s.;])(Verify|Confirm):\s+[A-Z]"
        ),
        "suggest": 'Drop the colon: "Verify A, B, C." not "Verify: A; B; C."',
        "autofix": None,
    },
    {
        "id": "fragment-list-intro",
        "severity": "medium",
        "description": "List introduced by a fragment, not a complete standalone sentence.",
        # Two high-confidence fragment shapes immediately before a <ul>:
        #   1. a lead-in ending in a weak connector whose object IS the list
        #      ("X include:", "X are:", "as follows:" before <ul>).
        #   2. a bare noun phrase ("Signs that X:", "Ways to confirm X:")
        #      that opens at a sentence boundary, has no main verb, and ends
        #      in a colon before the list. The boundary + relative-marker
        #      requirement keeps the complete-sentence pattern ("A few signs
        #      point to X:") from matching, since there the subject is
        #      preceded by "A few" and followed by a finite verb.
        "pattern": re.compile(
            r"\b(?:include|includes|are|following|below)\s*:\s*<ul>"
            r"|(?:^|[.>]\s*)(?:Signs|Patterns|Reasons|Conditions|Cases|Factors|"
            r"Symptoms|Ways|Indicators|Examples)\s+(?:that|of|which|to|for)\b"
            r"[^.<]{0,100}:\s*<ul>",
            re.IGNORECASE,
        ),
        "suggest": 'Introduce the list with a complete standalone sentence, e.g. "A few signs point to X:".',
        "autofix": None,
    },
]


# ========================================================================
#   JSON Field Extraction
# ========================================================================

# Field keys to skip during recursive walk — schema metadata, code
# samples, source URLs, file paths, and similar non-prose values.
SKIP_KEYS = {
    "code_snippet", "source_title", "source_url", "update_link",
    "id", "check_id", "category", "subcategory", "json_path",
    "file_path", "step", "url", "severity", "rule_category",
    "revised_at", "category_id", "audit_id", "before_text", "after_text",
    "column_dependencies", "data_dependencies", "important_note_url",
    # Skip examples-only fields where snippets are intentional reproductions
    # of bad-practice text (e.g., the qa_faq_content negative-examples list).
}

# Inline HTML / Markdown patterns to strip before running checks. These
# remove text inside <code>...</code> blocks (technical examples), inline
# code spans, and HTML anchor tags' attribute values so URLs and quoted
# attributes never trigger quote-punctuation rules.
CODE_BLOCK_RE = re.compile(r"<code[^>]*>.*?</code>", re.DOTALL | re.IGNORECASE)
PRE_BLOCK_RE = re.compile(r"<pre[^>]*>.*?</pre>", re.DOTALL | re.IGNORECASE)
ANCHOR_ATTR_RE = re.compile(r"<a\s+[^>]*>", re.IGNORECASE)

# Single-quoted reference pattern. Matches '<content>' where content is
# 8-80 chars, doesn't span newlines, and the opening quote sits at a
# word boundary (so contractions like "company's" don't match). Used to
# detect when a rule match falls inside a quoted UI label, button name,
# or example bad-practice phrase so those references aren't flagged.
QUOTED_REFERENCE_RE = re.compile(
    r"(?:^|[\s,(\[])'([^'\n]{8,80})'(?=[\s,.;:!?\)\]]|$)"
)

# Double-quoted reference pattern, used like the single-quoted one but
# for full-clause quoted examples (e.g., lecture titles, page titles
# shown as examples). Mid-sentence colons inside these references are
# part of the quoted example, not Annie's prose.
DOUBLE_QUOTED_REFERENCE_RE = re.compile(
    r'(?:^|[\s,(\[])"([^"\n]{8,150})"(?=[\s,.;:!?\)\]]|$)'
)

# Trigger phrases that appear NEAR a match to indicate the match is part
# of a quoted negative example or an instructional reference (telling
# readers what NOT to write), not Annie's own prose. Catches cases like
# "Using filler phrases like 'It's important to note that...'" where the
# AI-tell quote is inside a teaching example.
NEGATIVE_EXAMPLE_TRIGGERS = [
    "filler phrases",
    "filler phrase",
    "phrases like",
    "avoid phrases",
    "instead of writing",
    "examples of what",
    "phrases to avoid",
    "bad example",
    "negative example",
    "Don't write",
]


def extract_text_fields(obj, path=""):
    """
    Walks a JSON object recursively and yields (json_path, text) tuples
    for every prose field. Skips schema metadata, code snippets, and
    source URLs.

    Args:
        obj: A parsed JSON value (dict, list, str, or scalar).
        path (str): The accumulated dot-notation path used in the report.

    Yields:
        tuple[str, str]: (json_path, text) for each prose field.
    """

    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in SKIP_KEYS:
                continue
            child_path = f"{path}.{k}" if path else k
            yield from extract_text_fields(v, child_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from extract_text_fields(item, f"{path}[{i}]")
    elif isinstance(obj, str):
        if obj.strip():
            yield path, obj


def strip_code_and_html_attrs(text):
    """
    Removes content that should not trigger writing-rule checks:
    <code>...</code> spans, <pre>...</pre> blocks, and HTML anchor tags'
    attribute strings.

    Args:
        text (str): Raw field text.

    Returns:
        str: Text with code blocks and anchor attributes stripped.
    """

    text = CODE_BLOCK_RE.sub("", text)
    text = PRE_BLOCK_RE.sub("", text)
    text = ANCHOR_ATTR_RE.sub("", text)
    return text


# ========================================================================
#   Linter Engine
# ========================================================================

SEVERITY_LEVELS = {"low": 0, "medium": 1, "high": 2}


# Rules whose matches should be IGNORED when they fall inside a single-
# quoted reference span. Quoted UI labels, button names, and example
# bad-practice phrases legitimately contain banned words or framings.
RULES_SKIP_INSIDE_QUOTED = {
    "marketese-generic",
    "leverage-verb",
    "unlock-metaphor",
    "ecosystem-metaphor",
    "journey-metaphor",
    "artifact-deliverable",
    "throat-clearing",
    "not-just-framing",
    "silently-quietly",
    "quote-question-inside-single",
}

# Rules whose matches should be IGNORED when a "negative example"
# trigger phrase appears within 80 characters before the match. Used
# for AI-tell rules that legitimately appear inside teaching content
# that quotes the bad phrasing to warn against it.
RULES_SKIP_NEAR_NEGATIVE_EXAMPLE = {
    "throat-clearing",
    "not-just-framing",
}


def _has_negative_example_trigger(text, match_start):
    """
    Returns True if any NEGATIVE_EXAMPLE_TRIGGERS phrase appears within
    the 80 characters before `match_start`. Used to skip AI-tell rule
    hits that are quoted as bad-practice examples.

    Args:
        text (str): The full text being linted.
        match_start (int): Offset where the rule match begins.

    Returns:
        bool: Whether a negative-example trigger is nearby.
    """

    window = text[max(0, match_start - 80):match_start].lower()
    return any(trigger.lower() in window for trigger in NEGATIVE_EXAMPLE_TRIGGERS)


def _quoted_reference_spans(text):
    """
    Returns a list of (start, end) tuples for every single-quoted
    reference span in `text`. Used to decide whether a rule match
    sits inside a quoted UI label / negative-example phrase.

    Args:
        text (str): The text to scan.

    Returns:
        list[tuple[int, int]]: Spans covering the quoted content
            (inclusive of the quote characters).
    """

    return [(m.start(), m.end()) for m in QUOTED_REFERENCE_RE.finditer(text)]


def _is_inside_any(spans, start, end):
    """
    Returns True if [start, end) sits fully within any span in `spans`.

    Args:
        spans (list[tuple[int, int]]): The spans to test against.
        start (int): Match start offset.
        end (int): Match end offset.

    Returns:
        bool: Whether the match is inside one of the spans.
    """

    return any(s <= start and end <= e for s, e in spans)


def lint_text(text, rules, json_path=""):
    """
    Runs every rule against a single text string and yields findings.

    Args:
        text (str): The text to inspect.
        rules (list[dict]): Rule definitions from RULES.
        json_path (str): The JSON field path, used to honor per-rule
            field-skip patterns (e.g., mid-sentence-colon skips steps).

    Yields:
        dict: One finding per match with keys rule_id, severity,
            description, suggest, snippet, and match.
    """

    cleaned = strip_code_and_html_attrs(text)
    quoted_spans = _quoted_reference_spans(cleaned)
    double_quoted_spans = [
        (m.start(), m.end()) for m in DOUBLE_QUOTED_REFERENCE_RE.finditer(cleaned)
    ]

    for rule in rules:
        skip_field_re = rule.get("skip_field_pattern")
        if skip_field_re is not None and json_path and skip_field_re.search("." + json_path):
            continue

        for m in rule["pattern"].finditer(cleaned):
            # journey-metaphor gets a contextual allowlist pass for
            # documented product names (Customer Journey Analytics, etc.).
            if rule["id"] == "journey-metaphor":
                surrounding = cleaned[max(0, m.start() - 40):m.end() + 40]
                if any(allow.lower() in surrounding.lower() for allow in JOURNEY_ALLOWLIST):
                    continue

            # artifact-deliverable only fires when deliverable-context
            # language appears within 80 chars of the match. Avoids
            # false-positives on "legacy artifact" / "build artifact".
            if rule.get("context_requirements"):
                window = cleaned[max(0, m.start() - 80):m.end() + 80].lower()
                if not any(hint.lower() in window for hint in rule["context_requirements"]):
                    continue

            # Universal skip for matches that fall inside a single-quoted
            # reference span (UI labels, button names, negative-example
            # phrases). Only applies to rules where this exemption makes
            # sense — quote-comma-inside-single still fires inside quotes
            # because the violation IS the quoted content.
            if rule["id"] in RULES_SKIP_INSIDE_QUOTED and _is_inside_any(
                quoted_spans, m.start(), m.end()
            ):
                continue

            # Skip AI-tell rule matches that appear right after a
            # negative-example trigger like "filler phrases like" — those
            # quote bad phrasings as teaching examples.
            if rule["id"] in RULES_SKIP_NEAR_NEGATIVE_EXAMPLE and \
                    _has_negative_example_trigger(cleaned, m.start()):
                continue

            # Skip mid-sentence-colon matches inside double-quoted
            # references. Quoted page titles, lecture titles, and
            # similar examples legitimately contain "Topic: Subtopic"
            # patterns that aren't Annie's prose.
            if rule["id"] == "mid-sentence-colon" and _is_inside_any(
                double_quoted_spans, m.start(), m.end()
            ):
                continue

            ctx_start = max(0, m.start() - 30)
            ctx_end = min(len(cleaned), m.end() + 30)
            yield {
                "rule_id": rule["id"],
                "severity": rule["severity"],
                "description": rule["description"],
                "suggest": rule["suggest"],
                "snippet": cleaned[ctx_start:ctx_end].replace("\n", " "),
                "match": m.group(0),
            }


# Acronym-expansion pattern: an abbreviation spelled out in parentheses,
# e.g. "(GA4)", "(GTM)", "(ROAS)". Two or more of the SAME expansion on one
# rendered page is a double-expansion (see check_duplicate_acronym_expansion).
ACRONYM_EXPANSION_RE = re.compile(r"\(([A-Z][A-Za-z0-9]{1,7})\)")


def _page_groups(data):
    """
    Groups an audit-content file's prose fields into the units that render
    together on one page, so the abbreviation rule can enforce "expand at
    most once per rendered page".

    The subcategory Overview renders important_note + intro +
    worth_it_explanation together. Each check's educate step renders its
    impact_rationale + base + site_type_overlays together; each generate
    step renders its narrative_template alone.

    Args:
        data (dict): Parsed audit-content JSON (or any dict; non-audit
            files simply yield empty groups).

    Returns:
        list[tuple[str, str]]: (json_path_label, combined_text) per page.
    """

    def s(v):
        return v if isinstance(v, str) else ""

    pages = [(
        "overview",
        " ".join(s(data.get(k)) for k in ("important_note", "intro", "worth_it_explanation")),
    )]
    for i, check in enumerate(data.get("audit_checks", []) or []):
        if not isinstance(check, dict):
            continue
        edu = check.get("educate", {}) or {}
        overlays = edu.get("site_type_overlays", {}) or {}
        pages.append((
            f"audit_checks[{i}].educate",
            " ".join([s(check.get("impact_rationale")), s(edu.get("base"))]
                     + [s(v) for v in overlays.values()]),
        ))
        gen = check.get("generate", {}) or {}
        pages.append((
            f"audit_checks[{i}].generate.narrative_template",
            s(gen.get("narrative_template")),
        ))
    return pages


def check_duplicate_acronym_expansion(data, file_path):
    """
    File-level check: flags an abbreviation spelled out in parentheses more
    than once within a single rendered page (per _page_groups). Mirrors the
    per-page abbreviation rule in the authoring brief, which the per-field
    RULES engine cannot see because it spans sibling fields.

    Args:
        data (dict): Parsed JSON content.
        file_path (Path): Source file, for the finding record.

    Returns:
        list[dict]: Findings in the same shape lint_text yields.
    """

    findings = []
    if not isinstance(data, dict):
        return findings
    for label, text in _page_groups(data):
        counts = {}
        for acr in ACRONYM_EXPANSION_RE.findall(text):
            counts[acr] = counts.get(acr, 0) + 1
        for acr, n in counts.items():
            if n > 1:
                findings.append({
                    "file": str(file_path),
                    "json_path": label,
                    "rule_id": "duplicate-acronym-expansion",
                    "severity": "medium",
                    "description": f'Abbreviation "{acr}" is spelled out more than once on the same rendered page.',
                    "suggest": f'Expand "{acr}" once at its first occurrence on this page; use the bare form elsewhere.',
                    "snippet": f"({acr}) appears {n} times on this page",
                    "match": f"({acr})",
                })
    return findings


# Topic registries for the theme_tags check. The same json/_themes.json
# (valid topic slugs + their sides) and json/_platforms.json (platform ->
# side) that services/audit_engine.py reads. Loaded once at import.
def _load_registry(name, key):
    path = Path(__file__).resolve().parent.parent / "json" / name
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get(key, [])
    except (OSError, json.JSONDecodeError):
        return []


_THEMES = {t["slug"]: t for t in _load_registry("_themes.json", "themes")}
_PLATFORM_SIDE = {p["slug"]: p.get("side") for p in _load_registry("_platforms.json", "platforms")}


def _platform_side_from_path(file_path):
    """
    Derives a content file's platform side from its path
    (json/<platform>/<category>/<subcat>.json), or None.
    """

    parts = Path(file_path).parts
    if "json" in parts:
        i = parts.index("json")
        if i + 1 < len(parts):
            return _PLATFORM_SIDE.get(parts[i + 1])
    return None


def check_theme_tags(data, file_path):
    """
    File-level check: every audit check must carry at least one theme_tag,
    each tag must be a slug defined in json/_themes.json, and each tag must be
    valid on the platform's side (json/_platforms.json). Keeps the topic
    system first-class across every platform from the first check.

    Args:
        data (dict): Parsed audit-content JSON.
        file_path (Path): Source file (its path encodes the platform).

    Returns:
        list[dict]: Findings in the same shape lint_text yields.
    """

    findings = []
    if not isinstance(data, dict) or "audit_checks" not in data or not _THEMES:
        return findings
    side = _platform_side_from_path(file_path)
    for i, check in enumerate(data.get("audit_checks", []) or []):
        if not isinstance(check, dict):
            continue
        label = f"audit_checks[{i}].theme_tags"
        base = {"file": str(file_path), "json_path": label, "severity": "medium", "snippet": ""}
        tags = check.get("theme_tags")
        if not tags:
            findings.append({**base, "rule_id": "missing-theme-tags", "match": "",
                "description": "Check has no theme_tags. Every check must carry at least one topic from json/_themes.json.",
                "suggest": "Add a theme_tags array with one or more valid topic slugs."})
            continue
        for tag in tags:
            if tag not in _THEMES:
                findings.append({**base, "rule_id": "invalid-theme-tag", "match": tag,
                    "description": f'theme_tag "{tag}" is not defined in json/_themes.json.',
                    "suggest": "Use a topic slug defined in json/_themes.json."})
            elif side and side not in _THEMES[tag].get("sides", []):
                findings.append({**base, "rule_id": "theme-tag-wrong-side", "match": tag,
                    "description": f'theme_tag "{tag}" is not valid on the {side} side (this platform is {side}).',
                    "suggest": f'Use a topic whose sides include "{side}".'})
    return findings


# Human-readable label fields that SKIP_KEYS excludes from the general
# prose walk. Em-dashes and en-dashes are banned everywhere in Annie's
# house style, including citation titles, so scan these for dashes only
# (the general walk already covers every other prose field, and the
# colon/quote rules would false-positive on legitimate citation titles
# like "Guide: Section"). Without this, an em-dash in a source_title
# slips past every gate.
LABEL_DASH_FIELDS = {"source_title"}
LABEL_DASH_RE = re.compile("[—–]")


def check_label_dashes(obj, file_path, path=""):
    """
    File-level check: flag em-dashes and en-dashes inside human-readable
    label fields (e.g., source_title) that the general prose walk skips
    via SKIP_KEYS. Dashes are banned everywhere, so this closes the gap
    without subjecting citation titles to the colon and quote rules.

    Args:
        obj: A parsed JSON value (dict, list, str, or scalar).
        file_path (Path): Source file.
        path (str): Accumulated dot-notation path used in the report.

    Returns:
        list[dict]: Findings in the same shape lint_text yields.
    """

    findings = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{path}.{k}" if path else k
            if k in LABEL_DASH_FIELDS and isinstance(v, str):
                for m in LABEL_DASH_RE.finditer(v):
                    is_em = v[m.start()] == "—"
                    findings.append({
                        "file": str(file_path),
                        "json_path": child,
                        "rule_id": "em-dash" if is_em else "en-dash",
                        "severity": "high",
                        "description": "Em-dash or en-dash in a label field. Use a colon or comma.",
                        "suggest": "Replace the dash with a colon or comma.",
                        "snippet": v[max(0, m.start() - 25):m.start() + 25],
                        "match": v[m.start()],
                    })
            else:
                findings.extend(check_label_dashes(v, file_path, child))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            findings.extend(check_label_dashes(item, file_path, f"{path}[{i}]"))
    return findings


def lint_file(file_path, rules):
    """
    Lints a single JSON file.

    Args:
        file_path (Path): Path to a JSON file.
        rules (list[dict]): Rule definitions.

    Returns:
        list[dict]: Findings with file, json_path, and rule details.
    """

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [{
            "file": str(file_path),
            "json_path": "",
            "rule_id": "invalid-json",
            "severity": "high",
            "description": f"JSON parse error: {e}",
            "suggest": "Fix the JSON syntax.",
            "snippet": "",
            "match": "",
        }]
    except OSError as e:
        return [{
            "file": str(file_path),
            "json_path": "",
            "rule_id": "io-error",
            "severity": "high",
            "description": f"Cannot read file: {e}",
            "suggest": "Check file path and permissions.",
            "snippet": "",
            "match": "",
        }]

    findings = []
    for json_path, text in extract_text_fields(data):
        for v in lint_text(text, rules, json_path=json_path):
            v["file"] = str(file_path)
            v["json_path"] = json_path
            findings.append(v)
    # File-level check: abbreviation expanded twice on one rendered page.
    findings.extend(check_duplicate_acronym_expansion(data, file_path))
    # File-level check: every check carries valid, side-appropriate theme_tags.
    findings.extend(check_theme_tags(data, file_path))
    # File-level check: em/en-dashes in label fields (e.g., source_title)
    # that SKIP_KEYS otherwise hides from the general prose walk.
    findings.extend(check_label_dashes(data, file_path))
    return findings


def collect_files(targets):
    """
    Expands a list of file or directory paths into a flat list of JSON
    files to lint. Skips files outside the JSON audit content tree
    (e.g., editorial revision logs).

    Args:
        targets (list[str]): CLI args — file paths, directory paths,
            or globs.

    Returns:
        list[Path]: Paths to JSON files.
    """

    out = []
    for t in targets:
        p = Path(t)
        if p.is_dir():
            out.extend(sorted(p.rglob("*.json")))
        elif p.is_file() and p.suffix == ".json":
            out.append(p)
    # Filter out files in editorial/ — those are revision logs, not
    # audit content, and would self-trigger rules from quoted before/after
    # text snippets.
    out = [p for p in out if "editorial" not in p.parts]
    return out


# ========================================================================
#   Auto-fix
# ========================================================================

def apply_autofixes(file_path, rules):
    """
    Runs every rule's autofix in turn on the file's prose fields,
    rewriting the JSON in place when changes are made. Returns a list
    of (json_path, rule_id) tuples describing what was fixed.

    Args:
        file_path (Path): Path to a JSON file.
        rules (list[dict]): Rule definitions.

    Returns:
        list[tuple[str, str]]: (json_path, rule_id) per fix applied.
    """

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    fixes = []
    autofix_rules = [r for r in rules if r["autofix"] is not None]

    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k in list(obj.keys()):
                if k in SKIP_KEYS:
                    continue
                obj[k] = walk(obj[k], f"{path}.{k}" if path else k)
            return obj
        if isinstance(obj, list):
            return [walk(v, f"{path}[{i}]") for i, v in enumerate(obj)]
        if isinstance(obj, str):
            original = obj
            for rule in autofix_rules:
                new = rule["autofix"](obj)
                if new != obj:
                    fixes.append((path, rule["id"]))
                    obj = new
            return obj
        return obj

    new_data = walk(data)
    if fixes:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    return fixes


# ========================================================================
#   Reporting
# ========================================================================

# ANSI color codes for terminal output. Disabled when --no-color is set
# or when stdout is not a tty.
COLORS = {
    "reset": "\033[0m",
    "high": "\033[31m",      # red
    "medium": "\033[33m",    # yellow
    "low": "\033[36m",       # cyan
    "dim": "\033[2m",
    "bold": "\033[1m",
}


def format_text_report(findings, use_color):
    """
    Formats findings as human-readable text lines.

    Args:
        findings (list[dict]): All findings to report.
        use_color (bool): Whether to emit ANSI color codes.

    Returns:
        str: Formatted multi-line report.
    """

    if not findings:
        return ""

    def c(name, text):
        if use_color and name in COLORS:
            return f"{COLORS[name]}{text}{COLORS['reset']}"
        return text

    lines = []
    # Group by file so reports read top-down.
    by_file = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)

    for file_path, items in by_file.items():
        lines.append(c("bold", file_path))
        for f in items:
            sev = c(f["severity"], f["severity"].upper())
            rule = c("dim", f"[{f['rule_id']}]")
            path = c("dim", f["json_path"] or "<root>")
            lines.append(f"  {sev} {rule} {path}")
            lines.append(f"      match: \"{f['match']}\"")
            lines.append(c("dim", f"      context: ...{f['snippet']}..."))
            lines.append(c("dim", f"      suggest: {f['suggest']}"))
        lines.append("")
    return "\n".join(lines)


def format_json_report(findings):
    """
    Formats findings as a JSON document for programmatic consumption.

    Args:
        findings (list[dict]): All findings.

    Returns:
        str: JSON-serialized report.
    """

    return json.dumps({"findings": findings, "count": len(findings)}, indent=2)


def summarize(findings):
    """
    Returns a one-line summary by severity for the final status line.

    Args:
        findings (list[dict]): All findings.

    Returns:
        str: Summary like "0 high, 3 medium, 0 low".
    """

    from collections import Counter
    counts = Counter(f["severity"] for f in findings)
    parts = []
    for sev in ["high", "medium", "low"]:
        n = counts.get(sev, 0)
        parts.append(f"{n} {sev}")
    return ", ".join(parts)


# ========================================================================
#   CLI
# ========================================================================

def main(argv=None):
    """
    Entry point. Parses args, runs the linter, prints a report, and
    exits with a status reflecting whether violations were found.

    Args:
        argv (list[str], optional): Argument vector. Defaults to sys.argv[1:].

    Returns:
        int: Exit code (0 = clean, 1 = violations, 2 = invocation error).
    """

    parser = argparse.ArgumentParser(
        description=(
            "Lint Auditmaton: Ads audit JSON content against the Annielytics "
            "writing rules. See annielytics-writing-rules.md for the full rule set."
        ),
    )
    parser.add_argument(
        "targets",
        nargs="+",
        help="Files or directories to lint.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply safe mechanical auto-fixes in place (em-dash/en-dash NOT auto-fixed).",
    )
    parser.add_argument(
        "--severity",
        choices=["high", "medium", "low"],
        default="medium",
        help="Minimum severity to report and to fail on (default: medium).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Report format.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color codes.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the per-file report; show only the summary.",
    )
    args = parser.parse_args(argv)

    files = collect_files(args.targets)
    if not files:
        print("No JSON files found at the given paths.", file=sys.stderr)
        return 2

    # Optional auto-fix pass before linting.
    if args.fix:
        total_fixes = 0
        for f in files:
            fixes = apply_autofixes(f, RULES)
            total_fixes += len(fixes)
            for path, rule_id in fixes:
                print(f"fixed {f}:{path} ({rule_id})")
        if total_fixes:
            print(f"\nApplied {total_fixes} auto-fix(es). Re-running lint...\n")

    # Lint pass.
    threshold = SEVERITY_LEVELS[args.severity]
    all_findings = []
    for f in files:
        for finding in lint_file(f, RULES):
            if SEVERITY_LEVELS[finding["severity"]] >= threshold:
                all_findings.append(finding)

    use_color = (not args.no_color) and sys.stdout.isatty()

    if args.format == "json":
        print(format_json_report(all_findings))
    elif not args.quiet:
        report = format_text_report(all_findings, use_color)
        if report:
            print(report)

    summary = summarize(all_findings)
    status = "CLEAN" if not all_findings else "VIOLATIONS"
    print(
        f"[lint-editorial] {status} — {len(files)} file(s) scanned, "
        f"{len(all_findings)} finding(s): {summary}",
        file=sys.stderr,
    )

    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
