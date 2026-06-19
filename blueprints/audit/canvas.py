# blueprints/audit/canvas.py
# Handles the canvas view (Level 3) for individual audit checks.
# Renders the Guide tab with -ate framework content and the Canvas tab
# with a rich text editor for building the audit document. Also handles
# the "Report as Inaccurate" form submissions, saving them as JSON files
# and sending email notifications via the email service.

import json
import os
import re
from datetime import datetime

from flask import Blueprint, render_template, abort, request, jsonify, session, redirect, url_for
from flask_login import login_required
from services.audit_engine import get_check_data, get_category_metadata, AVAILABLE_PLATFORMS, platform_side
from services.email_service import send_inaccuracy_report_email, send_bug_report_email
from blueprints.audit.routes import get_mock_active_audit

# Pattern for validating route slugs (letters, digits, hyphens, underscores)
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


# ========================================================================
#   Blueprint Setup
# ========================================================================

canvas_bp = Blueprint(
    "canvas",
    __name__,
    template_folder="templates",
    static_folder=None,
)


# ========================================================================
#   Routes
# ========================================================================

# Valid -ate step slugs for permalink routing
VALID_STEPS = ["educate", "investigate", "generate", "canvas"]


@canvas_bp.route("/dashboard/<side>/<platform>/<category>/<subcategory>/<check_id>/")
@canvas_bp.route("/dashboard/<side>/<platform>/<category>/<subcategory>/<check_id>/<step>/")
@login_required
def canvas_view(side, platform, category, subcategory, check_id, step=None):
    """
    Renders the canvas view for a single audit check (Level 3).

    Loads the full check data from JSON, resolves category and subcategory
    metadata, and renders the two-tab layout: Guide (walking through the
    -ate framework steps) and Canvas (rich text editor for audit output).

    Args:
        category (str): Category slug (e.g., "crawl", "ai-geo")
        subcategory (str): Subcategory slug (e.g., "robots-txt")
        check_id (str): Unique check identifier (e.g., "robots-txt-non-200")
        step (str, optional): Active -ate step slug (e.g., "educate").
            Defaults to "educate" when not provided.

    Returns:
        Rendered canvas.html template, or 404 if category/check not found
        or step is invalid.
    """

    # Validate route parameters against allowed patterns
    if not SLUG_PATTERN.match(category):
        abort(404)
    if not SLUG_PATTERN.match(subcategory):
        abort(404)
    if not SLUG_PATTERN.match(check_id):
        abort(404)

    # Default to educate when no step is provided
    if step is None:
        step = "educate"

    # Validate the step slug
    if step not in VALID_STEPS:
        abort(404)

    # Validate the platform and set it active for this request.
    valid_platforms = {s for s, _ in AVAILABLE_PLATFORMS}
    if platform not in valid_platforms:
        abort(404)

    # The side segment must be a real side and must match the platform's side;
    # redirect to the truthful URL when it does not.
    if side not in ("demand", "supply"):
        abort(404)
    real_side = platform_side(platform)
    if real_side and real_side != side:
        kwargs = {
            "side": real_side, "platform": platform, "category": category,
            "subcategory": subcategory, "check_id": check_id,
        }
        if step and step != "educate":
            kwargs["step"] = step
        return redirect(url_for("canvas.canvas_view", **kwargs))

    session["active_platform"] = platform

    # Load category metadata for breadcrumb and context
    meta = get_category_metadata(category, platform=platform)
    if not meta:
        abort(404)

    # Pull the audit context from the intake session for narrative variable
    # substitution. Site name fills {{site_name}}; voice fills
    # {{voice_found}} / {{voice_recommend}} in the Generate findings.
    active_audit = get_mock_active_audit()
    site_name = session.get("intake_site_name") or ""
    voice = session.get("intake_voice") or "solo"

    # Load the individual check data from JSON, substituting the narrative
    # template variables captured at intake.
    check, subcategory_display = get_check_data(
        category, subcategory, check_id,
        platform=platform, site_name=site_name, voice=voice,
    )
    if not check:
        abort(404)

    return render_template(
        "audit/canvas.html",
        category_key=category,
        category_meta=meta,
        subcategory_slug=subcategory,
        subcategory_display=subcategory_display,
        check=check,
        active_step=step,
        audit_id=active_audit.get("id", ""),
    )


