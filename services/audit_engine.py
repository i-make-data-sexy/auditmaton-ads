# services/audit_engine.py
# =====================================================================
# AUDITMATON: ADS SCAFFOLD NOTE
# Carried over from the Tag Management edition. Auditmaton: Ads uses
# MANUAL / checklist intake (no upload, no platform auth) and a
# Demand-vs-Supply top-level fork. Review whether this logic applies
# to ad audits or needs rewriting. See SCAFFOLD_REPORT.md.
# =====================================================================
# Core service for loading audit subcategory data from JSON schema files.
# Provides functions to scan category directories, parse subcheck metadata,
# and prepare data for the category browser template.

import json
import os
import logging
from collections import Counter

logger = logging.getLogger(__name__)


# ========================================================================
#   Constants
# ========================================================================

# ========================================================================
#   Platform Switching
# ========================================================================
# Auditmaton: Ads audits across multiple advertising platforms (demand-side
# and supply-side). The active platform is stored in the Flask session under
# `active_platform` (durably backed by a cookie); the dashboard chip strip is
# the user-facing toggle. Content lives under json/<platform>/<category>/
# <subcategory>.json, so call sites resolve get_json_base_dir() on every
# request. Platform slugs are TBD pending taxonomy design.

# Default platform when the session has not yet specified one
DEFAULT_PLATFORM = "google-ads"

# Platforms the dashboard chip strip can toggle between. Order = display
# order in the chip strip. Add a tuple here when content for a new platform
# ships under json/<slug>/.
# Auditmaton: Ads platform registry, loaded from json/_platforms.json (the
# single source of truth the app and the editorial linter both read). Each
# record is {slug, name, side, type}; side is demand|supply, type is the
# single-concept class used to group the intake and dashboard pickers.
def _load_platforms():
    """
    Loads the platform registry from json/_platforms.json.

    Returns:
        list[dict]: Platform records, or [] if the file is missing/unparseable.
    """

    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json", "_platforms.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("platforms", [])
    except (IOError, json.JSONDecodeError):
        logger.error("Could not load platform registry: %s", path)
        return []


PLATFORMS = _load_platforms()

# slug -> platform record
PLATFORM_BY_SLUG = {p["slug"]: p for p in PLATFORMS}

# Derived flat (slug, name) list. Kept so the existing validator call sites
# that build a slug set from AVAILABLE_PLATFORMS keep working unchanged.
AVAILABLE_PLATFORMS = [(p["slug"], p["name"]) for p in PLATFORMS]


def get_platform(slug):
    """
    Returns the platform record for a slug, or None.

    Args:
        slug (str): Platform slug.

    Returns:
        dict or None: The {slug, name, side, type} record.
    """

    return PLATFORM_BY_SLUG.get(slug)


def platform_side(slug):
    """
    Returns the side ("demand" / "supply") for a platform slug, or None.

    Args:
        slug (str): Platform slug.

    Returns:
        str or None: The platform's side.
    """

    p = PLATFORM_BY_SLUG.get(slug)
    return p["side"] if p else None


def platform_has_content(slug):
    """
    Returns True if json/<slug>/ holds at least one category directory with a
    JSON file. Used to mark content-less platforms in the picker.

    Args:
        slug (str): Platform slug.

    Returns:
        bool: Whether the platform has authored content.
    """

    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json", slug)
    if not os.path.isdir(base):
        return False
    for entry in os.listdir(base):
        sub = os.path.join(base, entry)
        if os.path.isdir(sub) and any(fn.endswith(".json") for fn in os.listdir(sub)):
            return True
    return False


def platforms_grouped_by_type(side, slugs=None):
    """
    Groups a side's platforms by type for the picker, preserving registry
    order across types and within each type. Each platform record is
    augmented with a `has_content` flag.

    Args:
        side (str): "demand" or "supply".
        slugs (set[str], optional): When given, restrict to these platform
            slugs (e.g., the stack the practitioner selected at intake).

    Returns:
        list[tuple[str, list[dict]]]: (type_label, [platform records]).
    """

    groups = []
    index = {}
    for p in PLATFORMS:
        if p.get("side") != side:
            continue
        if slugs is not None and p["slug"] not in slugs:
            continue
        t = p.get("type", "")
        if t not in index:
            index[t] = []
            groups.append((t, index[t]))
        index[t].append({**p, "has_content": platform_has_content(p["slug"])})
    return groups


