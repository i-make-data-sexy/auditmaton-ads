# blueprints/editorial/routes.py
# API endpoints for the editorial overlay system. Handles content override
# proposals (submit, review, list), text-anchored comments (create, list,
# reply, resolve), and the owner approval dashboard.

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, render_template, abort
from flask_login import login_required, current_user

from extensions import db
from blueprints.auth.permissions import role_required
from models.audit import AuditSession
from services.editorial_service import (
    create_override,
    review_override,
    get_overrides_for_check,
    get_pending_overrides,
    get_all_overrides,
    create_comment,
    get_all_comments,
    get_comments_for_check,
    create_reply,
    resolve_comment,
)
from services.email_service import (
    send_edit_proposal_email,
    send_comment_notification_email,
)
from services.sheets_service import log_comment, log_edit_proposal
from services.json_writer import (
    apply_edit_to_filepath,
    apply_top_level_edit,
    revert_check_field_edit,
    find_filepath_for_check,
    find_filepath_for_scope,
    parse_scope,
)
from models.editorial import ContentOverride


# ========================================================================
#   Blueprint Setup
# ========================================================================

editorial_bp = Blueprint(
    "editorial",
    __name__,
    template_folder="templates",
    static_folder=None,
)


# ========================================================================
#   Content Override Endpoints
# ========================================================================

@editorial_bp.route("/api/propose-edit/", methods=["POST"])
@login_required
@role_required("editor", "owner", "admin")
def propose_edit():
    """
    Accepts a content override proposal from an editor.

    Expected JSON fields:
        check_id (str): The check identifier (required).
        field_path (str): Dot-notation path to the field (required).
        original_text (str): Snapshot of the original text (required).
        proposed_text (str): The proposed replacement (required).

    Returns:
        JSON response with the created override or error message.
    """

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    # Validate required fields
    check_id = (data.get("check_id") or "").strip()
    field_path = (data.get("field_path") or "").strip()
    original_text = (data.get("original_text") or "").strip()
    proposed_text = (data.get("proposed_text") or "").strip()

    source_url = (data.get("source_url") or "").strip() or None

    if not check_id or not field_path or not original_text or not proposed_text:
        return jsonify({"error": "All fields are required: check_id, field_path, original_text, proposed_text"}), 400

    # Don't allow proposals where nothing changed
    if original_text == proposed_text:
        return jsonify({"error": "Proposed text is identical to the original"}), 400

    override = create_override(
        check_id=check_id,
        field_path=field_path,
        original_text=original_text,
        proposed_text=proposed_text,
        proposed_by_id=current_user.id,
        source_url=source_url,
    )

    # All edits land in the To Do tab as "pending" so the owner can review
    # and approve from /admin/editorial/. Approving from the dashboard is
    # what writes the change to the source JSON.

    # Send email notification (best-effort)
    send_edit_proposal_email({
        "check_id": check_id,
        "field_path": field_path,
        "original_text": original_text,
        "proposed_text": proposed_text,
        "proposed_by": {
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "email": current_user.email,
        },
    })

    # Log to Google Sheet (best-effort)
    log_edit_proposal(
        timestamp=override.proposed_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        author_email=current_user.email,
        check_id=check_id,
        field_path=field_path,
        original_text=original_text,
        proposed_text=proposed_text,
    )

    return jsonify({"success": True, "override_id": override.id}), 201


@editorial_bp.route("/api/format-as-code/", methods=["POST"])
@login_required
@role_required("editor", "owner", "admin")
def format_as_code():
    """
    Submits a "wrap selection in <code> tags" edit as a pending proposal.

    Lands in the To Do tab on /admin/editorial/. The owner approves from
    there to write the change to the source JSON.

    Expected JSON fields:
        check_id (str): The check identifier (required).
        field_path (str): Dot-notation path within the check (required).
        selected_text (str): The exact text to wrap (required).
        source_url (str): Optional referring page URL.

    Returns:
        JSON response with the proposed (wrapped) text or an error message.
    """

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    check_id = (data.get("check_id") or "").strip()
    field_path = (data.get("field_path") or "").strip()
    selected_text = data.get("selected_text") or ""
    source_url = (data.get("source_url") or "").strip() or None

    if not (check_id and field_path and selected_text):
        return jsonify({"error": "Required: check_id, field_path, selected_text"}), 400

    # Refuse trivial selections that would produce noise or break parsing
    if not selected_text.strip():
        return jsonify({"error": "Selection is empty or whitespace-only"}), 400

    proposed_text = f"<code>{selected_text}</code>"

    override = create_override(
        check_id=check_id,
        field_path=field_path,
        original_text=selected_text,
        proposed_text=proposed_text,
        proposed_by_id=current_user.id,
        source_url=source_url,
    )

    return jsonify({
        "success": True,
        "override_id": override.id,
        "proposed_text": proposed_text,
        "status": "pending",
    }), 201