# ========================================================================
#   Report as Inaccurate
# ========================================================================

# Directory where inaccuracy reports are saved as JSON files
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")


@canvas_bp.route("/api/report-inaccuracy/", methods=["POST"])
@login_required
def report_inaccuracy():
    """
    Accepts a JSON payload from the Report as Inaccurate form and saves
    it to a timestamped JSON file in the reports/ directory.

    Expected JSON fields:
        first_name (str): Reporter's first name (required)
        last_name (str): Reporter's last name (optional)
        description (str): What was inaccurate (required)
        reference (str): Supporting URL (optional)
        selected_text (str): Highlighted text from the Guide tab (optional)
        active_step (str): The -ate step that was active (optional)
        category (str): Audit category name (optional)
        subcategory (str): Audit subcategory name (optional)
        check_title (str): Audit check title (optional)
        page_url (str): Full page URL (optional)

    Returns:
        JSON response with success status or error message.
    """

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    # Validate required fields
    first_name = (data.get("first_name") or "").strip()
    description = (data.get("description") or "").strip()
    if not first_name or not description:
        return jsonify({"error": "First name and description are required"}), 400

    # Build the report record
    report = {
        "timestamp": datetime.now().isoformat(),
        "reporter": {
            "first_name": first_name,
            "last_name": (data.get("last_name") or "").strip(),
        },
        "context": {
            "category": (data.get("category") or "").strip(),
            "subcategory": (data.get("subcategory") or "").strip(),
            "check_title": (data.get("check_title") or "").strip(),
            "active_step": (data.get("active_step") or "").strip(),
            "page_url": (data.get("page_url") or "").strip(),
            "selected_text": (data.get("selected_text") or "").strip(),
        },
        "description": description,
        "reference": (data.get("reference") or "").strip(),
    }

    # Ensure the reports directory exists
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # Save with a timestamped filename
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
    filepath = os.path.join(REPORTS_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Send email notification (best-effort; does not block the response)
    send_inaccuracy_report_email(report)

    return jsonify({"success": True, "file": filename}), 201


# ========================================================================
#   Bug Reports
# ========================================================================

# Directory where bug reports are saved as JSON files
BUG_REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports", "bugs")


@canvas_bp.route("/api/bug-report/", methods=["POST"])
@login_required
def bug_report():
    """
    Accepts a JSON payload from the Bug Report form and saves
    it to a timestamped JSON file in the reports/bugs/ directory.

    Expected JSON fields:
        first_name (str): Reporter's first name (required)
        last_name (str): Reporter's last name (optional)
        email (str): Reporter's email address (required)
        description (str): Bug description (required)
        page_url (str): Full page URL (optional)
        user_agent (str): Browser user agent string (optional)
        images (list[dict]): Array of {data_url, filename} objects (optional)

    Returns:
        JSON response with success status or error message.
    """

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    # Validate required fields
    first_name = (data.get("first_name") or "").strip()
    email = (data.get("email") or "").strip()
    description = (data.get("description") or "").strip()
    if not first_name or not email or not description:
        return jsonify({"error": "First name, email, and description are required"}), 400

    # Build the bug report record
    report = {
        "timestamp": datetime.now().isoformat(),
        "type": "bug_report",
        "reporter": {
            "first_name": first_name,
            "last_name": (data.get("last_name") or "").strip(),
            "email": email,
        },
        "description": description,
        "context": {
            "page_url": (data.get("page_url") or "").strip(),
            "user_agent": (data.get("user_agent") or "").strip(),
        },
        "images": data.get("images", []),
    }

    # Ensure the bug reports directory exists
    os.makedirs(BUG_REPORTS_DIR, exist_ok=True)

    # Save with a timestamped filename
    filename = "bug_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
    filepath = os.path.join(BUG_REPORTS_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Send email notification (best-effort; does not block the response)
    send_bug_report_email(report)

    return jsonify({"success": True, "file": filename}), 201
