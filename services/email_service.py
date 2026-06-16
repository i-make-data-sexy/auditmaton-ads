# services/email_service.py
# Email notification service for Auditmaton for Site Audits. Composes and sends
# email messages through Flask-Mail. Currently handles inaccuracy
# report notifications; will expand as other notification types
# are added.

import base64
import logging
from flask_mail import Message
from extensions import mail


logger = logging.getLogger(__name__)


# ========================================================================
#   Constants
# ========================================================================

# Recipient for inaccuracy report notifications
INACCURACY_REPORT_RECIPIENT = "feedback@annielytics.com"

# Recipient for bug report notifications
BUG_REPORT_RECIPIENT = "bug@annielytics.com"

# Recipient for edit proposal notifications (owner)
EDIT_PROPOSAL_RECIPIENT = "feedback@annielytics.com"

# Recipient for comment notifications
COMMENT_NOTIFICATION_RECIPIENT = "feedback@annielytics.com"


# ========================================================================
#   Email Composition
# ========================================================================

def _compose_inaccuracy_email(report):
    """
    Builds a Flask-Mail Message from an inaccuracy report dict.

    Formats the report data into a readable plain-text email body
    with clearly labeled fields. All fields are included regardless
    of whether the reporter filled them in (empty fields show as
    blank, making it obvious what was omitted).

    Args:
        report (dict): The structured report dict with keys:
            - timestamp (str): ISO timestamp
            - reporter (dict): first_name, last_name
            - context (dict): category, subcategory, check_title,
              active_step, page_url, selected_text
            - description (str): What was reported as inaccurate
            - reference (str): Supporting URL

    Returns:
        Message: A Flask-Mail Message object ready to send.
    """

    reporter = report.get("reporter", {})
    context = report.get("context", {})

    # Build the reporter display name
    name_parts = [
        reporter.get("first_name", ""),
        reporter.get("last_name", ""),
    ]
    reporter_name = " ".join(part for part in name_parts if part).strip() or "Unknown"

    # Build the subject line with category context
    category = context.get("category", "Unknown Category")
    check_title = context.get("check_title", "")
    subject = f"Inaccuracy Report: {category} > {check_title} ({reporter_name})"

    # Build the plain-text body with all report fields
    body_lines = [
        "INACCURACY REPORT",
        "=" * 50,
        "",
        f"Reported by:     {reporter_name}",
        f"Timestamp:       {report.get('timestamp', 'N/A')}",
        "",
        "CONTEXT",
        "-" * 50,
        f"Category:        {context.get('category', '')}",
        f"Subcategory:     {context.get('subcategory', '')}",
        f"Check title:     {context.get('check_title', '')}",
        f"Active step:     {context.get('active_step', '')}",
        f"Page URL:        {context.get('page_url', '')}",
        "",
        "SELECTED TEXT",
        "-" * 50,
        context.get("selected_text", "") or "(none)",
        "",
        "DESCRIPTION",
        "-" * 50,
        report.get("description", ""),
        "",
        "REFERENCE URL",
        "-" * 50,
        report.get("reference", "") or "(none)",
    ]

    body = "\n".join(body_lines)

    msg = Message(
        subject=subject,
        recipients=[INACCURACY_REPORT_RECIPIENT],
        body=body,
    )

    return msg


# ========================================================================
#   Public API
# ========================================================================

def send_inaccuracy_report_email(report):
    """
    Sends an email notification for an inaccuracy report.

    Composes the email from the report dict and sends it via
    Flask-Mail. Returns True on success, False on failure.
    Exceptions are caught and logged; this function never raises.

    Args:
        report (dict): The structured report dict (same format
            as saved to the JSON file).

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """

    try:
        msg = _compose_inaccuracy_email(report)
        mail.send(msg)
        logger.info("Inaccuracy report email sent to %s", INACCURACY_REPORT_RECIPIENT)
        return True

    except Exception as e:
        logger.error("Failed to send inaccuracy report email: %s", e)
        return False


# ========================================================================
#   Bug Report Emails
# ========================================================================