def get_active_side():
    """
    Returns the side of the active platform, or None.

    Returns:
        str or None: "demand" / "supply".
    """

    return platform_side(get_active_platform())

PLATFORM_COOKIE_NAME = "active_platform"
PLATFORM_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year


def get_active_platform():
    """
    Returns the active platform slug for the current request.

    Read order: session (per-request cache), then cookie (durable
    persistence), then DEFAULT_PLATFORM. Cookie values are validated against
    AVAILABLE_PLATFORMS so a stale or tampered cookie can never poison the
    session.

    Returns:
        str: Platform slug (e.g., "google-tag-manager", "adobe-tags").
    """

    try:
        from flask import session, request
    except RuntimeError:
        return DEFAULT_PLATFORM

    if "active_platform" in session:
        return session["active_platform"]

    cookie_value = request.cookies.get(PLATFORM_COOKIE_NAME)
    if cookie_value:
        valid_slugs = {slug for slug, _ in AVAILABLE_PLATFORMS}
        if cookie_value in valid_slugs:
            session["active_platform"] = cookie_value
            return cookie_value

    return DEFAULT_PLATFORM


def set_active_platform(response, slug):
    """
    Persists the active platform on the response and the current session.

    Args:
        response: A Flask response object. The cookie is set on it.
        slug (str): Platform slug. Must match an entry in AVAILABLE_PLATFORMS;
            the caller validates.

    Returns:
        The response, with the platform cookie attached.
    """

    try:
        from flask import session
        session["active_platform"] = slug
    except RuntimeError:
        pass

    response.set_cookie(
        PLATFORM_COOKIE_NAME,
        slug,
        max_age=PLATFORM_COOKIE_MAX_AGE,
        samesite="Lax",
        httponly=False,
    )
    return response


def get_json_base_dir(platform=None):
    """
    Returns the JSON content directory for the given platform.

    Args:
        platform (str, optional): Platform slug. Defaults to the active
            platform from the session.

    Returns:
        str: Absolute path to json/<platform>/.
    """

    if platform is None:
        platform = get_active_platform()
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "json", platform)


# Backward-compat: resolves to the default platform's content silo. New code
# should call get_json_base_dir() so it stays in sync with the active platform.
JSON_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json", DEFAULT_PLATFORM)

