#!/usr/bin/env python3
"""
scripts/extract_revisions_from_diff.py

Builds revision-log entries from a git diff between the working tree and
a baseline ref (default: main). Used to backfill the editorial-revisions
log when content was edited outside the `append_revision()` flow — e.g.,
a bulk Python script that rewrote many files, or a sub-agent that
forgot to log.

Produces the same schema as `append_revision()`. Entries created by this
script have `source: "extract"` so the dashboard can distinguish them
from `source: "append"` entries written at edit time.

Sentence-level extraction: each changed field is split at `<br><br>`,
`</li>`, `</p>` boundaries, then diffed sentence-by-sentence so each
record is one localized change rather than a whole-field replacement.

Usage:
    python3 scripts/extract_revisions_from_diff.py                # against main
    python3 scripts/extract_revisions_from_diff.py origin/main    # any baseline
    python3 scripts/extract_revisions_from_diff.py --merge        # merge with existing append-source records

Without --merge, the existing log is overwritten with extract-only
records. With --merge, the script preserves existing append-source
records and dedupes against (file_path, json_path, before_text) so
re-running is idempotent.
"""

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from services.revision_log import (
    REVISIONS_PATH,
    RULE_LABELS,
    classify_revision,
    _file_stem_to_slug,
    _json_path_to_field,
    _resolve_check_title,
    _check_to_step,
)


# ========================================================================
#   Git diff plumbing
# ========================================================================

def list_changed_files(baseline):
    """
    Returns the list of JSON files under json/ that differ between
    `baseline` and the working tree.

    Args:
        baseline (str): Git ref to diff against (e.g., "main").

    Returns:
        list[str]: Paths relative to the repo root.
    """

    out = subprocess.check_output(
        ["git", "diff", "--name-only", baseline, "--", "json/"],
        cwd=REPO_ROOT,
        text=True,
    )
    return [line for line in out.splitlines() if line.endswith(".json")]


