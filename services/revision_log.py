# services/revision_log.py
# Append-only log of direct JSON content revisions made to enforce
# Annielytics writing rules on audit content. Each entry follows the
# unified editorial-revisions schema described in
# ~/.claude/rules/editorial/editorial-system.md. The log is rendered by the
# /admin/editorial-revisions/ dashboard.

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path


# ========================================================================
#   Paths
# ========================================================================

REVISIONS_PATH = (
    Path(__file__).resolve().parent.parent
    / "editorial"
    / "editorial_revisions.json"
)


# ========================================================================
#   Slug Helpers
# ========================================================================

def _file_stem_to_slug(stem):
    """
    Converts a JSON file stem (underscore form) to a URL slug (dash form).

    Args:
        stem (str): The file name without the .json extension
            (e.g., "ad_density_placement").

    Returns:
        str: The URL-friendly subcategory slug (e.g., "ad-density-placement").
    """

    return stem.replace("_", "-")


def _json_path_to_field(json_path):
    """
    Converts a dot-notation JSON path to a human-readable arrow form for
    the dashboard's `field` column.

    Args:
        json_path (str): Dot-notation path like "audit_checks[1].educate.base".

    Returns:
        str: Arrow-separated form like "audit_checks[1] > educate > base".
    """

    if not json_path:
        return ""
    return json_path.replace(".", " > ")


def _resolve_check_title(file_path, check_id):
    """
    Looks up the human-readable title for a given check_id by reading
    the audit JSON file and matching against its audit_checks array.

    Returns None if the file can't be read, the check_id doesn't appear
    in the file, or the check_id is a subcategory-level slug (in which
    case the file's top-level title or subcategory display name applies
    and the dashboard renders empty).

    Args:
        file_path (str): Path to the audit JSON file, relative to the
            repo root (e.g., "json/ads/ad_density_placement.json").
        check_id (str): The audit check identifier or subcategory slug.

    Returns:
        str or None: The check title if found, otherwise None.
    """

    full_path = Path(__file__).resolve().parent.parent / file_path
    if not full_path.exists():
        return None
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    # audit_check entries use "id" (not "check_id") as the identifier
    # field. Match against both for forward-compatibility.
    for check in data.get("audit_checks", []):
        if check.get("id") == check_id or check.get("check_id") == check_id:
            return check.get("title")

    # If the check_id is the subcategory slug (subcategory-level fields
    # like intro, worth_it_explanation use the file stem), fall back to
    # the subcategory display name.
    if check_id == _file_stem_to_slug(Path(file_path).stem):
        return data.get("display_name") or data.get("subcategory_title")

    return None


# ========================================================================
#   Rule Classifier
# ========================================================================

# Display labels for each rule category. The dashboard renders these as
# pill labels and as filter dropdown options. Order here controls the
# order in the filter dropdown.
RULE_LABELS = {
    # Punctuation
    "em-dash": "Em-dash",
    "en-dash": "En-dash",
    "horizontal-rule": "Horizontal rule",
    "mid-sentence-colon": "Mid-sentence colon",
    "comma-before-because-since": "Comma before because/since",
    "quote-punctuation": "Quote punctuation",
    "quote-choice": "Single vs. double quote",
    # AI tells
    "throat-clearing": "AI throat-clearing",
    "not-just-framing": "Not just X, it's Y",
    "silently-quietly": "Silently / quietly",
    # Marketese (split into category-specific rules)
    "marketese-generic": "Marketese",
    "leverage-verb": "Leverage (verb)",
    "unlock-metaphor": "Unlock (metaphor)",
    "ecosystem-metaphor": "Ecosystem (metaphor)",
    "journey-metaphor": "Journey (metaphor)",
    "artifact-deliverable": "Artifact (deliverable)",
    # Audit-content patterns
    "flag-when-semicolons": "Flag-when semicolons",
    "verify-colon": "Verify colon",
    "keyboard-shortcut-plus": "Keyboard shortcut +",
    "missing-anchor-class": "Missing anchor class",
    # Quantities / examples / lists
    "over-to-more-than": "Over → more than",
    "eg-ie-comma": "e.g. / i.e. comma",
    "fragment-list-intro": "Fragment list intro",
    "long-parenthetical": "Long parenthetical",
    # Semantic rules (review)
    "suggestive-phrasing": "Suggestive phrasing",
    "abbreviation-expansion": "Abbreviation expansion",
    "editorializing": "Editorializing",
    # Catch-alls
    "deleted": "Sentence deleted",
    "other": "Other cleanup",
}