# Category metadata: display names, icons, and descriptions
# Keys match the JSON directory names and dashboard card keys
# Per-platform category metadata. Keyed by platform slug, then by category
# slug (which matches the json/<platform>/<category>/ directory). Category
# order within each platform is the dashboard + treemap order. The dashboard
# and treemap derive everything from this plus the live json/ dirs, so adding,
# renaming, or reordering a category here propagates everywhere. Each platform
# has its own architecture, so categories and descriptions are platform-specific
# (some slugs repeat across platforms, e.g. "governance", but the metadata is
# scoped per platform).
CATEGORY_METADATA = {
    # Auditmaton: Ads (demand side). The full demand/supply category map is
    # TBD; google-ads/conversion-tracking is wired first for the calibration
    # sample. The legacy tag-management entries below are inert (not in
    # AVAILABLE_PLATFORMS) and will be removed when the ads taxonomy lands.
    "google-ads": {
        "conversion-tracking": {
            "display_name": "Conversion Tracking",
            "icon_class": "fa-solid fa-bullseye",
            "description": "Whether conversions are captured accurately, deduplicated, and durable as cookies erode",
        },
    },
    "google-tag-manager": {
        "container-structure": {
            "display_name": "Container Structure",
            "icon_class": "fa-solid fa-sitemap",
            "description": "Folder organization, naming conventions, and workspace hygiene",
        },
        "governance": {
            "display_name": "Governance",
            "icon_class": "fa-solid fa-scale-balanced",
            "description": "Versioning, publishing discipline, access control, and cleanup",
        },
        "triggers": {
            "display_name": "Triggers",
            "icon_class": "fa-solid fa-bolt",
            "description": "Trigger configuration and whether tags fire correctly",
        },
        "variables": {
            "display_name": "Variables",
            "icon_class": "fa-solid fa-cube",
            "description": "dataLayer design and variable configuration",
        },
        "data-quality": {
            "display_name": "Data Quality",
            "icon_class": "fa-solid fa-broom",
            "description": "Sensitive-data handling and custom code risk",
        },
        "privacy": {
            "display_name": "Privacy",
            "icon_class": "fa-solid fa-user-shield",
            "description": "Consent mode, compliance, and tag gating",
        },
        "infrastructure": {
            "display_name": "Infrastructure",
            "icon_class": "fa-solid fa-server",
            "description": "Server-side tagging, vendors, and measurement durability",
        },
    },
    "adobe-tags": {
        "property-structure": {
            "display_name": "Property Structure",
            "icon_class": "fa-solid fa-sitemap",
            "description": "Naming, library organization, extension inventory, and property sprawl",
        },
        "governance": {
            "display_name": "Governance",
            "icon_class": "fa-solid fa-scale-balanced",
            "description": "Publishing workflow, environments, permissions, and change documentation",
        },
        "rules": {
            "display_name": "Rules",
            "icon_class": "fa-solid fa-bolt",
            "description": "Rule events, conditions, action order, and duplicate rules",
        },
        "data-elements": {
            "display_name": "Data Elements",
            "icon_class": "fa-solid fa-cube",
            "description": "Data element types, naming, storage, and data-layer references",
        },
        "data-quality": {
            "display_name": "Data Quality",
            "icon_class": "fa-solid fa-broom",
            "description": "Sensitive-data handling and custom-code risk",
        },
        "privacy": {
            "display_name": "Privacy",
            "icon_class": "fa-solid fa-user-shield",
            "description": "Consent integration, consent gating, and regional compliance",
        },
        "infrastructure": {
            "display_name": "Infrastructure",
            "icon_class": "fa-solid fa-server",
            "description": "Hosts, embed and load, library performance, and the Web SDK",
        },
    },
    "tealium-iq": {
        "profile-structure": {
            "display_name": "Profile Structure",
            "icon_class": "fa-solid fa-sitemap",
            "description": "Naming, profile organization, sprawl, and loader configuration",
        },
        "governance": {
            "display_name": "Governance",
            "icon_class": "fa-solid fa-scale-balanced",
            "description": "Publishing workflow, versions, permissions, and change documentation",
        },
        "load-rules": {
            "display_name": "Load Rules",
            "icon_class": "fa-solid fa-bolt",
            "description": "Load-rule logic, reuse, and scope correctness",
        },
        "tags": {
            "display_name": "Tags",
            "icon_class": "fa-solid fa-tags",
            "description": "Tag inventory, variable mapping, duplicates, and versions",
        },
        "data-layer": {
            "display_name": "Data Layer",
            "icon_class": "fa-solid fa-layer-group",
            "description": "UDO design, variable definitions, timing, and sensitive data",
        },
        "extensions": {
            "display_name": "Extensions",
            "icon_class": "fa-solid fa-puzzle-piece",
            "description": "Extension scope, types, custom-code risk, and order",
        },
        "privacy": {
            "display_name": "Privacy",
            "icon_class": "fa-solid fa-user-shield",
            "description": "Consent Manager, consent-to-tag mapping, and regional compliance",
        },
    },
    "segment": {
        "sources": {
            "display_name": "Sources",
            "icon_class": "fa-solid fa-arrow-right-to-bracket",
            "description": "Source types, write keys, environments, and naming",
        },
        "implementation": {
            "display_name": "Implementation",
            "icon_class": "fa-solid fa-screwdriver-wrench",
            "description": "Snippet install, spec calls, event naming, and de-duplication",
        },
        "tracking-plan": {
            "display_name": "Tracking Plan",
            "icon_class": "fa-solid fa-clipboard-list",
            "description": "Plan conformance, property types, and Protocols enforcement",
        },
        "destinations": {
            "display_name": "Destinations",
            "icon_class": "fa-solid fa-arrow-right-from-bracket",
            "description": "Inventory, connection mode, filters, and mappings",
        },
        "identity": {
            "display_name": "Identity",
            "icon_class": "fa-solid fa-fingerprint",
            "description": "Identify calls, user vs anonymous IDs, traits, and resolution",
        },
        "privacy": {
            "display_name": "Privacy",
            "icon_class": "fa-solid fa-user-shield",
            "description": "Privacy Portal, consent, compliance, and deletion",
        },
        "governance": {
            "display_name": "Governance",
            "icon_class": "fa-solid fa-scale-balanced",
            "description": "Workspace roles, environment hygiene, and ownership",
        },
    },
    "commanders-act": {
        "structure": {
            "display_name": "Structure",
            "icon_class": "fa-solid fa-sitemap",
            "description": "Naming, container organization, sprawl, and templates",
        },
        "governance": {
            "display_name": "Governance",
            "icon_class": "fa-solid fa-scale-balanced",
            "description": "Deployment, environments, versions, permissions, and QA",
        },
        "tags": {
            "display_name": "Tags",
            "icon_class": "fa-solid fa-tags",
            "description": "Tag and destination inventory, routing, mappings, and duplicates",
        },
        "rules": {
            "display_name": "Rules",
            "icon_class": "fa-solid fa-bolt",
            "description": "Trigger and load conditions, reuse, and scope",
        },
        "data-layer": {
            "display_name": "Data Layer",
            "icon_class": "fa-solid fa-layer-group",
            "description": "Data layer design, variables, transformation scripts, and sensitive data",
        },
        "privacy": {
            "display_name": "Privacy",
            "icon_class": "fa-solid fa-user-shield",
            "description": "TrustCommander consent, consent gating, and regional compliance",
        },
        "infrastructure": {
            "display_name": "Infrastructure",
            "icon_class": "fa-solid fa-server",
            "description": "Server-side and Conversions API destinations, cookieless collection, and EU data residency",
        },
    },
    "piwik-pro": {
        "structure": {
            "display_name": "Structure",
            "icon_class": "fa-solid fa-sitemap",
            "description": "Naming, organization, sprawl, and templates",
        },
        "governance": {
            "display_name": "Governance",
            "icon_class": "fa-solid fa-scale-balanced",
            "description": "Publishing, versions, environments, and permissions",
        },
        "triggers": {
            "display_name": "Triggers",
            "icon_class": "fa-solid fa-bolt",
            "description": "Trigger types, conditions, firing correctness, and duplicates",
        },
        "variables": {
            "display_name": "Variables",
            "icon_class": "fa-solid fa-cube",
            "description": "Data layer, built-in and custom variables, and naming",
        },
        "data-quality": {
            "display_name": "Data Quality",
            "icon_class": "fa-solid fa-broom",
            "description": "Custom-code risk, PII handling, and sensitive data",
        },
        "privacy": {
            "display_name": "Privacy",
            "icon_class": "fa-solid fa-user-shield",
            "description": "Consent Manager integration, consent types per tag, gating, and compliance",
        },
        "infrastructure": {
            "display_name": "Infrastructure",
            "icon_class": "fa-solid fa-server",
            "description": "Container install and load, performance, and EU data residency",
        },
    },
}