def file_content_at(ref, path):
    """
    Returns the file content at the given git ref, or None if the file
    doesn't exist at that ref.

    Args:
        ref (str): Git ref to read from.
        path (str): Path relative to the repo root.

    Returns:
        str or None: File content as text, or None if missing.
    """

    try:
        return subprocess.check_output(
            ["git", "show", f"{ref}:{path}"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None


# ========================================================================
#   JSON walk + sentence-level diff
# ========================================================================

SENTENCE_BOUNDARIES = re.compile(r"<br\s*/?>\s*<br\s*/?>\s*|</li>|</p>|(?<=[.!?])\s+(?=[A-Z])")


def walk_text_fields(obj, path=""):
    """
    Yields (json_path, text) for every string in the parsed JSON object.

    Args:
        obj: A parsed JSON value.
        path (str): The accumulated dot-notation path.

    Yields:
        tuple[str, str]: (json_path, text).
    """

    if isinstance(obj, dict):
        for k, v in obj.items():
            child_path = f"{path}.{k}" if path else k
            yield from walk_text_fields(v, child_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from walk_text_fields(item, f"{path}[{i}]")
    elif isinstance(obj, str):
        if obj.strip():
            yield path, obj


def split_sentences(text):
    """
    Splits a prose string at sentence boundaries. Honors HTML break tags
    (<br><br>, </li>, </p>) and standard sentence-ending punctuation
    followed by a capitalized continuation.

    Args:
        text (str): Prose text to split.

    Returns:
        list[str]: Non-empty sentence-level chunks.
    """

    chunks = [s.strip() for s in SENTENCE_BOUNDARIES.split(text) if s and s.strip()]
    return chunks


def diff_sentences(before_text, after_text):
    """
    Returns sentence pairs (before, after) for sentences that changed.
    Uses a simple set-based diff: sentences in before but not after are
    paired with sentences in after but not before by position, falling
    back to a single full-field diff if positional alignment fails.

    Args:
        before_text (str): Original field content.
        after_text (str): New field content.

    Returns:
        list[tuple[str, str]]: (before_snippet, after_snippet) pairs.
    """

    before_sents = split_sentences(before_text)
    after_sents = split_sentences(after_text)

    before_set = set(before_sents)
    after_set = set(after_sents)

    removed = [s for s in before_sents if s not in after_set]
    added = [s for s in after_sents if s not in before_set]

    # Pair removed/added positionally. If counts mismatch, fall back to
    # one big diff so we don't drop changes.
    if not removed and not added:
        return []
    if len(removed) == len(added):
        return list(zip(removed, added))
    if not added:
        return [(r, "") for r in removed]
    if not removed:
        return [("", a) for a in added]
    # Mismatch — emit one whole-field record.
    return [(before_text, after_text)]


# ========================================================================
#   Severity heuristic
# ========================================================================

HIGH_SIGNALS = (
    "—", "–", "isn't just", "not just", "it's important to note",
    "this matters because", "quietly", "silently", "comprehensive",
    "robust", "powerful", "intuitive", "seamless", "leverag", "unlock",
    "ecosystem", "transformative", "revolutionary", "holistic",
)

MEDIUM_SIGNALS = (
    ", because ", ", since ", " over ", "e.g. ", "i.e. ", ": ", "'",
)


def heuristic_severity(before_text):
    """
    Picks a severity for an extracted record by looking for high-signal
    or medium-signal phrases in the before text.

    Args:
        before_text (str): The text that was replaced.

    Returns:
        str: "high", "medium", or "low".
    """

    bt = before_text.lower()
    if any(sig.lower() in bt for sig in HIGH_SIGNALS):
        return "high"
    if any(sig in bt for sig in MEDIUM_SIGNALS):
        return "medium"
    return "low"


# ========================================================================
#   Extract entry point
# ========================================================================

def extract_revisions(baseline):
    """
    Walks every changed JSON file, diffs at the sentence level, and
    builds revision records.

    Args:
        baseline (str): Git ref to diff against.

    Returns:
        list[dict]: Revision records in the unified schema.
    """

    changed = list_changed_files(baseline)
    print(f"changed files: {len(changed)}", file=sys.stderr)

    now = datetime.now(timezone.utc)
    records = []

    for path in changed:
        before_raw = file_content_at(baseline, path)
        after_raw = (REPO_ROOT / path).read_text(encoding="utf-8")
        if before_raw is None:
            # File is new in working tree — skip; no before to diff.
            continue
        try:
            before_data = json.loads(before_raw)
            after_data = json.loads(after_raw)
        except json.JSONDecodeError:
            continue

        before_fields = dict(walk_text_fields(before_data))
        after_fields = dict(walk_text_fields(after_data))

        for json_path, after_text in after_fields.items():
            before_text = before_fields.get(json_path)
            if before_text is None or before_text == after_text:
                continue

            pairs = diff_sentences(before_text, after_text)
            for bt, at in pairs:
                # Derive check_id from the json_path. If the path starts
                # with audit_checks[N], extract the check's id from the
                # parsed JSON. Otherwise use the file stem.
                m = re.match(r"audit_checks\[(\d+)\]", json_path)
                if m:
                    idx = int(m.group(1))
                    check = after_data.get("audit_checks", [])[idx] \
                        if idx < len(after_data.get("audit_checks", [])) else {}
                    check_id = check.get("id") or check.get("check_id") or ""
                else:
                    check_id = _file_stem_to_slug(Path(path).stem)

                # Derive category from the path: json/<category>/<file>.json
                parts = Path(path).parts
                category = parts[1] if len(parts) >= 3 else ""
                subcategory = _file_stem_to_slug(Path(path).stem)

                step = _check_to_step(json_path)
                rule_category = classify_revision(bt, at)
                records.append({
                    "id": str(uuid.uuid4()),
                    "revised_at": now.isoformat(),
                    "revision_date": now.strftime("%Y-%m-%d"),
                    "source": "extract",
                    "file_path": path,
                    "category": category,
                    "subcategory": subcategory,
                    "check_id": check_id,
                    "check_title": _resolve_check_title(path, check_id),
                    "json_path": json_path,
                    "field": _json_path_to_field(json_path),
                    "step": step,
                    "url": f"/dashboard/{category}/{subcategory}/{check_id}/{step}/",
                    "before_text": bt,
                    "after_text": at,
                    "severity": heuristic_severity(bt),
                    "rule_category": rule_category,
                    "rule_label": RULE_LABELS.get(rule_category, rule_category),
                })

    return records


# ========================================================================
#   CLI
# ========================================================================

def main(argv=None):
    """
    Entry point. Diffs against the baseline ref, builds extract records,
    optionally merges with existing append-source records, and writes
    the unified revisions JSON.

    Args:
        argv (list[str], optional): Argument vector.

    Returns:
        int: Exit code.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", nargs="?", default="main",
                        help="Git ref to diff against (default: main).")
    parser.add_argument("--merge", action="store_true",
                        help="Preserve existing append-source records "
                             "instead of overwriting with extract-only.")
    args = parser.parse_args(argv)

    new_records = extract_revisions(args.baseline)
    print(f"extracted {len(new_records)} revision records", file=sys.stderr)

    if args.merge and REVISIONS_PATH.exists():
        with open(REVISIONS_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f).get("revisions", [])
        append_records = [r for r in existing if r.get("source") == "append"]
        # Dedupe extract records against append records by
        # (file_path, json_path, before_text). Append takes precedence.
        append_keys = {
            (r.get("file_path"), r.get("json_path"), r.get("before_text"))
            for r in append_records
        }
        new_records = [
            r for r in new_records
            if (r["file_path"], r["json_path"], r["before_text"]) not in append_keys
        ]
        merged = append_records + new_records
        print(
            f"merged: {len(append_records)} append + {len(new_records)} extract = {len(merged)}",
            file=sys.stderr,
        )
    else:
        merged = new_records

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "generated_at": now,
        "baseline_ref": args.baseline,
        "revision_count": len(merged),
        "file_count": len({r.get("file_path") for r in merged}),
        "revisions": merged,
    }
    REVISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REVISIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"wrote {REVISIONS_PATH} ({len(merged)} records)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