@editorial_bp.route("/api/overrides/<check_id>/", methods=["GET"])
@login_required
@role_required("editor", "owner", "admin")
def list_overrides(check_id):
    """
    Returns all content overrides for a given check.

    Args:
        check_id (str): The check identifier.

    Returns:
        JSON array of override objects.
    """

    overrides = get_overrides_for_check(check_id)
    return jsonify(overrides), 200


@editorial_bp.route("/api/overrides/<override_id>/review/", methods=["POST"])
@login_required
@role_required("owner")
def review_override_endpoint(override_id):
    """
    Approves or rejects a content override proposal.

    Expected JSON fields:
        status (str): "approved" or "rejected" (required).
        note (str): Optional reviewer note.

    Args:
        override_id (str): UUID of the override to review.

    Returns:
        JSON response with the updated override or error message.
    """

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    status = (data.get("status") or "").strip()
    if status not in ("approved", "rejected", "pending"):
        return jsonify({"error": "Status must be 'approved', 'rejected', or 'pending'"}), 400

    note = (data.get("note") or "").strip() or None
    proposed_text = (data.get("proposed_text") or "").strip() or None

    # The owner can also edit original_text from the dashboard to re-anchor
    # a stale override (where the JSON content has shifted since the edit
    # was proposed). When provided, use the new value for the JSON write
    # and persist it on the row so the audit trail reflects what was
    # actually replaced.
    original_text_override = (data.get("original_text") or "").strip() or None

    # If the override is currently "applied" (we wrote to JSON), reverting it
    # back to pending or rejecting it must also reverse the JSON file edit
    # so the rendered text actually matches the new status.
    existing = db.session.get(ContentOverride, override_id)
    if not existing:
        return jsonify({"error": "Override not found"}), 404

    # If the override is "applied", reverting must reverse the JSON write.
    if existing.status == "applied" and status in ("pending", "rejected"):
        scope = parse_scope(existing.check_id)
        filepath = find_filepath_for_scope(existing.check_id)
        if not filepath:
            return jsonify({
                "error": f"Source file not found for {existing.check_id}",
            }), 404

        if scope[0] == "subcat":

            # Subcat-level revert: swap proposed_text back to original_text
            # at the top-level field
            revert_result = apply_top_level_edit(
                filepath=filepath,
                field_path=existing.field_path,
                original_text=existing.proposed_text,
                new_text=existing.original_text,
            )
        else:
            revert_result = revert_check_field_edit(
                check_id=existing.check_id,
                field_path=existing.field_path,
                original_text=existing.original_text,
                current_text=existing.proposed_text,
            )

        if not revert_result["success"]:
            return jsonify({
                "error": f"Could not revert source JSON: {revert_result['message']}",
            }), 409

    # Approving an edit: find the source JSON file by scope and write the
    # change. On success, force status to "applied" so the render-time
    # overlay does not double-apply (it filters for "approved").
    if status == "approved" and existing.status != "applied":
        proposed = proposed_text if proposed_text else existing.proposed_text
        original = original_text_override if original_text_override else existing.original_text
        scope = parse_scope(existing.check_id)
        filepath = find_filepath_for_scope(existing.check_id)
        if not filepath:
            return jsonify({
                "error": f"Source file not found for {existing.check_id}",
            }), 404

        if scope[0] == "subcat":
            apply_result = apply_top_level_edit(
                filepath=filepath,
                field_path=existing.field_path,
                original_text=original,
                new_text=proposed,
            )
        else:
            apply_result = apply_edit_to_filepath(
                filepath=filepath,
                check_id=existing.check_id,
                field_path=existing.field_path,
                original_text=original,
                new_text=proposed,
            )

        if not apply_result["success"]:
            return jsonify({
                "error": f"Could not write to source JSON: {apply_result['message']}",
            }), 409

        # Persist the (possibly updated) original_text on the row so the
        # row reflects what was actually replaced
        if original_text_override:
            existing.original_text = original_text_override

        # Force the final status to "applied" so the render path treats
        # the JSON as the source of truth and does not also re-overlay.
        status = "applied"

    override = review_override(
        override_id=override_id,
        status=status,
        reviewed_by_id=current_user.id,
        note=note,
        proposed_text=proposed_text,
    )

    if not override:
        return jsonify({"error": "Override not found"}), 404

    return jsonify({"success": True, "status": override.status}), 200