# Generic marketese words. Other ex-marketese words moved to their own
# rule categories (leverage, unlock, ecosystem, journey, artifact).
MARKETESE_WORDS = {
    "seamless", "robust", "cutting-edge", "best-in-class", "comprehensive",
    "world-class", "next-generation", "next-gen", "revolutionary",
    "transformative", "holistic", "powerful", "intuitive", "supercharge",
    "empower", "scalable", "granular",
}

# Word lists for the new category-specific rules. Kept here so the
# classifier and the linter stay aligned.
LEVERAGE_VERB_WORDS = {"leverage", "leverages", "leveraged", "leveraging"}
UNLOCK_WORDS = {"unlock", "unlocks", "unlocked", "unlocking"}
ECOSYSTEM_WORDS = {"ecosystem", "ecosystems"}
JOURNEY_WORDS = {"journey", "journeys"}
ARTIFACT_WORDS = {"artifact", "artifacts"}

# Words / phrasings that flag editorializing about prevalence, detection,
# practitioner behavior, or unsourced superlatives. Used as a fallback
# when no more-specific rule pattern matches. The list is intentionally
# generous because the classifier's "other" bucket should be small.
EDITORIALIZING_HINTS = [
    # Detection / practitioner-failure claims
    "almost never", "easy to miss", "blind spot", "goes unnoticed",
    "without anyone noticing", "without the publisher", "implementation team",
    "nobody reviews", "gives raters nothing", "fail to", "fails to",
    "are vulnerable to", "especially vulnerable", "particularly vulnerable",
    # Prevalence claims
    "rarely", "commonly", "common issue", "common contradiction",
    "common culprit", "common source", "common cause", "common mistake",
    "common reputation", "common failure", "common misconfiguration",
    "common patterns", "common problem", "common error",
    "frequently flagged", "frequently cited", "frequently introduced",
    "frequently caused", "frequently lands", "frequently miss",
    "frequently the largest", "frequently the single", "often introduced",
    "often accidental", "often the largest", "often the single",
    "often the heaviest", "tend to perform better", "tend to outperform",
    "tend to receive little", "are notorious",
    "every site accumulates", "every site", "almost every site",
    "routinely miss", "routinely serves", "routinely",
    "in many cases", "in most cases", "most sites", "most businesses",
    "many businesses", "many sites", "majority of",
    "common after migrations",
    # Unsourced superlatives / records
    "most common", "most damaging", "most overlooked", "most frequently",
    "most impactful", "biggest blind", "biggest source", "biggest cause",
    "biggest contributor", "biggest sources", "single largest",
    "single heaviest", "single most", "the largest source",
    "the leading cause", "single biggest", "single greatest",
    "single most common", "the single",
    # Unsourced stats / "research shows" patterns
    "industry studies suggest", "research shows", "research suggests",
    "studies suggest", "studies have suggested", "studies show",
    "google has stated that", "google recently noted",
    "nearly 85%", "nearly half", "nearly every",
    "30-40% of the time", "majority of the time", "99.9% of the time",
    "50% or more",
    # In-our-experience / set-the-industry framing
    "in our experience", "we've seen", "we have seen",
    "industry standard", "set the industry", "set the bar",
    "represent the most significant", "represents a major",
    "hold a structural advantage", "consistently outperform",
    # Magnitude editorializing
    "measurably collapsed", "tanks click-through", "tanks LCP",
    "dramatically", "significantly more", "severely",
    "wreaks havoc", "crushes", "destroys",
    "the most significant structural shift",
    # Practitioner-attribution claims
    "publishers install them",
    "is inevitable",
    "can serve as an early warning",
    "may foreshadow",
    "signals neglect", "signals to raters", "signals to users",
    "appears anonymous", "appears insincere",
    "automatically appears", "automatically reflects",
    # Sentence-opening editorial frames
    "Ignoring negative", "Without it,", "Without this,",
    "Sites that fail",
    # Competitive-framing prevalence claims
    "competitive disadvantage", "competitive advantage",
    "most frequent offenders", "the most frequent",
    "consistently outrank", "consistently lift",
    "carries disproportionate weight",
    "are the most frequent", "the most attention-grabbing",
    "one of the strongest visual",
    "tend to earn higher", "tend to receive",
    "an early-adoption opportunity",
    "in the highly competitive",
    "significant competitive", "significant traffic",
    "structural advantage",
    # Magnitude framings without sources
    "lose critical visibility", "lose significant traffic",
    "drive significant", "drive high",
    "have a stronger entity",
    "is one of the simplest fixes",
    "is one of the most impactful",
    "is one of the top causes",
    "is the most effective",
    # More prevalence / frequency framings
    "typically have elevated", "will typically have", "are likely to have",
    "consistently increase", "more often than expected",
    "publishers frequently", "frequently use", "never reviewed",
    "more frequent", "frequent offenders",
    "a developer adds", "quality raters note",
    "happens more often",
    "a stronger entity foundation",
]


