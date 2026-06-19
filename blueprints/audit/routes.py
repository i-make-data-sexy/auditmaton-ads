# blueprints/audit/routes.py
# Handles audit session management, dashboard, and category/subcategory views

import re

from flask import Blueprint, session, render_template, request, abort, redirect, url_for
from flask_login import login_required
from services.audit_engine import get_subcategories, get_category_metadata, get_theme_registry, AVAILABLE_PLATFORMS, platform_side

# Pattern for validating route slugs (letters, digits, hyphens, underscores).
# No length cap: the character class (lowercase, digits, hyphen, underscore,
# must start alphanumeric) is what keeps this safe; a too-long URL simply
# matches no check and 404s naturally. Check-id columns are String(100), and
# long platform prefixes (e.g., amazon-publisher-services-) plus descriptive
# suffixes routinely exceed 64 chars, which a cap would wrongly reject.
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


# ========================================================================
#   Blueprint Setup
# ========================================================================

audit_bp = Blueprint(
    "audit",
    __name__,
    template_folder="templates",
    static_folder=None,
)


# ========================================================================
#   Mock Data
# ========================================================================

def get_mock_active_audit():
    """
    Returns mock data for the active audit session context bar.

    Simulates a SaaS site audit on the AI tier with token tracking.

    Returns:
        dict: Active audit session data with domain, tier, and token info.
    """
    return {
        "id": "mock-audit",
        "domain": "https://example-saas.com",
        "tier": "ai",
        "tier_display": "AI Tier",
        "tokens_remaining": 8420,
    }


# ========================================================================
#   Intake → Dashboard Connection
# ========================================================================

# Audit finding #7: Reads intake session data to dynamically set
# locked/unlocked/muted status for conditional and variable sections.

def apply_intake_overrides(categories):
    """
    Applies intake session data to dashboard category states.

    Reads session keys set during the intake flow to determine which
    conditional sections are locked/unlocked and whether JavaScript
    should be muted. Also sets the Rich Results subcategory count
    based on the number of schemas selected at intake.

    Args:
        categories (list[dict]): List of category dicts from mock data.

    Returns:
        list[dict]: Categories with intake-driven overrides applied.
    """

    # Read intake session data
    site_types = session.get("intake_site_types", [])
    international = session.get("intake_international", False)
    has_ads = session.get("intake_has_ads", False)
    js_frameworks = session.get("intake_js_frameworks", [])
    selected_schemas = session.get("intake_rich_results_schemas", [])
    intake_complete = session.get("intake_complete", False)

    # Only apply overrides if intake has been completed
    if not intake_complete:
        return categories

    for cat in categories:
        key = cat["key"]

        # Shopping: locked unless Ecommerce site type selected
        if key == "shopping":
            if "ecommerce" in site_types:
                cat["locked"] = False
                cat["status"] = "not_started"
                cat["locked_reason"] = None
            else:
                cat["locked"] = True
                cat["status"] = "locked"
                cat["locked_reason"] = "Shopping audits are available for Ecommerce sites. Update your site type in intake settings to unlock."

        # Local: locked unless Local Business site type selected
        if key == "local":
            if "local_business" not in site_types:
                cat["locked"] = True
                cat["status"] = "locked"
                cat["locked_reason"] = "Local SEO is available for Local Business site types. Update your site type in intake settings to unlock."
            else:
                cat["locked"] = False
                cat["status"] = "not_started"
                cat["locked_reason"] = None

        # International: locked unless flagged at intake
        if key == "international":
            if not international:
                cat["locked"] = True
                cat["status"] = "locked"
                cat["locked_reason"] = "International SEO is available for sites serving multiple countries or languages. Update your intake settings to unlock."
            else:
                cat["locked"] = False
                cat["status"] = "not_started"
                cat["locked_reason"] = None

        # Ads: locked unless site has advertising flagged at intake
        if key == "ads":
            if has_ads:
                cat["locked"] = False
                cat["status"] = "not_started"
                cat["locked_reason"] = None
            else:
                cat["locked"] = True
                cat["status"] = "locked"
                cat["locked_reason"] = "Ad audits are available for sites that display advertising. Update your intake settings to unlock."

        # Rich Results: dynamic subcategory count based on schema selections
        if key == "rich_results":
            if selected_schemas:
                cat["total_subchecks"] = len(selected_schemas)

        # JavaScript: muted if "No / minimal JS" selected at intake
        if key == "javascript":
            if "no_minimal" in js_frameworks:
                cat["muted"] = True
                cat["muted_reason"] = "JavaScript section deprioritized because your site uses minimal JavaScript"

    return categories


# ========================================================================
#   Routes
# ========================================================================

@audit_bp.route("/dashboard/<side>/<platform>/<category>/")
@audit_bp.route("/dashboard/<side>/<platform>/<category>/<subcategory>/")
@audit_bp.route("/dashboard/<side>/<platform>/<category>/<subcategory>/<tab>/")
@login_required
def category_view(side, platform, category, subcategory=None, tab=None):
    """
    Renders the subcategory browser for a given audit category (Level 2).

    Loads all subcategories from the JSON directory for the given category,
    then renders the two-column layout with subcategory buttons on the left
    and the selected subcategory's checks on the right.

    Args:
        category (str): Category slug (e.g., "crawl", "ai-geo")
        subcategory (str, optional): Subcategory slug (e.g., "robots-txt").
            Defaults to the first subcategory alphabetically.
        tab (str, optional): Active tab slug ("overview" or "audit-checks").
            Defaults to "overview".

    Returns:
        Rendered category.html template, or 404 if category not found.
    """

    # Validate route parameters against allowed patterns
    if not SLUG_PATTERN.match(category):
        abort(404)
    if subcategory and not SLUG_PATTERN.match(subcategory):
        abort(404)

    # Validate tab parameter
    if tab and tab not in ("overview", "audit-checks"):
        abort(404)

    # Validate the platform and set it active for this request so
    # platform-scoped content resolves correctly.
    valid_platforms = {s for s, _ in AVAILABLE_PLATFORMS}
    if platform not in valid_platforms:
        abort(404)

    # The side segment must be a real side and must match the platform's side;
    # redirect to the truthful URL when it does not (the path is the source of
    # truth for the side, so it never carries a query param).
    if side not in ("demand", "supply"):
        abort(404)
    real_side = platform_side(platform)
    if real_side and real_side != side:
        kwargs = {"side": real_side, "platform": platform, "category": category}
        if subcategory:
            kwargs["subcategory"] = subcategory
        if tab:
            kwargs["tab"] = tab
        return redirect(url_for("audit.category_view", **kwargs))

    session["active_platform"] = platform

    # Load category metadata
    meta = get_category_metadata(category, platform=platform)
    if not meta:
        abort(404)

    # Load all subcategories with their checks
    subcategories = get_subcategories(category, platform=platform)
    if not subcategories:
        abort(404)

    # Determine which subcategory is selected
    selected_slug = subcategory if subcategory else subcategories[0]["slug"]

    # Validate the selected subcategory exists
    selected = None
    for sub in subcategories:
        if sub["slug"] == selected_slug:
            selected = sub
            break

    # Fall back to first if slug doesn't match
    if not selected:
        selected = subcategories[0]
        selected_slug = selected["slug"]

    # Determine active tab (default to overview)
    active_tab = tab if tab else "overview"

    return render_template(
        "audit/category.html",
        category_key=category,
        category_meta=meta,
        subcategories=subcategories,
        selected=selected,
        selected_slug=selected_slug,
        active_tab=active_tab,
        theme_registry=get_theme_registry(),
    )
