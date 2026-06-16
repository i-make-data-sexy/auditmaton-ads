# blueprints/admin/routes.py
# Admin hub and owner-only management pages. Provides a central landing
# page with links to all admin tools (editorial review, user management,
# server logs, etc.).

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from blueprints.auth.permissions import role_required
from services.revision_log import load_revisions, RULE_LABELS
from services.site_type_suggestions import load_suggestions
from services.tier import set_test_tier, resolve_effective_tier, OVERRIDE_TIERS


# ========================================================================
#   Blueprint Setup
# ========================================================================

admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="templates",
    static_folder=None,
)


# ========================================================================
#   Admin Hub
# ========================================================================

@admin_bp.route("/admin/")
@login_required
@role_required("owner", "admin")
def admin_hub():
    """
    Renders the admin hub page with links to all admin tools, plus the
    App Architecture treemap (live category/subcategory taxonomy).

    Returns:
        Rendered admin/hub.html template.
    """

    from services.chart_builder import build_architecture_treemap

    return render_template(
        "admin/hub.html",
        treemap=build_architecture_treemap(),
    )


# ========================================================================
#   Editorial Revisions Dashboard
# ========================================================================

@admin_bp.route("/admin/editorial-revisions/")
@login_required
@role_required("owner", "admin")
def editorial_revisions_dashboard():
    """
    Renders the dashboard of editorial revisions — direct JSON content
    edits that enforce the Annielytics writing rules. Each row shows
    the revision date, the affected check (with deep link), the before
    and after text, the rule violated, and the severity.

    Returns:
        Rendered admin/editorial_revisions.html template.
    """

    # Newest first so the most recent edits are visible without scrolling
    revisions = sorted(
        load_revisions(),
        key=lambda r: r.get("revised_at", ""),
        reverse=True,
    )

    # Build the rule filter dropdown options. Show only labels for which
    # at least one revision exists, ordered by frequency so the most
    # common rule violations sit at the top.
    rule_counts = {}
    for r in revisions:
        rc = r.get("rule_category") or "other"
        rule_counts[rc] = rule_counts.get(rc, 0) + 1
    rule_options = sorted(
        [(key, RULE_LABELS.get(key, key), count) for key, count in rule_counts.items()],
        key=lambda t: -t[2],
    )

    return render_template(
        "admin/editorial_revisions.html",
        revisions=revisions,
        total_count=len(revisions),
        rule_options=rule_options,
        rule_labels=RULE_LABELS,
    )


# ========================================================================
#   Site Type Suggestions
# ========================================================================

@admin_bp.route("/admin/site-type-suggestions/")
@login_required
@role_required("owner", "admin")
def site_type_suggestions():
    """
    Lists site types users suggested via the intake form's 'Other' option.

    Newest first. Each row shows when it was submitted, the suggested type,
    and the audit context (submitting user, audit name, platform) so new
    site types can be added to the intake list over time.

    Returns:
        Rendered admin/site_type_suggestions.html template.
    """

    suggestions = sorted(
        load_suggestions(),
        key=lambda s: s.get("submitted_at", ""),
        reverse=True,
    )

    return render_template(
        "admin/site_type_suggestions.html",
        suggestions=suggestions,
        total_count=len(suggestions),
    )


# Backward-compat redirect from the legacy route. Remove after
# 2026-08-01 once nothing references the old URL.
from flask import redirect, url_for


@admin_bp.route("/admin/revisions/")
@login_required
@role_required("owner", "admin")
def revisions_dashboard_legacy_redirect():
    """Redirects the legacy /admin/revisions/ URL to the new path."""

    return redirect(url_for("admin.editorial_revisions_dashboard"), code=301)


# ========================================================================
#   Test as Tier Switcher
# ========================================================================

@admin_bp.route("/admin/test-tier/", methods=["POST"])
@login_required
@role_required("owner", "admin")
def set_test_tier_route():
    """
    Sets (or clears) the admin-only Test as tier override.

    The switcher in the menu posts the chosen tier here. Selecting 'admin'
    clears the override and returns to the real admin view; any other value
    in OVERRIDE_TIERS is stored in the session so the rest of the app treats
    the admin as a viewer of that tier. The front end reloads after a
    successful response so the new tier takes effect everywhere.

    Returns:
        JSON {ok, effective_tier} on success, or {error} with 400 if the
        requested tier is not a recognized override value.
    """

    data = request.get_json(silent=True) or {}
    tier = data.get("tier", "")

    if not set_test_tier(tier):
        return jsonify({
            "error": "Invalid tier",
            "allowed": sorted(OVERRIDE_TIERS),
        }), 400

    return jsonify({"ok": True, "effective_tier": resolve_effective_tier()})