# ========================================================================
#   Helper Functions
# ========================================================================

def _key_to_slug(key):
    """
    Converts an underscore-based JSON key to a URL-friendly dash-based slug.

    Args:
        key (str): Underscore-separated key (e.g., "robots_txt")

    Returns:
        str: Dash-separated slug (e.g., "robots-txt")
    """
    return key.replace("_", "-")


def _slug_to_key(slug):
    """
    Converts a URL-friendly dash-based slug back to an underscore-based key.

    Args:
        slug (str): Dash-separated slug (e.g., "robots-txt")

    Returns:
        str: Underscore-separated key (e.g., "robots_txt")
    """
    return slug.replace("-", "_")


def _substitute_template_vars(obj, variables):
    """
    Recursively replaces {{variable}} placeholders in all string values
    within a nested dict/list structure.

    Args:
        obj: A dict, list, or string containing template placeholders.
        variables (dict): Mapping of variable names to replacement values
            (e.g., {"domain": "https://example.com", "domain_bare": "example.com"}).

    Returns:
        The same structure with all placeholders replaced.
    """

    if isinstance(obj, str):
        for key, value in variables.items():
            obj = obj.replace("{{" + key + "}}", value)
        return obj

    if isinstance(obj, dict):
        return {k: _substitute_template_vars(v, variables) for k, v in obj.items()}

    if isinstance(obj, list):
        return [_substitute_template_vars(item, variables) for item in obj]

    return obj


