# services/tier.py
# Effective-tier resolution and the admin "Test as tier" override.
#
# This module is the single place that answers "what tier is the current
# viewer being treated as?" It folds together three inputs: the real user's
# purchased products/subscription, the admin-only session override set by the
# Test as tier switcher, and the unauthenticated state. Feature gates (charts,
# AI, ghost-chart upsells) should call tier_grants()/tier_at_least() here rather
# than scattering has_product() checks across the codebase.

from flask import session
from flask_login import current_user


# ========================================================================
#   Tier Vocabulary
# ========================================================================

# Canonical tier ladder, lowest to highest. Rank is the list index, so
# tier_at_least() can compare two tiers by position. "admin" is handled
# separately (it is a full-access bypass, not a point on the paid ladder).
CANONICAL_TIERS = ["unauth", "none", "free_trial", "base", "viz", "ai"]

# The subset the admin Test as tier switcher is allowed to set. Anything
# outside this set is rejected by the route. "admin" clears the override.
OVERRIDE_TIERS = {"admin", "free_trial", "base", "ai", "unauth"}

# Session key holding the active override (only honored for real admins).
_SESSION_KEY = "test_tier"

# Feature -> minimum tier that grants it. Future gates read this map via
# tier_grants() so the tier->feature mapping lives in exactly one place.
_FEATURE_MIN_TIER = {
    "charts": "viz",          # Plotly visualizations (Viz add-on and up)
    "ai_narrative": "ai",     # AI-written audit narrative
    "ai_chatbot": "ai",       # AI chatbot
    "contextual_queries": "ai",
}

# Display labels for the switcher options, in menu order.
SWITCHER_OPTIONS = [
    ("admin", "Admin"),
    ("free_trial", "Free Trial"),
    ("base", "Base"),
    ("ai", "AI"),
    ("unauth", "Unauthenticated"),
]


# ========================================================================
#   Admin / Override State
# ========================================================================

def is_real_admin():
    """
    Reports whether the current user is a genuine admin or owner, ignoring
    any active Test as tier override.

    This is what gates switcher visibility: a real admin previewing as
    'base' or 'unauth' must still see the switcher so they can switch back.

    Returns:
        bool: True if authenticated and the real role is owner or admin.
    """

    return bool(
        current_user.is_authenticated
        and getattr(current_user, "role", None) in ("owner", "admin")
    )


def get_test_tier():
    """
    Returns the active Test as tier override, or None.

    The override is only honored for real admins, so a stale session value
    on a downgraded account can never grant or alter access.

    Returns:
        str or None: One of OVERRIDE_TIERS, or None when no override applies.
    """

    if not is_real_admin():
        return None

    tier = session.get(_SESSION_KEY)
    if tier in OVERRIDE_TIERS:
        return tier
    return None


def set_test_tier(tier):
    """
    Sets or clears the Test as tier override in the session.

    Selecting 'admin' clears the override entirely (return to real admin
    view). Any other value in OVERRIDE_TIERS is stored.

    Args:
        tier (str): A value from OVERRIDE_TIERS.

    Returns:
        bool: True if the value was applied, False if it was rejected.
    """

    if tier not in OVERRIDE_TIERS:
        return False

    if tier == "admin":
        session.pop(_SESSION_KEY, None)
    else:
        session[_SESSION_KEY] = tier

    return True


def clear_test_tier():
    """
    Removes any Test as tier override from the session.

    Called on logout so an override never leaks into a later session.

    Returns:
        None
    """

    session.pop(_SESSION_KEY, None)


# ========================================================================
#   Effective Tier Resolution
# ========================================================================

def resolve_effective_tier():
    """
    Resolves the tier the current viewer should be treated as.

    Order of precedence:
        1. An active admin override (the Test as tier switcher).
        2. Unauthenticated visitors -> 'unauth'.
        3. Real admins with no override -> 'admin' (full access).
        4. Otherwise, derived from purchased products and subscription.

    Returns:
        str: One of CANONICAL_TIERS or 'admin'.
    """

    override = get_test_tier()
    if override is not None:
        return override

    if not current_user.is_authenticated:
        return "unauth"

    if is_real_admin():
        return "admin"

    # Derive from products. Add-ons stack on Base, so check highest first.
    if current_user.has_product("ai"):
        return "ai"
    if current_user.has_product("viz"):
        return "viz"
    if current_user.has_active_subscription:
        return "base"
    return "none"


def tier_at_least(tier, floor):
    """
    Reports whether a tier ranks at or above a floor on the canonical ladder.

    'admin' always satisfies the check (full access). A tier not on the
    ladder never satisfies it.

    Args:
        tier (str): The tier to test (e.g., the effective tier).
        floor (str): The minimum tier required (e.g., 'viz').

    Returns:
        bool: True if tier outranks or equals floor.
    """

    if tier == "admin":
        return True
    if tier not in CANONICAL_TIERS or floor not in CANONICAL_TIERS:
        return False
    return CANONICAL_TIERS.index(tier) >= CANONICAL_TIERS.index(floor)


def tier_grants(tier, feature):
    """
    Reports whether a tier grants a named feature.

    The feature-to-tier mapping lives in _FEATURE_MIN_TIER so future gates
    (ghost charts, AI chatbot, token-metered queries) call this instead of
    re-deriving the rule.

    Args:
        tier (str): The tier to test (e.g., the effective tier).
        feature (str): A key in _FEATURE_MIN_TIER (e.g., 'charts').

    Returns:
        bool: True if the tier is high enough for the feature.
    """

    floor = _FEATURE_MIN_TIER.get(feature)
    if floor is None:
        return False
    return tier_at_least(tier, floor)


def viewer_authenticated():
    """
    Reports whether the viewer should be presented as logged in.

    Returns False during an admin 'unauth' preview so the nav and menus
    render the logged-out experience, even though the admin is really
    still authenticated. Otherwise mirrors Flask-Login's auth state.

    Returns:
        bool: True if the viewer should see authenticated UI.
    """

    if resolve_effective_tier() == "unauth":
        return False
    return current_user.is_authenticated
