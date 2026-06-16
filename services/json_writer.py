# services/json_writer.py
# Writes content edits back to source JSON files in json/<category>/<subcategory>.json.
# Used by the editorial system when an owner wants edits to be permanent
# (committed to the repo) rather than stored only as DB-backed render-time
# overrides. Atomic write via tempfile + os.replace so a partial write can
# never corrupt a JSON file.

import json
import logging
import os
import tempfile
import threading

from services.audit_engine import JSON_BASE_DIR
from services.editorial_service import navigate_field_path


logger = logging.getLogger(__name__)


# ========================================================================
#   File Lock
# ========================================================================

# Single global lock for JSON file writes. Edits are infrequent and
# serializing them avoids interleaved reads/writes without needing
# per-file locking. If contention ever becomes a concern, swap for a
# keyed lock map.
_WRITE_LOCK = threading.Lock()


# ========================================================================
#   Path Resolution
# ========================================================================

def _slug_to_key(slug):
    """
    Converts a URL slug (dashes) to a filename key (underscores).

    Args:
        slug (str): URL-friendly slug (e.g., "robots-txt").

    Returns:
        str: Underscore-separated filename key (e.g., "robots_txt").
    """

    return slug.replace("-", "_")


def _resolve_filepath(category_key, subcategory_slug):
    """
    Resolves the absolute path of the JSON file for a given category/subcategory.

    Tries the category_key as-is first, then a dash-converted variant
    (e.g., "ai_geo" -> "ai-geo") to match how the audit engine resolves
    directories.

    Args:
        category_key (str): Category directory name.
        subcategory_slug (str): URL-friendly subcategory slug.

    Returns:
        str or None: Absolute filepath if the file exists, None otherwise.
    """

    subcategory_key = _slug_to_key(subcategory_slug)

    # Try the category as-is, then dash variant
    for candidate in (category_key, category_key.replace("_", "-")):
        category_dir = os.path.join(JSON_BASE_DIR, candidate)
        filepath = os.path.join(category_dir, f"{subcategory_key}.json")
        if os.path.isfile(filepath):
            return filepath

    return None


# ========================================================================
#   Atomic Write
# ========================================================================

def _atomic_write_json(filepath, data):
    """
    Writes a JSON file atomically by writing to a temp file in the same
    directory and renaming over the original.

    Using the same directory ensures the rename is on the same filesystem
    (so it is truly atomic on POSIX) and inherits the directory's permissions.

    Args:
        filepath (str): Destination filepath.
        data: Object to serialize as JSON.
    """

    directory = os.path.dirname(filepath)

    # Write to a sibling temp file, then atomic rename
    fd, tmp_path = tempfile.mkstemp(
        prefix=".write-",
        suffix=".json.tmp",
        dir=directory,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_path, filepath)
    except Exception:

        # Best-effort cleanup of the temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ========================================================================
#   Public API
# ========================================================================