def _format_display_name(file_key):
    """
    Converts a JSON file key into a human-readable display name.

    Handles common abbreviations and formatting. Splits on underscores,
    title-cases each word, and applies special-case overrides.

    Args:
        file_key (str): Underscore-separated file name (e.g., "xml_sitemap")

    Returns:
        str: Formatted display name (e.g., "XML Sitemap")
    """

    # Special-case display names for abbreviations and proper nouns
    overrides = {
        "server_side_conversions": "Server-Side Conversions",
        "xml_sitemap": "XML Sitemap",
        "robots_txt": "Robots.txt",
        "url_structure": "URL Structure",
        "url_domain_structure": "URL/Domain Structure",
        "eeat": "E-E-A-T",
        "cls": "CLS",
        "lcp": "LCP",
        "inp": "INP",
        "cwv_cls": "CWV: CLS",
        "cwv_inp": "CWV: INP",
        "cwv_lcp": "CWV: LCP",
        "nap_consistency": "NAP Consistency",
        "faq": "FAQ",
        "qa": "Q&A",
        "education_qa": "Education Q&A",
        "faq_qa_optimization": "FAQ/Q&A Optimization",
        "qa_faq_content": "Q&A/FAQ Content",
        "llm_friendly_content": "LLM-Friendly Content",
        "structured_data_for_llms": "Structured Data",
        "brand_mentions_citations": "Brand Signals",
        "ai_overview_visibility": "AI Overview Visibility",
        "ymyl_compliance": "YMYL Compliance",
        "video_seo": "Video SEO",
    }

    if file_key in overrides:
        return overrides[file_key]

    # Default: replace underscores with spaces, title-case
    return file_key.replace("_", " ").title()


# ========================================================================
#   Public API
# ========================================================================

def get_theme_registry():
    """
    Loads the controlled theme vocabulary from json/_themes.json.

    The per-check theme_tags filter and the dropdown both resolve labels and
    side scoping from this single registry. Returns a dict keyed by slug so a
    template can look up a theme's label in constant time.

    Returns:
        dict: {slug: {"slug", "label", "sides", "description"}}. Empty dict if
            the registry file is missing or malformed.
    """

    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json", "_themes.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logger.error("Failed to load theme registry: %s", e)
        return {}

    return {t["slug"]: t for t in data.get("themes", []) if t.get("slug")}


def get_category_metadata(category_key, platform=None):
    """
    Returns display name, icon class, and description for a category on a platform.

    Looks up the category in the active (or given) platform's CATEGORY_METADATA
    sub-dict. The category_key can use either underscores or dashes.

    Args:
        category_key (str): Category identifier (e.g., "rules" or "data-elements")
        platform (str, optional): Platform slug. Defaults to the active platform.

    Returns:
        dict or None: Category metadata dict, or None if not found.
    """

    if platform is None:
        platform = get_active_platform()
    platform_meta = CATEGORY_METADATA.get(platform, {})

    # Try the key as-is first, then the dash variant
    meta = platform_meta.get(category_key)
    if meta:
        return meta

    dash_key = category_key.replace("_", "-")
    return platform_meta.get(dash_key)


