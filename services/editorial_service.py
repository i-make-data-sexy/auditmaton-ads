# services/editorial_service.py
# Business logic for the editorial overlay system. Handles CRUD operations
# for content overrides (edit proposals with approval workflow) and
# text-anchored comments. Routes stay thin — all heavy lifting lives here.

import logging
import re
from datetime import datetime, timezone

from zoneinfo import ZoneInfo

from extensions import db
from models.editorial import ContentOverride, ContentComment, CommentReply


logger = logging.getLogger(__name__)

# Eastern timezone for display formatting
EASTERN = ZoneInfo("America/New_York")


def _format_eastern(dt):
    """
    Converts a UTC datetime to an Eastern time display string.

    Args:
        dt (datetime): A timezone-aware UTC datetime.

    Returns:
        str or None: Formatted string like "3/7/2026 10:30 AM",
            or None if dt is None.
    """

    if not dt:
        return None

    eastern_dt = dt.astimezone(EASTERN)
    return eastern_dt.strftime("%-m/%-d/%Y %-I:%M %p")


# ========================================================================
#   Content Override CRUD
# ========================================================================

def create_override(check_id, field_path, original_text, proposed_text, proposed_by_id, scope="global", audit_id=None, source_url=None):
    """
    Creates a new content override proposal.

    Args:
        check_id (str): The check identifier (e.g., "robots-txt-non-200").
        field_path (str): Dot-notation path to the JSON field
            (e.g., "educate.base", "learn_more[0].source_url").
        original_text (str): Snapshot of the original text at proposal time.
        proposed_text (str): The proposed replacement text.
        proposed_by_id (str): UUID of the user proposing the edit.
        scope (str): "global" for all audits, "audit" for one specific audit.
        audit_id (str, optional): Required when scope is "audit".
        source_url (str, optional): The page URL where the edit was proposed.

    Returns:
        ContentOverride: The newly created override object.
    """

    override = ContentOverride(
        check_id=check_id,
        field_path=field_path,
        original_text=original_text,
        proposed_text=proposed_text,
        proposed_by_id=proposed_by_id,
        scope=scope,
        audit_id=audit_id,
        source_url=source_url,
    )

    db.session.add(override)
    db.session.commit()

    logger.info("Override proposed: %s::%s by user %s", check_id, field_path, proposed_by_id)
    return override


def review_override(override_id, status, reviewed_by_id, note=None, proposed_text=None):
    """
    Approves or rejects a content override proposal.

    Args:
        override_id (str): UUID of the override to review.
        status (str): "approved", "rejected", or "pending".
        reviewed_by_id (str): UUID of the reviewing user.
        note (str, optional): Reviewer's note explaining the decision.
        proposed_text (str, optional): Updated proposed text (for edit-then-approve).

    Returns:
        ContentOverride or None: The updated override, or None if not found.
    """

    override = db.session.get(ContentOverride, override_id)
    if not override:
        return None

    override.status = status
    override.reviewed_by_id = reviewed_by_id
    override.review_note = note
    override.reviewed_at = datetime.now(timezone.utc)

    # Update proposed text if the owner edited it before approving
    if proposed_text is not None:
        override.proposed_text = proposed_text

    db.session.commit()

    logger.info("Override %s: %s::%s by user %s", status, override.check_id, override.field_path, reviewed_by_id)
    return override


def get_overrides_for_check(check_id):
    """
    Fetches all content overrides for a given check.

    Returns overrides of any status (pending, approved, rejected)
    so the frontend can show indicators for all states.

    Args:
        check_id (str): The check identifier.

    Returns:
        list[dict]: List of override dicts with all fields serialized.
    """

    overrides = ContentOverride.query.filter_by(check_id=check_id).order_by(
        ContentOverride.proposed_at.desc()
    ).all()

    return [_serialize_override(o) for o in overrides]


def get_pending_overrides():
    """
    Fetches all pending override proposals for the approval dashboard.

    Returns:
        list[dict]: List of pending override dicts ordered by proposal date.
    """

    overrides = ContentOverride.query.filter_by(status="pending").order_by(
        ContentOverride.proposed_at.desc()
    ).all()

    return [_serialize_override(o) for o in overrides]