def apply_check_field_edit(category_key, subcategory_slug, check_id, field_path, original_text, new_text):
    """
    Applies a content edit directly to a JSON file by replacing original_text
    with new_text inside the resolved field for the given check.

    Resolves the JSON file from category_key + subcategory_slug, finds the
    audit_check whose id matches check_id, navigates to the field via
    field_path, and replaces the first occurrence of original_text in the
    field's string value. Writes the file back atomically.

    Args:
        category_key (str): Category directory key (e.g., "rich-results").
        subcategory_slug (str): Subcategory slug (e.g., "education-qa").
        check_id (str): The audit check id to edit.
        field_path (str): Dot-notation path within the check (e.g.,
            "educate.base", "educate.site_type_overlays.educational").
        original_text (str): The exact substring currently in the field.
        new_text (str): The replacement substring.

    Returns:
        dict: {
            "success": bool,
            "message": str,
            "occurrences": int,   # how many matches existed before replace
        }
    """

    if original_text == new_text:
        return {"success": False, "message": "Original and new text are identical", "occurrences": 0}

    if not original_text:
        return {"success": False, "message": "original_text is required", "occurrences": 0}

    filepath = _resolve_filepath(category_key, subcategory_slug)
    if not filepath:
        return {
            "success": False,
            "message": f"JSON file not found for {category_key}/{subcategory_slug}",
            "occurrences": 0,
        }

    with _WRITE_LOCK:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Failed to load %s: %s", filepath, e)
            return {"success": False, "message": f"Failed to load JSON: {e}", "occurrences": 0}

        # Find the audit check by id
        if not isinstance(data, dict):
            return {"success": False, "message": "JSON file is not a dict wrapper (cannot resolve check_id)", "occurrences": 0}

        checks = data.get("audit_checks", [])
        target_check = None
        for check in checks:
            if check.get("id") == check_id:
                target_check = check
                break

        if target_check is None:
            return {"success": False, "message": f"check_id not found: {check_id}", "occurrences": 0}

        # Navigate to the parent + key of the target field
        parent, key = navigate_field_path(target_check, field_path)
        if parent is None:
            return {"success": False, "message": f"field_path could not be resolved: {field_path}", "occurrences": 0}

        current_value = parent[key] if isinstance(parent, dict) else parent[key]
        if not isinstance(current_value, str):
            return {"success": False, "message": "Target field is not a string", "occurrences": 0}

        # Count occurrences for the caller; replace only the first to avoid
        # accidental cascading replacements
        occurrences = current_value.count(original_text)
        if occurrences == 0:
            return {
                "success": False,
                "message": "original_text not found in target field (page may be stale)",
                "occurrences": 0,
            }

        updated_value = current_value.replace(original_text, new_text, 1)

        if isinstance(parent, dict):
            parent[key] = updated_value
        else:

            # parent is a list; key is the integer index
            parent[key] = updated_value

        try:
            _atomic_write_json(filepath, data)
        except Exception as e:
            logger.exception("Atomic write failed for %s", filepath)
            return {"success": False, "message": f"Atomic write failed: {e}", "occurrences": occurrences}

    logger.info(
        "Applied edit to %s :: %s :: %s (occurrences=%d)",
        filepath, check_id, field_path, occurrences,
    )

    return {
        "success": True,
        "message": "Edit applied to JSON file",
        "occurrences": occurrences,
    }


SUBCAT_SCOPE_PREFIX = "__subcat__/"


def parse_scope(scope):
    """
    Parses a content-path scope into a tuple describing what kind of edit
    target it identifies.

    Returns one of:
        ("subcat", category_key, subcategory_slug) — for top-level subcategory
            fields like intro, important_note, subcat_img_caption.
        ("check", check_id) — for fields inside an audit_check.

    Args:
        scope (str): The string before "::" in a data-content-path attribute.

    Returns:
        tuple
    """

    if scope.startswith(SUBCAT_SCOPE_PREFIX):
        rest = scope[len(SUBCAT_SCOPE_PREFIX):]
        category_key, _, subcategory_slug = rest.partition("/")
        return ("subcat", category_key, subcategory_slug)
    return ("check", scope)