def get_subcategories(category_key, platform=None):
    """
    Loads all subcategory data for a given category from JSON files.

    Scans the json/<category>/ directory, loads each JSON file, and extracts
    subcategory metadata including check titles, impact scores, and counts.

    The category_key should match the JSON directory name. For categories
    with dashes in the directory name (e.g., "ai-geo"), the key can use
    either dashes or underscores.

    Args:
        category_key (str): Category directory name (e.g., "crawl", "ai-geo")

    Returns:
        list[dict]: List of subcategory dicts sorted alphabetically by display_name.
            Each dict contains:
            - key (str): File name without .json (underscore format)
            - slug (str): URL-friendly dash format
            - display_name (str): Human-readable name
            - check_count (int): Number of subchecks
            - max_impact (int): Highest impact_score among subchecks
            - checks (list[dict]): Subchecks sorted by impact_score desc

        Returns empty list if the category directory is not found.
    """

    # Resolve the JSON directory path for the active (or given) platform
    base_dir = get_json_base_dir(platform)
    category_dir = os.path.join(base_dir, category_key)

    # Try dash variant if underscore version not found
    if not os.path.isdir(category_dir):
        dash_key = category_key.replace("_", "-")
        category_dir = os.path.join(base_dir, dash_key)

    if not os.path.isdir(category_dir):
        logger.warning("Category directory not found: %s", category_key)
        return []

    subcategories = []

    # Load each JSON file in the category directory
    for filename in sorted(os.listdir(category_dir)):
        if not filename.endswith(".json"):
            continue

        file_key = filename.replace(".json", "")
        filepath = os.path.join(category_dir, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)

            # Some JSON files use a wrapper dict with metadata and an
            # 'audit_checks' key; others are a plain list of checks
            if isinstance(raw, dict):
                subchecks = raw.get("audit_checks", [])
            else:
                subchecks = raw
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Failed to load %s: %s", filepath, e)
            continue

        if not subchecks:
            continue

        # Extract check metadata sorted by impact score descending
        checks = sorted(
            [
                {
                    "id": check.get("id", ""),
                    "title": check.get("title", ""),
                    "impact_score": check.get("impact_score", 1),
                    "theme_tags": check.get("theme_tags", []),
                }
                for check in subchecks
            ],
            key=lambda c: c["impact_score"],
            reverse=True,
        )

        # Calculate max and average impact across all subchecks
        max_impact = max(c["impact_score"] for c in checks) if checks else 1
        avg_impact = round(sum(c["impact_score"] for c in checks) / len(checks), 1) if checks else 0

        # Extract wrapper metadata (intro, worth_it, etc.) from Rich Results
        # JSON files that use the dict format with an 'audit_checks' key
        metadata = {}
        if isinstance(raw, dict):
            metadata = {k: v for k, v in raw.items() if k != "audit_checks"}

        # Per-topic check counts across this subcategory, for the Topic
        # dropdown (icon + label + count, mirroring the Depth filter).
        theme_counter = Counter(t for c in checks for t in c.get("theme_tags", []))
        theme_slugs = sorted(theme_counter)

        subcategories.append({
            "key": file_key,
            "slug": _key_to_slug(file_key),
            "display_name": _format_display_name(file_key),
            "check_count": len(checks),
            "max_impact": max_impact,
            "avg_impact": avg_impact,
            "checks": checks,
            "theme_slugs": theme_slugs,
            "theme_counts": dict(theme_counter),
            "intro": metadata.get("intro", ""),
            "worth_it": metadata.get("worth_it", ""),
            "worth_it_explanation": metadata.get("worth_it_explanation", ""),
            "worth_it_visible": metadata.get("worth_it_visible", ""),
            "tier": metadata.get("tier", ""),
            "important_note": metadata.get("important_note", ""),
            "important_note_url": metadata.get("important_note_url", ""),
            "subcat_img": metadata.get("subcat_img", ""),
            "subcat_img_caption": metadata.get("subcat_img_caption", ""),
            "subcat_img_credit": metadata.get("subcat_img_credit", ""),
            "google_guidance": metadata.get("google_guidance", ""),
        })

    # Rich Results sorts alphabetically (content is being actively revised);
    # all other categories sort by average impact descending
    if category_key in ("rich_results", "rich-results"):
        subcategories.sort(key=lambda s: s["display_name"].lower())
    else:
        subcategories.sort(key=lambda s: s["avg_impact"], reverse=True)

    return subcategories