def get_all_overrides():
    """
    Fetches all override proposals regardless of status.

    Returns:
        list[dict]: List of override dicts ordered by proposal date (newest first).
    """

    overrides = ContentOverride.query.order_by(
        ContentOverride.proposed_at.desc()
    ).all()

    return [_serialize_override(o) for o in overrides]


def get_approved_overrides_for_check(check_id):
    """
    Fetches only approved overrides for a check, used by the render pipeline.

    Args:
        check_id (str): The check identifier.

    Returns:
        list[ContentOverride]: List of approved ContentOverride objects.
    """

    return ContentOverride.query.filter_by(
        check_id=check_id,
        status="approved",
    ).all()


def _serialize_override(override):
    """
    Converts a ContentOverride object to a JSON-serializable dict.

    Args:
        override (ContentOverride): The override to serialize.

    Returns:
        dict: Serialized override data.
    """

    return {
        "id": override.id,
        "check_id": override.check_id,
        "field_path": override.field_path,
        "original_text": override.original_text,
        "proposed_text": override.proposed_text,
        "status": override.status,
        "scope": override.scope,
        "proposed_by": {
            "id": override.proposed_by.id,
            "first_name": override.proposed_by.first_name,
            "last_name": override.proposed_by.last_name,
            "email": override.proposed_by.email,
        } if override.proposed_by else None,
        "reviewed_by": {
            "id": override.reviewed_by.id,
            "first_name": override.reviewed_by.first_name,
            "last_name": override.reviewed_by.last_name,
        } if override.reviewed_by else None,
        "review_note": override.review_note,
        "source_url": override.source_url,
        "proposed_at": override.proposed_at.isoformat() if override.proposed_at else None,
        "proposed_at_display": _format_eastern(override.proposed_at),
        "reviewed_at": override.reviewed_at.isoformat() if override.reviewed_at else None,
        "reviewed_at_display": _format_eastern(override.reviewed_at),
    }


# ========================================================================
#   Content Comment CRUD
# ========================================================================

def create_comment(audit_id, check_id, content_path, anchor_data, comment_text, author_id, source_url=None):
    """
    Creates a new text-anchored comment.

    Args:
        audit_id (str or None): UUID of the audit session, or None if no session exists.
        check_id (str): The check identifier.
        content_path (str): The data-content-path value identifying the field.
        anchor_data (dict): Text anchoring data with keys:
            - exact (str): The exact selected text.
            - prefix (str): ~30 characters before the selection.
            - suffix (str): ~30 characters after the selection.
            - start_offset (int): Character offset start (fallback).
            - end_offset (int): Character offset end (fallback).
        comment_text (str): The comment body.
        author_id (str): UUID of the commenting user.
        source_url (str, optional): The page URL where the comment was made.

    Returns:
        ContentComment: The newly created comment object.
    """

    comment = ContentComment(
        audit_id=audit_id,
        check_id=check_id,
        content_path=content_path,
        anchor_exact=anchor_data.get("exact", ""),
        anchor_prefix=anchor_data.get("prefix"),
        anchor_suffix=anchor_data.get("suffix"),
        anchor_start_offset=anchor_data.get("start_offset"),
        anchor_end_offset=anchor_data.get("end_offset"),
        comment_text=comment_text,
        author_id=author_id,
        source_url=source_url,
    )

    db.session.add(comment)
    db.session.commit()

    logger.info("Comment created on %s::%s by user %s", check_id, content_path, author_id)
    return comment


def get_all_comments(resolved=False):
    """
    Fetches all comments, optionally filtering by resolved status.

    Args:
        resolved (bool): If False, returns only unresolved comments.
            If True, returns only resolved comments.

    Returns:
        list[dict]: List of comment dicts ordered by creation date (newest first).
    """

    comments = ContentComment.query.filter_by(resolved=resolved).order_by(
        ContentComment.created_at.desc()
    ).all()

    return [_serialize_comment(c) for c in comments]


def get_comments_for_check(audit_id, check_id):
    """
    Fetches all comments for a check, including replies.

    Args:
        audit_id (str or None): UUID of the audit session, or None to fetch all.
        check_id (str): The check identifier.

    Returns:
        list[dict]: List of comment dicts with nested replies.
    """

    # Filter by check_id; include audit_id filter only if provided
    query = ContentComment.query.filter_by(check_id=check_id)
    if audit_id:
        query = query.filter_by(audit_id=audit_id)

    comments = query.order_by(ContentComment.created_at.asc()).all()

    return [_serialize_comment(c) for c in comments]