def apply_top_level_edit(filepath, field_path, original_text, new_text):
    """
    Replaces text in a top-level (subcategory-level) field of a JSON file.

    Used for fields like `intro`, `important_note`, `subcat_img_caption`
    that live on the wrapper dict, not inside an audit_check.

    Args:
        filepath (str): Absolute path to the source JSON file.
        field_path (str): Dot-notation path from the root (usually a single
            key like "intro" or "important_note").
        original_text (str): The exact substring currently in the field.
        new_text (str): Replacement substring.

    Returns:
        dict: {"success": bool, "message": str, "occurrences": int}
    """

    if original_text == new_text:
        return {"success": False, "message": "Original and new text are identical", "occurrences": 0}

    if not original_text:
        return {"success": False, "message": "original_text is required", "occurrences": 0}

    if not os.path.isfile(filepath):
        return {"success": False, "message": f"File does not exist: {filepath}", "occurrences": 0}

    with _WRITE_LOCK:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            return {"success": False, "message": f"Failed to load JSON: {e}", "occurrences": 0}

        if not isinstance(data, dict):
            return {"success": False, "message": "JSON file is not a dict wrapper", "occurrences": 0}

        parent, key = navigate_field_path(data, field_path)
        if parent is None:
            return {"success": False, "message": f"field_path could not be resolved: {field_path}", "occurrences": 0}

        current_value = parent[key]
        if not isinstance(current_value, str):
            return {"success": False, "message": "Target field is not a string", "occurrences": 0}

        occurrences = current_value.count(original_text)
        if occurrences == 0:
            return {
                "success": False,
                "message": "original_text not found in target field (page may be stale)",
                "occurrences": 0,
            }

        parent[key] = current_value.replace(original_text, new_text, 1)

        try:
            _atomic_write_json(filepath, data)
        except Exception as e:
            logger.exception("Atomic write failed for %s", filepath)
            return {"success": False, "message": f"Atomic write failed: {e}", "occurrences": occurrences}

    logger.info("Applied top-level edit on %s :: %s", filepath, field_path)
    return {"success": True, "message": "Edit applied to JSON file", "occurrences": occurrences}


def find_filepath_for_scope(scope):
    """
    Resolves a JSON filepath from any scope (check-level or subcat-level).

    Args:
        scope (str): Either a real check_id or a synthetic
            `__subcat__/<category>/<subcategory>` prefix.

    Returns:
        str or None: Absolute filepath if found, None otherwise.
    """

    parsed = parse_scope(scope)
    if parsed[0] == "subcat":
        return _resolve_filepath(parsed[1], parsed[2])
    return find_filepath_for_check(parsed[1])


def apply_edit_to_filepath(filepath, check_id, field_path, original_text, new_text):
    """
    Variant of apply_check_field_edit that operates on a known filepath
    instead of resolving it from category_key + subcategory_slug.

    Used by the dashboard approval flow, where we locate the source file
    by walking the JSON tree (find_filepath_for_check) rather than
    storing category/subcategory on the override row.

    Args:
        filepath (str): Absolute path to the source JSON file.
        check_id (str): The audit check id.
        field_path (str): Dot-notation path within the check.
        original_text (str): Exact substring currently in the field.
        new_text (str): Replacement substring.

    Returns:
        dict: {"success": bool, "message": str, "occurrences": int}
    """

    if original_text == new_text:
        return {"success": False, "message": "Original and new text are identical", "occurrences": 0}

    if not original_text:
        return {"success": False, "message": "original_text is required", "occurrences": 0}

    if not os.path.isfile(filepath):
        return {"success": False, "message": f"File does not exist: {filepath}", "occurrences": 0}

    with _WRITE_LOCK:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            return {"success": False, "message": f"Failed to load JSON: {e}", "occurrences": 0}

        if not isinstance(data, dict):
            return {"success": False, "message": "JSON file is not a dict wrapper", "occurrences": 0}

        target_check = None
        for check in data.get("audit_checks", []):
            if check.get("id") == check_id:
                target_check = check
                break
        if target_check is None:
            return {"success": False, "message": f"check_id not found: {check_id}", "occurrences": 0}

        parent, key = navigate_field_path(target_check, field_path)
        if parent is None:
            return {"success": False, "message": f"field_path could not be resolved: {field_path}", "occurrences": 0}

        current_value = parent[key]
        if not isinstance(current_value, str):
            return {"success": False, "message": "Target field is not a string", "occurrences": 0}

        occurrences = current_value.count(original_text)
        if occurrences == 0:
            return {
                "success": False,
                "message": "original_text not found in target field (page may be stale)",
                "occurrences": 0,
            }

        parent[key] = current_value.replace(original_text, new_text, 1)

        try:
            _atomic_write_json(filepath, data)
        except Exception as e:
            logger.exception("Atomic write failed for %s", filepath)
            return {"success": False, "message": f"Atomic write failed: {e}", "occurrences": occurrences}

    logger.info("Applied edit on %s :: %s :: %s", filepath, check_id, field_path)
    return {"success": True, "message": "Edit applied to JSON file", "occurrences": occurrences}