def get_check_data(category_key, subcategory_slug, check_id, domain=None, platform=None, site_name=None, voice=None):
    """
    Loads a single audit check from a subcategory JSON file.

    Resolves the category directory, converts the subcategory slug to a
    filename, loads the JSON array, and finds the check matching the given ID.
    If a domain is provided, replaces {{domain}} and {{domain_bare}} template
    variables throughout the check data.

    Args:
        category_key (str): Category directory name (e.g., "crawl", "ai-geo")
        subcategory_slug (str): URL-friendly subcategory slug (e.g., "robots-txt")
        check_id (str): Unique check identifier (e.g., "robots-txt-non-200")
        domain (str, optional): Full domain with protocol (e.g., "https://example.com").
            Used to substitute {{domain}} and {{domain_bare}} placeholders.

    Returns:
        tuple: (check_dict, subcategory_display_name) if found,
               (None, None) if the category, subcategory, or check is not found.
    """

    # Convert URL slug to underscore-based filename
    subcategory_key = _slug_to_key(subcategory_slug)

    # Resolve the category directory path for the active (or given) platform
    base_dir = get_json_base_dir(platform)
    category_dir = os.path.join(base_dir, category_key)

    # Try dash variant if underscore version not found
    if not os.path.isdir(category_dir):
        dash_key = category_key.replace("_", "-")
        category_dir = os.path.join(base_dir, dash_key)

    if not os.path.isdir(category_dir):
        logger.warning("Category directory not found for check lookup: %s", category_key)
        return None, None

    # Build the JSON file path
    filepath = os.path.join(category_dir, f"{subcategory_key}.json")
    if not os.path.isfile(filepath):
        logger.warning("Subcategory file not found: %s", filepath)
        return None, None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)

        # Some JSON files use a wrapper dict with metadata and an
        # 'audit_checks' key; others are a plain list of checks
        if isinstance(raw, dict):
            subchecks = raw.get("audit_checks", [])
        else:
            subchecks = raw
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Failed to load check data from %s: %s", filepath, e)
        return None, None

    # Find the matching check by ID
    for check in subchecks:
        if check.get("id") == check_id:
            subcategory_display = _format_display_name(subcategory_key)

            # Substitute narrative template variables. Voice always resolves
            # (defaulting to solo "I") and site name defaults to "the site",
            # so a finding never renders a raw {{voice_*}} or {{site_name}}
            # placeholder even before the auditor edits it.
            variables = {
                "site_name": site_name or "the site",
                "voice_found": "We found" if voice == "team" else "I found",
                "voice_recommend": "We recommend" if voice == "team" else "I recommend",
            }

            # Domain is a legacy SEO-edition variable; tag content does not use
            # it, but keep the substitution for safety if it is ever provided.
            if domain:

                # Strip protocol for {{domain_bare}} (used in site: searches)
                domain_bare = domain.replace("https://", "").replace("http://", "").rstrip("/")
                variables["domain"] = domain
                variables["domain_bare"] = domain_bare

            check = _substitute_template_vars(check, variables)

            # Apply approved content overrides from the database
            check = _apply_content_overrides(check, check_id)

            return check, subcategory_display

    logger.warning("Check ID not found in %s: %s", filepath, check_id)
    return None, None


def _apply_content_overrides(check, check_id):
    """
    Applies approved content overrides from the database to a check dict.

    Queries the content_overrides table for all approved overrides matching
    the check_id, then navigates the nested dict to each field_path and
    replaces the value with the approved proposed_text.

    Args:
        check (dict): The check data dict loaded from JSON.
        check_id (str): The check identifier.

    Returns:
        dict: The check dict with approved overrides applied.
    """

    # Import inside function to avoid circular imports at module level
    from services.editorial_service import get_approved_overrides_for_check, navigate_field_path

    overrides = get_approved_overrides_for_check(check_id)

    for override in overrides:
        parent, key = navigate_field_path(check, override.field_path)

        if parent is not None and key is not None:
            try:
                current_value = parent[key]

                # If the field is a string and the original text is a substring,
                # do a targeted find-and-replace instead of full field replacement
                if isinstance(current_value, str) and override.original_text in current_value:
                    parent[key] = current_value.replace(
                        override.original_text,
                        override.proposed_text,
                        1,  # Replace only the first occurrence
                    )
                else:

                    # Fallback: replace the entire field value
                    parent[key] = override.proposed_text

            except (TypeError, IndexError, KeyError):
                logger.warning(
                    "Failed to apply override %s::%s — path navigation succeeded but assignment failed",
                    check_id, override.field_path
                )
        else:
            logger.warning(
                "Failed to apply override %s::%s — could not navigate field path",
                check_id, override.field_path
            )

    return check
