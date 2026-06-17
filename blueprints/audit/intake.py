# blueprints/audit/intake.py
# =====================================================================
# AUDITMATON: ADS SCAFFOLD NOTE
# Carried over from the Tag Management edition. Auditmaton: Ads uses
# MANUAL / checklist intake (no upload, no platform auth) and a
# Demand-vs-Supply top-level fork. Review whether this logic applies
# to ad audits or needs rewriting. See SCAFFOLD_REPORT.md.
# =====================================================================
#
# Manual intake for the Auditmaton: Ads edition.
#
# This edition uses a single-page, manual intake. There is no file
# upload, no API connection, and no crawl. The form captures the
# audit name, the advertiser role (demand-side or supply-side), the
# platform being audited, the site name, the site type, the narrative
# voice, and an optional account ID.
#
# All values are stored in the Flask session and consumed by the dashboard
# and by the check narrative substitution (voice + site name fill the
# {{voice_found}} / {{voice_recommend}} / {{site_name}} placeholders).
# =====================================================================

from flask import Blueprint, render_template, request, session, redirect, url_for
from flask_login import login_required, current_user

from services.audit_engine import (
    AVAILABLE_PLATFORMS,
    DEFAULT_PLATFORM,
    set_active_platform,
    platform_side,
    platform_has_content,
    platforms_grouped_by_type,
)
from services.site_type_suggestions import append_suggestion


# ========================================================================
#   Blueprint Setup
# ========================================================================

intake_bp = Blueprint(
    "intake",
    __name__,
    template_folder="templates",
    static_folder=None,
)


# ========================================================================
#   Option Lists
# ========================================================================

def get_site_types():
    """
    Returns the site-type options for the intake form.

    Site type feeds the per-check site_type_overlays (extra guidance shown
    when it matches), so the list mirrors the overlay keys the tag content
    uses, plus a general default. Site type does NOT gate or hide any
    category or check.

    Returns:
        list[dict]: Site type options with key and label.
    """
    return [
        {"key": "general", "label": "General / Not listed"},
        {"key": "ecommerce", "label": "Ecommerce"},
        {"key": "lead_gen", "label": "Lead generation"},
        {"key": "publishing", "label": "Publishing / Media"},
        {"key": "healthcare", "label": "Healthcare / Wellness"},
        {"key": "saas", "label": "SaaS / Software"},
        {"key": "nonprofit", "label": "Nonprofit"},
    ]


def get_voice_options():
    """
    Returns the narrative-voice options for the intake form.

    The choice fills {{voice_found}} / {{voice_recommend}} in the Generate
    findings, so a solo consultant reads as "I" and a team reads as "We".

    Returns:
        list[dict]: Voice options with key, label, and an example.
    """
    return [
        {"key": "solo", "label": "Solo consultant", "example": "I found, I recommend"},
        {"key": "team", "label": "Team or agency", "example": "We found, We recommend"},
    ]


# ========================================================================
#   Routes
# ========================================================================

@intake_bp.route("/intake/", methods=["GET", "POST"])
@login_required
def intake_start():
    """
    Single-page manual intake for a new tag audit.

    GET renders the form, prefilled with any previously saved values.
    POST stores every field in the session, sets the active platform, marks
    the intake complete, and redirects to that platform's dashboard.

    Returns:
        GET: Rendered intake form.
        POST: Redirect to the platform dashboard.
    """
    valid_platforms = {slug for slug, _ in AVAILABLE_PLATFORMS}

    if request.method == "POST":

        # Resolve the side (demand / supply), defaulting to demand
        side = request.form.get("side", "demand").strip()
        if side not in {"demand", "supply"}:
            side = "demand"

        # Collect platform slugs from the checkboxes; keep only slugs that
        # belong to the chosen side and exist in the registry
        raw_platforms = request.form.getlist("platforms")
        platforms = [
            s for s in raw_platforms
            if s in valid_platforms and platform_side(s) == side
        ]

        # Fall back to content-bearing platforms for the side when nothing
        # valid was submitted; then to the first platform on that side
        if not platforms:
            fallback = [s for s, _ in AVAILABLE_PLATFORMS
                        if platform_side(s) == side and platform_has_content(s)]
            if not fallback:
                fallback = [s for s, _ in AVAILABLE_PLATFORMS
                            if platform_side(s) == side]
            platforms = fallback or [DEFAULT_PLATFORM]

        # The active platform is the first selected platform that has
        # authored content; else the first selected; else the default
        active = next(
            (s for s in platforms if platform_has_content(s)),
            platforms[0] if platforms else DEFAULT_PLATFORM,
        )

        # Normalize the narrative voice to a known value (default solo)
        voice = request.form.get("voice", "solo").strip()
        if voice not in {"solo", "team"}:
            voice = "solo"

        # Store every intake field in the session
        audit_name = request.form.get("audit_name", "").strip()
        site_type = request.form.get("site_type", "general").strip()
        site_type_suggestion = request.form.get("site_type_suggestion", "").strip()

        session["intake_audit_name"] = audit_name
        # intake_platform is kept for backward compatibility (single active slug)
        session["intake_platform"] = active
        # intake_side and intake_platforms carry the Demand/Supply fork choices
        session["intake_side"] = side
        session["intake_platforms"] = platforms
        session["intake_site_name"] = request.form.get("site_name", "").strip()
        session["intake_site_type"] = site_type
        session["intake_site_type_suggestion"] = site_type_suggestion
        session["intake_voice"] = voice
        session["intake_container_id"] = request.form.get("container_id", "").strip()
        session["intake_complete"] = True

        # Log a user-submitted site type so it can be added to the list later.
        # Only when 'Other' is chosen and the user actually typed something.
        if site_type == "other" and site_type_suggestion:
            email = current_user.email if getattr(current_user, "is_authenticated", False) else ""
            append_suggestion(
                site_type_suggestion,
                user_email=email,
                audit_name=audit_name,
                platform=active,
            )

        # Set the active platform on the redirect response (cookie + session)
        # so the dashboard lands on the first content-bearing audited platform
        response = redirect(url_for("dashboard_home"))
        set_active_platform(response, active)
        return response

    # GET: build grouped picker data for both sides
    demand_groups = platforms_grouped_by_type("demand")
    supply_groups = platforms_grouped_by_type("supply")

    # Render the form prefilled with any previously saved values
    return render_template(
        "audit/intake.html",
        platforms=AVAILABLE_PLATFORMS,
        demand_groups=demand_groups,
        supply_groups=supply_groups,
        site_types=get_site_types(),
        voice_options=get_voice_options(),
        saved={
            "audit_name": session.get("intake_audit_name", ""),
            "platform": session.get("intake_platform", DEFAULT_PLATFORM),
            "side": session.get("intake_side", "demand"),
            "platforms": session.get("intake_platforms", []),
            "site_name": session.get("intake_site_name", ""),
            "site_type": session.get("intake_site_type", "general"),
            "site_type_suggestion": session.get("intake_site_type_suggestion", ""),
            "voice": session.get("intake_voice", "solo"),
            "container_id": session.get("intake_container_id", ""),
        },
    )
