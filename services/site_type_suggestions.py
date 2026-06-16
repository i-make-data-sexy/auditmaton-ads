# services/site_type_suggestions.py
# Stores and loads user-submitted site-type suggestions. When a user picks
# "Other" on the intake form and names a site type they wish existed, the
# suggestion is appended to a JSON log under reports/. The admin hub surfaces
# these so new site types can be added to the intake list over time.

import json
import os
from datetime import datetime, timezone


# ========================================================================
#   Paths
# ========================================================================

SUGGESTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
SUGGESTIONS_FILE = os.path.join(SUGGESTIONS_DIR, "site_type_suggestions.json")


# ========================================================================
#   Read / Write
# ========================================================================

def load_suggestions():
    """
    Loads all stored site-type suggestions.

    Returns:
        list[dict]: Suggestion records, or an empty list if none exist or
            the file is missing or unreadable.
    """

    if not os.path.exists(SUGGESTIONS_FILE):
        return []

    try:
        with open(SUGGESTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def append_suggestion(suggestion, user_email="", audit_name="", platform=""):
    """
    Appends a single site-type suggestion to the JSON log.

    Args:
        suggestion (str): The site type the user typed.
        user_email (str): The submitting user's email, when available.
        audit_name (str): The audit name from the same intake, for context.
        platform (str): The platform slug the audit targets, for context.

    Returns:
        dict: The record that was written.
    """

    os.makedirs(SUGGESTIONS_DIR, exist_ok=True)

    record = {
        "suggestion": suggestion,
        "user_email": user_email,
        "audit_name": audit_name,
        "platform": platform,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    records = load_suggestions()
    records.append(record)

    with open(SUGGESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return record