def create_reply(comment_id, reply_text, author_id):
    """
    Creates a reply on an existing comment.

    Args:
        comment_id (str): UUID of the parent comment.
        reply_text (str): The reply body.
        author_id (str): UUID of the replying user.

    Returns:
        CommentReply or None: The newly created reply, or None if comment not found.
    """

    comment = db.session.get(ContentComment, comment_id)
    if not comment:
        return None

    reply = CommentReply(
        comment_id=comment_id,
        reply_text=reply_text,
        author_id=author_id,
    )

    db.session.add(reply)
    db.session.commit()

    logger.info("Reply added to comment %s by user %s", comment_id, author_id)
    return reply


def resolve_comment(comment_id, resolved_by_id):
    """
    Marks a comment as resolved.

    Args:
        comment_id (str): UUID of the comment to resolve.
        resolved_by_id (str): UUID of the user resolving it.

    Returns:
        ContentComment or None: The updated comment, or None if not found.
    """

    comment = db.session.get(ContentComment, comment_id)
    if not comment:
        return None

    comment.resolved = True
    comment.resolved_by_id = resolved_by_id
    comment.resolved_at = datetime.now(timezone.utc)

    db.session.commit()

    logger.info("Comment %s resolved by user %s", comment_id, resolved_by_id)
    return comment


def _serialize_comment(comment):
    """
    Converts a ContentComment object to a JSON-serializable dict.

    Args:
        comment (ContentComment): The comment to serialize.

    Returns:
        dict: Serialized comment data with nested replies.
    """

    return {
        "id": comment.id,
        "check_id": comment.check_id,
        "content_path": comment.content_path,
        "anchor": {
            "exact": comment.anchor_exact,
            "prefix": comment.anchor_prefix,
            "suffix": comment.anchor_suffix,
            "start_offset": comment.anchor_start_offset,
            "end_offset": comment.anchor_end_offset,
        },
        "comment_text": comment.comment_text,
        "author": {
            "id": comment.author.id,
            "first_name": comment.author.first_name,
            "last_name": comment.author.last_name,
        } if comment.author else None,
        "resolved": comment.resolved,
        "source_url": comment.source_url,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "created_at_display": _format_eastern(comment.created_at),
        "replies": [
            {
                "id": r.id,
                "reply_text": r.reply_text,
                "author": {
                    "id": r.author.id,
                    "first_name": r.author.first_name,
                    "last_name": r.author.last_name,
                } if r.author else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in comment.replies
        ],
    }


# ========================================================================
#   Field Path Navigation
# ========================================================================

# Pattern to match array index notation: "steps[0]" → ("steps", 0)
_ARRAY_INDEX_PATTERN = re.compile(r"^(.+)\[(\d+)\]$")


def navigate_field_path(obj, field_path):
    """
    Navigates a nested dict/list structure using a dot-notation field path.

    Supports array index notation like "learn_more[0].source_url".

    Args:
        obj (dict): The root object to navigate.
        field_path (str): Dot-separated path (e.g., "educate.base",
            "validate.impactful_updates[0].update_summary").

    Returns:
        tuple: (parent_obj, final_key) so the caller can read or write the value.
            Returns (None, None) if the path cannot be resolved.
    """

    parts = field_path.split(".")
    current = obj

    # Navigate to the parent of the final key
    for part in parts[:-1]:

        # Check for array index notation
        match = _ARRAY_INDEX_PATTERN.match(part)
        if match:
            key, index = match.group(1), int(match.group(2))
            if not isinstance(current, dict) or key not in current:
                return None, None
            current = current[key]
            if not isinstance(current, list) or index >= len(current):
                return None, None
            current = current[index]
        else:
            if not isinstance(current, dict) or part not in current:
                return None, None
            current = current[part]

    # Handle the final key
    final_key = parts[-1]
    match = _ARRAY_INDEX_PATTERN.match(final_key)

    if match:

        # Final key is an array access like "steps[2]"
        key, index = match.group(1), int(match.group(2))
        if not isinstance(current, dict) or key not in current:
            return None, None
        arr = current[key]
        if not isinstance(arr, list) or index >= len(arr):
            return None, None
        return arr, index

    return current, final_key