def _compose_bug_report_email(report):
    """
    Builds a Flask-Mail Message from a bug report dict.

    Formats the report data into a readable plain-text email body
    with clearly labeled fields. Images are decoded from base64
    data URLs and attached to the email as inline image files.

    Args:
        report (dict): The structured bug report dict with keys:
            - timestamp (str): ISO timestamp
            - reporter (dict): first_name, last_name, email
            - description (str): Bug description
            - context (dict): page_url, user_agent
            - images (list): Array of {data_url, filename} dicts

    Returns:
        Message: A Flask-Mail Message object ready to send.
    """

    reporter = report.get("reporter", {})
    context = report.get("context", {})
    images = report.get("images", [])

    # Build the reporter display name
    name_parts = [
        reporter.get("first_name", ""),
        reporter.get("last_name", ""),
    ]
    reporter_name = " ".join(part for part in name_parts if part).strip() or "Unknown"

    # Build the plain-text body with all report fields
    body_lines = [
        "BUG REPORT",
        "=" * 50,
        "",
        f"Reported by:     {reporter_name}",
        f"Email:           {reporter.get('email', 'Not provided')}",
        f"Timestamp:       {report.get('timestamp', 'N/A')}",
        "",
        "DESCRIPTION",
        "-" * 50,
        report.get("description", "No description provided"),
        "",
        "CONTEXT",
        "-" * 50,
        f"Page URL:        {context.get('page_url', '')}",
        f"User Agent:      {context.get('user_agent', '')}",
        f"Images attached: {len(images)}",
    ]

    body = "\n".join(body_lines)

    # Reply-To routes one-click replies to the reporter instead of the
    # support@ sender. Gmail SMTP requires the From header to match the
    # authenticated mailbox, so the user's address goes in Reply-To.
    reporter_email = (reporter.get("email") or "").strip()

    msg = Message(
        subject=f"Bug Report from {reporter_name}",
        recipients=[BUG_REPORT_RECIPIENT],
        body=body,
        reply_to=reporter_email or None,
    )

    # Decode base64 data URLs and attach as image files
    for i, img in enumerate(images):
        _attach_base64_image(msg, img, i)

    return msg


def _attach_base64_image(msg, img_data, index):
    """
    Decodes a base64 data URL and attaches it to a Flask-Mail Message.

    Parses the data URL format (data:image/jpeg;base64,...), extracts
    the MIME type and binary data, and attaches the image with a
    generated filename if none is provided.

    Args:
        msg (Message): The Flask-Mail Message to attach the image to.
        img_data (dict): Dict with 'data_url' (base64 string) and
            optional 'filename' (display name).
        index (int): Zero-based index used for fallback filename.

    Returns:
        None
    """

    data_url = img_data.get("data_url", "")
    filename = img_data.get("filename", "")

    if not data_url or "," not in data_url:
        return

    # Parse the data URL: "data:image/jpeg;base64,/9j/4AAQ..."
    header, encoded = data_url.split(",", 1)

    # Extract MIME type from header (e.g., "data:image/jpeg;base64")
    content_type = "image/jpeg"
    if ":" in header and ";" in header:
        content_type = header.split(":")[1].split(";")[0]

    # Determine file extension from MIME type
    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }
    ext = ext_map.get(content_type, ".jpg")

    # Use provided filename or generate one
    if not filename or filename == "pasted-image.png":
        filename = f"bug-screenshot-{index + 1}{ext}"

    # Decode and attach
    try:
        image_bytes = base64.b64decode(encoded)
        msg.attach(filename, content_type, image_bytes)
    except Exception as e:
        logger.warning("Failed to attach image %s: %s", filename, e)


def send_bug_report_email(report):
    """
    Sends an email notification for a bug report.

    Composes the email from the report dict and sends it via
    Flask-Mail. Returns True on success, False on failure.
    Exceptions are caught and logged; this function never raises.

    Args:
        report (dict): The structured bug report dict (same format
            as saved to the JSON file).

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """

    try:
        msg = _compose_bug_report_email(report)
        mail.send(msg)
        logger.info("Bug report email sent to %s", BUG_REPORT_RECIPIENT)
        return True

    except Exception as e:
        logger.error("Failed to send bug report email: %s", e)
        return False


# ========================================================================
#   Editorial Overlay Emails
# ========================================================================