def _has_word(text, word):
    """
    Returns True if `word` appears as a whole word (case-insensitive)
    in `text`. Underscores and hyphens count as word boundaries so
    hyphenated terms like 'cutting-edge' match cleanly.

    Args:
        text (str): The text to search.
        word (str): The word or hyphenated phrase to look for.

    Returns:
        bool: Whether the word is present as a standalone token.
    """

    if not text or not word:
        return False
    pattern = r"(?<![A-Za-z0-9])" + re.escape(word) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def classify_revision(before_text, after_text):
    """
    Classifies a revision by inspecting the before/after diff and picking
    the most specific writing rule that the edit enforced. Categories are
    checked in priority order; the first match wins.

    Args:
        before_text (str): The original text that was replaced.
        after_text (str): The replacement text (empty string when the
            content was deleted outright).

    Returns:
        str: A rule category key from RULE_LABELS.
    """

    bt = before_text or ""
    at = after_text or ""

    # If the content was deleted entirely, tag it specially so reviewers
    # can find every removed sentence quickly.
    if bt and not at.strip():
        return "deleted"

    # Banned punctuation — most visible AI tells first.
    if "—" in bt and "—" not in at:
        return "em-dash"
    if "–" in bt and "–" not in at:
        return "en-dash"
    if re.search(r"(?m)^---\s*$", bt) and not re.search(r"(?m)^---\s*$", at):
        return "horizontal-rule"

    # Silently / quietly + verb.
    if (
        re.search(r"\b(silently|quietly)\b", bt, re.IGNORECASE)
        and not re.search(r"\b(silently|quietly)\b", at, re.IGNORECASE)
    ):
        return "silently-quietly"

    # Throat-clearing AI framing.
    if re.search(r"it's important to note|this matters because", bt, re.IGNORECASE) \
            and not re.search(r"it's important to note|this matters because", at, re.IGNORECASE):
        return "throat-clearing"

    # "Not just X, it's Y" / "Isn't just X" pattern.
    if re.search(r"isn't just|not just\b.{1,40}\bbut\b", bt, re.IGNORECASE) \
            and not re.search(r"isn't just|not just\b.{1,40}\bbut\b", at, re.IGNORECASE):
        return "not-just-framing"

    # Comma before "because" or "since" introducing a reason clause.
    if re.search(r",\s+(because|since)\b", bt) \
            and not re.search(r",\s+(because|since)\b", at):
        return "comma-before-because-since"

    # "Over <number>" for quantities → "more than".
    if re.search(r"\bover\s+[\d]", bt) and not re.search(r"\bover\s+[\d]", at):
        return "over-to-more-than"

    # "e.g." / "i.e." missing comma after.
    if re.search(r"\b(e\.g\.|i\.e\.)[^,]", bt) \
            and not re.search(r"\b(e\.g\.|i\.e\.)[^,]", at):
        return "eg-ie-comma"

    # "e.g.," / "i.e.," introduced in the after where before had a bare
    # parenthetical list of examples.
    if not re.search(r"\b(e\.g\.|i\.e\.)", bt) \
            and re.search(r"\b(e\.g\.,|i\.e\.,)", at):
        return "eg-ie-comma"

    # Mid-sentence colon before a list/example/question in prose.
    # Heuristic: before has a colon mid-sentence followed by content,
    # after has no such colon at that position. Match both lowercase and
    # uppercase preceding letters (e.g., "for SEO:" → "for SEO.") to
    # catch cases the previous regex missed.
    if re.search(r"[A-Za-z]:\s+\S", bt) and not re.search(r"[A-Za-z]:\s+\S", at):
        return "mid-sentence-colon"

    # Quote punctuation inside the closing single quote (e.g., 'Linear,'
    # corrected to 'Linear', — comma/period/question mark moved outside).
    if re.search(r"[A-Za-z][,.?]'", bt) and not re.search(r"[A-Za-z][,.?]'", at):
        return "quote-punctuation"

    # Single-quoted full sentence/question switched to double quotes.
    if re.search(r"'[^']{20,}\?'", bt) and re.search(r'"[^"]{20,}\?"', at):
        return "quote-choice"

    # Category-specific marketese rules. Check these BEFORE the generic
    # marketese bucket so the dashboard can filter on the more specific
    # category.
    for word in LEVERAGE_VERB_WORDS:
        if _has_word(bt, word) and not _has_word(at, word):
            return "leverage-verb"
    for word in UNLOCK_WORDS:
        if _has_word(bt, word) and not _has_word(at, word):
            return "unlock-metaphor"
    for word in ECOSYSTEM_WORDS:
        if _has_word(bt, word) and not _has_word(at, word):
            return "ecosystem-metaphor"
    for word in JOURNEY_WORDS:
        if _has_word(bt, word) and not _has_word(at, word):
            # Skip when the journey appears as part of a documented
            # product name in the before text.
            if not any(allow.lower() in bt.lower() for allow in [
                "Customer Journey Analytics", "Adobe Journey Optimizer",
                "ObservePoint Journey",
            ]):
                return "journey-metaphor"
    for word in ARTIFACT_WORDS:
        if _has_word(bt, word) and not _has_word(at, word):
            return "artifact-deliverable"

    # Generic marketese — any of the remaining banned words removed from
    # before. Check this AFTER the more-specific rules so a single edit
    # that fixed both gets the more interesting label.
    for word in MARKETESE_WORDS:
        if _has_word(bt, word) and not _has_word(at, word):
            return "marketese-generic"

    # Fragment list intro: short before line ending with a colon, after
    # is a complete sentence.
    if bt.strip().endswith(":") and len(bt.strip()) < 50:
        return "fragment-list-intro"

    # Long parenthetical: a (...) chunk in before with more than 12 words
    # that was restructured or shortened in after.
    bt_parens = re.findall(r"\(([^)]+)\)", bt)
    at_parens = re.findall(r"\(([^)]+)\)", at)
    if any(len(p.split()) > 12 for p in bt_parens) \
            and not any(len(p.split()) > 12 for p in at_parens):
        return "long-parenthetical"

    # Imperative → suggestive phrasing. Catches any directive "should",
    # "must", "need to", or "Ensure" being softened.
    softening_terms = (
        r"may want to|benefit from|benefits from|is worth|are worth|"
        r"is particularly|are particularly|is well-suited|are well-suited|"
        r"is well-served|are well-served|belongs in|belong in|"
        r"can\b|consider\b|considering\b|"
        r"better positioned|positions the|is the cleanest|is the most|"
        r"a reliable way|the most reliable|documenting"
    )
    if re.search(r"\bshould\b|\bmust\b|\bneed to\b|\bEnsure\b", bt) \
            and re.search(softening_terms, at, re.IGNORECASE):
        return "suggestive-phrasing"

    # Reverse direction: "Ensure" hardcoded to "should" — still a softening
    # because "Ensure" is the most directive form and "should" reads as a
    # recommendation.
    if re.search(r"\bEnsure\b", bt) and re.search(r"\bshould\b", at) \
            and not re.search(r"\bEnsure\b", at):
        return "suggestive-phrasing"

    # Abbreviation expansion: after introduces "<expansion> (<abbr>)"
    # patterns that were not present in before. Catches cases where the
    # abbreviation alone appeared in before and the expansion was added.
    abbr_pattern = r"\b((?:[A-Za-z]+\s+){1,5}[A-Za-z]+)\s+\(([A-Z]{2,5})\)"
    after_abbrs = set(re.findall(abbr_pattern, at))
    before_abbrs = set(re.findall(abbr_pattern, bt))
    if after_abbrs - before_abbrs:
        return "abbreviation-expansion"

    # Editorializing fallback: prevalence/detection/practitioner-behavior
    # claims that the edit removed.
    for hint in EDITORIALIZING_HINTS:
        if hint.lower() in bt.lower() and hint.lower() not in at.lower():
            return "editorializing"

    return "other"