@editorial_bp.route("/api/overrides/<override_id>/", methods=["DELETE"])
@login_required
@role_required("editor", "owner", "admin")
def delete_override(override_id):
    """
    Removes a content override.

    Permissions:
        - Owners can delete any override.
        - Editors can delete only their own overrides, and only while
          they're still pending (so they can pull back a proposal before
          the owner reviews it). Once an override is applied or rejected,
          only the owner can remove it.

    If the override was already applied to the source JSON, the JSON
    write is reversed before the row is deleted so the rendered content
    matches the deletion.

    Args:
        override_id (str): UUID of the override to delete.

    Returns:
        JSON response with success or an error message.
    """

    override = db.session.get(ContentOverride, override_id)
    if not override:
        return jsonify({"error": "Override not found"}), 404

    is_owner = current_user.role == "owner"
    is_proposer = override.proposed_by_id == current_user.id

    if not is_owner and (not is_proposer or override.status != "pending"):
        return jsonify({
            "error": "You can only remove your own pending edits"
        }), 403

    # If the edit had been written to the source JSON, undo that write
    # before dropping the audit row
    if override.status == "applied":
        scope = parse_scope(override.check_id)
        filepath = find_filepath_for_scope(override.check_id)
        if not filepath:
            return jsonify({
                "error": f"Source file not found for {override.check_id}",
            }), 404

        if scope[0] == "subcat":
            revert_result = apply_top_level_edit(
                filepath=filepath,
                field_path=override.field_path,
                original_text=override.proposed_text,
                new_text=override.original_text,
            )
        else:
            revert_result = revert_check_field_edit(
                check_id=override.check_id,
                field_path=override.field_path,
                original_text=override.original_text,
                current_text=override.proposed_text,
            )

        if not revert_result["success"]:
            return jsonify({
                "error": f"Could not revert source JSON: {revert_result['message']}",
            }), 409

    db.session.delete(override)
    db.session.commit()

    return jsonify({"success": True}), 200


# ========================================================================
#   Comment Endpoints
# ========================================================================

@editorial_bp.route("/api/comments/", methods=["POST"])
@login_required
@role_required("contributor", "editor", "owner", "admin")
def create_comment_endpoint():
    """
    Creates a text-anchored comment on audit content.

    Expected JSON fields:
        audit_id (str): UUID of the audit session (required).
        check_id (str): The check identifier (required).
        content_path (str): The data-content-path value (required).
        anchor_exact (str): The exact selected text (required).
        anchor_prefix (str): ~30 chars before selection (optional).
        anchor_suffix (str): ~30 chars after selection (optional).
        anchor_start_offset (int): Character offset start (optional).
        anchor_end_offset (int): Character offset end (optional).
        comment_text (str): The comment body (required).

    Returns:
        JSON response with the created comment or error message.
    """

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    # Validate required fields
    audit_id = (data.get("audit_id") or "").strip() or None
    check_id = (data.get("check_id") or "").strip()
    content_path = (data.get("content_path") or "").strip()
    anchor_exact = (data.get("anchor_exact") or "").strip()
    comment_text = (data.get("comment_text") or "").strip()
    source_url = (data.get("source_url") or "").strip() or None

    # Validate that audit_id exists in the DB; drop it if not
    if audit_id and not AuditSession.query.get(audit_id):
        audit_id = None

    if not check_id or not content_path or not anchor_exact or not comment_text:
        return jsonify({"error": "Required fields: check_id, content_path, anchor_exact, comment_text"}), 400

    # Build anchor data dict
    anchor_data = {
        "exact": anchor_exact,
        "prefix": (data.get("anchor_prefix") or "").strip() or None,
        "suffix": (data.get("anchor_suffix") or "").strip() or None,
        "start_offset": data.get("anchor_start_offset"),
        "end_offset": data.get("anchor_end_offset"),
    }

    comment = create_comment(
        audit_id=audit_id,
        check_id=check_id,
        content_path=content_path,
        anchor_data=anchor_data,
        comment_text=comment_text,
        author_id=current_user.id,
        source_url=source_url,
    )

    # Send email notification (best-effort)
    send_comment_notification_email({
        "check_id": check_id,
        "content_path": content_path,
        "anchor_exact": anchor_exact,
        "comment_text": comment_text,
        "author": {
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "email": current_user.email,
        },
    })

    # Log to Google Sheet (best-effort)
    log_comment(
        timestamp=comment.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        author_email=current_user.email,
        check_id=check_id,
        content_path=content_path,
        selected_text=anchor_exact,
        comment_text=comment_text,
    )

    return jsonify({"success": True, "comment_id": comment.id}), 201