def _compose_edit_proposal_email(data):
    """
    Builds a Flask-Mail Message from an edit proposal dict.

    Args:
        data (dict): The proposal data with keys:
            - check_id (str): The check identifier
            - field_path (str): Dot-notation path to the field
            - original_text (str): The original text
            - proposed_text (str): The proposed replacement
            - proposed_by (dict): first_name, last_name, email

    Returns:
        Message: A Flask-Mail Message object ready to send.
    """

    proposer = data.get("proposed_by", {})

    # Build the proposer display name
    name_parts = [
        proposer.get("first_name", ""),
        proposer.get("last_name", ""),
    ]
    proposer_name = " ".join(part for part in name_parts if part).strip() or "Unknown"

    body_lines = [
        "EDIT PROPOSAL",
        "=" * 50,
        "",
        f"Proposed by:     {proposer_name}",
        f"Email:           {proposer.get('email', '')}",
        "",
        "LOCATION",
        "-" * 50,
        f"Check:           {data.get('check_id', '')}",
        f"Field:           {data.get('field_path', '')}",
        "",
        "ORIGINAL TEXT",
        "-" * 50,
        data.get("original_text", ""),
        "",
        "PROPOSED TEXT",
        "-" * 50,
        data.get("proposed_text", ""),
    ]

    body = "\n".join(body_lines)

    # Reply-To routes one-click replies to the proposer instead of the
    # support@ sender. See bug report compose for the full rationale.
    proposer_email = (proposer.get("email") or "").strip()

    msg = Message(
        subject=f"Edit Proposal: {data.get('check_id', '')} ({proposer_name})",
        recipients=[EDIT_PROPOSAL_RECIPIENT],
        body=body,
        reply_to=proposer_email or None,
    )

    return msg


def send_edit_proposal_email(data):
    """
    Sends an email notification when an edit is proposed.

    Args:
        data (dict): The proposal data (see _compose_edit_proposal_email).

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """

    try:
        msg = _compose_edit_proposal_email(data)
        mail.send(msg)
        logger.info("Edit proposal email sent to %s", EDIT_PROPOSAL_RECIPIENT)
        return True

    except Exception as e:
        logger.error("Failed to send edit proposal email: %s", e)
        return False


def _compose_comment_notification_email(data):
    """
    Builds a Flask-Mail Message from a comment notification dict.

    Args:
        data (dict): The comment data with keys:
            - check_id (str): The check identifier
            - content_path (str): The data-content-path value
            - anchor_exact (str): The selected text the comment is about
            - comment_text (str): The comment body
            - author (dict): first_name, last_name, email

    Returns:
        Message: A Flask-Mail Message object ready to send.
    """

    author = data.get("author", {})

    # Build the author display name
    name_parts = [
        author.get("first_name", ""),
        author.get("last_name", ""),
    ]
    author_name = " ".join(part for part in name_parts if part).strip() or "Unknown"

    body_lines = [
        "NEW COMMENT",
        "=" * 50,
        "",
        f"Author:          {author_name}",
        f"Email:           {author.get('email', '')}",
        "",
        "LOCATION",
        "-" * 50,
        f"Check:           {data.get('check_id', '')}",
        f"Content path:    {data.get('content_path', '')}",
        "",
        "SELECTED TEXT",
        "-" * 50,
        data.get("anchor_exact", "") or "(none)",
        "",
        "COMMENT",
        "-" * 50,
        data.get("comment_text", ""),
    ]

    body = "\n".join(body_lines)

    # Reply-To routes one-click replies to the comment author instead of
    # the support@ sender. See bug report compose for the full rationale.
    author_email = (author.get("email") or "").strip()

    msg = Message(
        subject=f"Comment on {data.get('check_id', '')} ({author_name})",
        recipients=[COMMENT_NOTIFICATION_RECIPIENT],
        body=body,
        reply_to=author_email or None,
    )

    return msg


def send_comment_notification_email(data):
    """
    Sends an email notification when a comment is posted.

    Args:
        data (dict): The comment data (see _compose_comment_notification_email).

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """

    try:
        msg = _compose_comment_notification_email(data)
        mail.send(msg)
        logger.info("Comment notification email sent to %s", COMMENT_NOTIFICATION_RECIPIENT)
        return True

    except Exception as e:
        logger.error("Failed to send comment notification email: %s", e)
        return False