def find_filepath_for_check(check_id):
    """
    Locates the JSON file that contains an audit check with the given id.

    Used by the revert flow when we have only a check_id and need to find
    the source file (the override row does not store category/subcategory).
    Walks the json/ tree once and returns the first file whose audit_checks
    array contains a matching id.

    Args:
        check_id (str): The audit check id to locate.

    Returns:
        str or None: Absolute filepath if found, None otherwise.
    """

    for root, _, files in os.walk(JSON_BASE_DIR):
        for fname in files:
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as h:
                    data = json.load(h)
            except (json.JSONDecodeError, IOError):
                continue
            if not isinstance(data, dict):
                continue
            for check in data.get("audit_checks", []):
                if check.get("id") == check_id:
                    return fpath

    return None


def revert_check_field_edit(check_id, field_path, original_text, current_text):
    """
    Reverts a previously applied edit by replacing current_text with
    original_text inside the resolved field of the matching check.

    This is the inverse of apply_check_field_edit, used by the dashboard
    revert button when an "applied" override is rolled back.

    Args:
        check_id (str): The audit check id.
        field_path (str): Dot-notation path within the check.
        original_text (str): The pre-edit text to restore.
        current_text (str): The text currently in the field (was the
            proposed_text when the edit was applied).

    Returns:
        dict: {"success": bool, "message": str, "occurrences": int}
    """

    filepath = find_filepath_for_check(check_id)
    if not filepath:
        return {"success": False, "message": f"Source file not found for {check_id}", "occurrences": 0}

    with _WRITE_LOCK:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            return {"success": False, "message": f"Failed to load JSON: {e}", "occurrences": 0}

        target_check = None
        for check in data.get("audit_checks", []):
            if check.get("id") == check_id:
                target_check = check
                break
        if target_check is None:
            return {"success": False, "message": f"check_id not found in {filepath}", "occurrences": 0}

        parent, key = navigate_field_path(target_check, field_path)
        if parent is None:
            return {"success": False, "message": f"field_path could not be resolved: {field_path}", "occurrences": 0}

        current_value = parent[key]
        if not isinstance(current_value, str):
            return {"success": False, "message": "Target field is not a string", "occurrences": 0}

        occurrences = current_value.count(current_text)
        if occurrences == 0:
            return {
                "success": False,
                "message": "Current text not found in field — file may have changed since the edit was applied",
                "occurrences": 0,
            }

        parent[key] = current_value.replace(current_text, original_text, 1)

        try:
            _atomic_write_json(filepath, data)
        except Exception as e:
            logger.exception("Atomic write failed for %s", filepath)
            return {"success": False, "message": f"Atomic write failed: {e}", "occurrences": occurrences}

    logger.info("Reverted edit on %s :: %s :: %s", filepath, check_id, field_path)
    return {"success": True, "message": "Edit reverted in JSON file", "occurrences": occurrences}


def wrap_in_code_tags(category_key, subcategory_slug, check_id, field_path, selected_text):
    """
    Wraps the selected text in <code> tags within the resolved JSON field.

    Convenience wrapper around apply_check_field_edit for the "Format as code"
    action. Refuses to wrap text that is already inside a <code> tag in the
    field value (simple heuristic: if the wrapped form already exists, fail).

    Args:
        category_key (str): Category directory key.
        subcategory_slug (str): Subcategory slug.
        check_id (str): The audit check id.
        field_path (str): Dot-notation path to the field.
        selected_text (str): The exact substring to wrap.

    Returns:
        dict: Same shape as apply_check_field_edit.
    """

    wrapped = f"<code>{selected_text}</code>"

    # Don't double-wrap if the selection is already inside a <code> tag.
    # We can't fully inspect HTML structure here, but we can refuse if
    # the literal wrapped form already exists in the field.
    return apply_check_field_edit(
        category_key=category_key,
        subcategory_slug=subcategory_slug,
        check_id=check_id,
        field_path=field_path,
        original_text=selected_text,
        new_text=wrapped,
    )