@editorial_bp.route("/api/comments/<check_id>/", methods=["GET"])
@login_required
@role_required("contributor", "editor", "owner", "admin")
def list_comments(check_id):
    """
    Returns all comments for a given check within an audit.

    Query parameters:
        audit_id (str): UUID of the audit session (required).

    Args:
        check_id (str): The check identifier.

    Returns:
        JSON array of comment objects with nested replies.
    """

    audit_id = request.args.get("audit_id", "").strip() or None

    comments = get_comments_for_check(audit_id, check_id)
    return jsonify(comments), 200


@editorial_bp.route("/api/comments/<comment_id>/reply/", methods=["POST"])
@login_required
@role_required("contributor", "editor", "owner", "admin")
def reply_to_comment(comment_id):
    """
    Creates a reply on an existing comment.

    Expected JSON fields:
        reply_text (str): The reply body (required).

    Args:
        comment_id (str): UUID of the parent comment.

    Returns:
        JSON response with the created reply or error message.
    """

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    reply_text = (data.get("reply_text") or "").strip()
    if not reply_text:
        return jsonify({"error": "reply_text is required"}), 400

    reply = create_reply(
        comment_id=comment_id,
        reply_text=reply_text,
        author_id=current_user.id,
    )

    if not reply:
        return jsonify({"error": "Comment not found"}), 404

    return jsonify({"success": True, "reply_id": reply.id}), 201


@editorial_bp.route("/api/comments/<comment_id>/resolve/", methods=["POST"])
@login_required
@role_required("owner")
def resolve_comment_endpoint(comment_id):
    """
    Marks a comment as resolved.

    Args:
        comment_id (str): UUID of the comment to resolve.

    Returns:
        JSON response with success status or error message.
    """

    comment = resolve_comment(
        comment_id=comment_id,
        resolved_by_id=current_user.id,
    )

    if not comment:
        return jsonify({"error": "Comment not found"}), 404

    return jsonify({"success": True}), 200


# ========================================================================
#   Approval Dashboard
# ========================================================================

@editorial_bp.route("/admin/editorial/")
@login_required
@role_required("owner")
def approval_dashboard():
    """
    Renders the owner approval dashboard for pending edit proposals.

    Displays all pending content overrides in a table with approve/reject
    actions. Also shows recently reviewed overrides for reference.

    Returns:
        Rendered editorial/dashboard.html template.
    """

    overrides = get_all_overrides()
    open_comments = get_all_comments(resolved=False)
    resolved_comments = get_all_comments(resolved=True)

    return render_template(
        "editorial/dashboard.html",
        overrides=overrides,
        open_comments=open_comments,
        resolved_comments=resolved_comments,
    )


@editorial_bp.route("/api/overrides/reject-all/", methods=["POST"])
@login_required
@role_required("owner")
def reject_all_overrides():
    """
    Rejects all approved and pending overrides, restoring original JSON content.

    This is a bulk action for resetting all content overrides. After this,
    all pages will render from the original JSON files without any overrides.

    Returns:
        JSON response with the count of overrides rejected.
    """

    from extensions import db
    from models.editorial import ContentOverride

    overrides = ContentOverride.query.filter(
        ContentOverride.status.in_(["approved", "pending"])
    ).all()

    count = len(overrides)
    for override in overrides:
        override.status = "rejected"
        override.reviewed_by_id = current_user.id
        override.reviewed_at = datetime.now(timezone.utc)
        override.review_note = "Bulk rejected to restore original content"

    db.session.commit()

    return jsonify({"success": True, "count": count}), 200