def _check_to_step(json_path):
    """
    Infers the active -ate step from a JSON dot path so the revision URL
    deep-links to the correct tab in the canvas.

    Maps any path starting with educate/investigate/generate to its step.
    Falls back to "educate" for top-level paths like intro, worth_it_explanation,
    or important_note that render on the Educate tab.

    Args:
        json_path (str): A dot-notation field path
            (e.g., "educate.base", "investigate.steps[0]", "intro").

    Returns:
        str: One of "educate", "investigate", "generate", or "canvas".
    """

    head = json_path.split(".")[0].split("[")[0]
    if head in {"educate", "investigate", "generate", "canvas"}:
        return head
    return "educate"


# ========================================================================
#   Read
# ========================================================================

def load_revisions():
    """
    Loads all logged revisions from disk.

    Returns:
        list[dict]: Revision entries in the order they were appended.
            Returns an empty list if the file is missing or empty.
    """

    if not REVISIONS_PATH.exists():
        return []

    with open(REVISIONS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("revisions", [])


# ========================================================================
#   Append
# ========================================================================

def append_revision(
    file_path,
    category,
    check_id,
    json_path,
    before_text,
    after_text,
    severity,
    rule_category=None,
):
    """
    Appends a single revision entry to the editorializing revisions log.

    Args:
        file_path (str): Path to the audit JSON file relative to repo root
            (e.g., "json/ads/ad_density_placement.json").
        category (str): Category folder slug (e.g., "ads", "ai-geo").
        check_id (str): The audit check identifier
            (e.g., "ads-content-pushed-below-fold"). Use the subcategory
            file stem when the edit is in a subcategory-level field like
            intro or worth_it_explanation.
        json_path (str): Dot-notation path to the edited field
            (e.g., "educate.site_type_overlays.recipe").
        before_text (str): The exact text that was replaced.
        after_text (str): The new text.
        severity (str): One of "high", "medium", "low".
        rule_category (str, optional): Override the auto-classified rule
            label. Omit to let the classifier inspect before/after text
            and pick the most specific match.

    Returns:
        dict: The revision entry that was appended.
    """

    # Derive the subcategory slug from the file name. JSON files use
    # underscores; URLs use dashes.
    file_stem = Path(file_path).stem
    subcategory = _file_stem_to_slug(file_stem)

    step = _check_to_step(json_path)
    url = f"/dashboard/{category}/{subcategory}/{check_id}/{step}/"

    if rule_category is None:
        rule_category = classify_revision(before_text, after_text)

    now = datetime.now(timezone.utc)

    entry = {
        "id": str(uuid.uuid4()),
        "revised_at": now.isoformat(),
        "revision_date": now.strftime("%Y-%m-%d"),
        "source": "append",
        "file_path": file_path,
        "category": category,
        "subcategory": subcategory,
        "check_id": check_id,
        "check_title": _resolve_check_title(file_path, check_id),
        "json_path": json_path,
        "field": _json_path_to_field(json_path),
        "step": step,
        "url": url,
        "before_text": before_text,
        "after_text": after_text,
        "severity": severity,
        "rule_category": rule_category,
        "rule_label": RULE_LABELS.get(rule_category, rule_category),
    }

    # Load, append, write back. This is not concurrency-safe; revisions
    # are written by sequentially-run agents, not concurrent web requests.
    revisions = load_revisions()
    revisions.append(entry)

    REVISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": now.isoformat(),
        "baseline_ref": None,
        "revision_count": len(revisions),
        "file_count": len({r.get("file_path") for r in revisions}),
        "revisions": revisions,
    }
    with open(REVISIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return entry
