# ========================================================================
#   Chart Builder
#
#   Builds Plotly chart data structures for the app's visualizations.
#   Currently provides the "App Architecture" treemap (category ->
#   subcategory -> check-count), ported from the ML Model Picker's
#   overview treemap. The treemap is data-driven: it reads the live
#   taxonomy, so it always reflects the current category structure.
# ========================================================================


def build_architecture_treemap(platform=None):
    """
    Builds the category/subcategory tree for the App Architecture treemap.

    Reads the live taxonomy (CATEGORY_METADATA + the authored JSON content)
    and returns data ready for a Plotly treemap. Each category cell is sized
    by its total check count (the sum of its subcategories), and each
    subcategory cell is sized by its own check count. Every cell carries a
    relative URL the cell navigates to on click; window.APP_ROOT is prepended
    client-side.

    Categories with no authored content (e.g., the inherited SEO placeholders)
    are skipped. Categories are emitted in audit-flow order.

    Returns:
        dict: {
            "categories": [
                {
                    "key": str,            # category dir / URL slug
                    "name": str,           # display name
                    "slug": str,           # same as key (treemap id)
                    "url": str,            # relative, e.g. "/dashboard/<cat>/"
                    "total_checks": int,   # sum of subcategory check counts
                    "num_subcategories": int,
                    "subcategories": [
                        {"name", "slug", "count", "url"}, ...
                    ],
                }, ...
            ]
        }
    """
    from services.audit_engine import CATEGORY_METADATA, get_subcategories, get_active_platform

    if platform is None:
        platform = get_active_platform()

    # Categories and their order come from CATEGORY_METADATA (the single
    # source of truth); only those with authored content are emitted. This
    # keeps the treemap tethered to the live taxonomy so it never goes stale.
    categories = []
    for key, meta in CATEGORY_METADATA.get(platform, {}).items():
        subs = get_subcategories(key, platform=platform)
        if not subs:
            continue

        subcategories = []
        total_checks = 0
        for sub in subs:
            count = sub.get("check_count", 0)
            subcategories.append({
                "name": sub["display_name"],
                "slug": sub["slug"],
                "count": count,
                "url": f"/dashboard/{platform}/{key}/{sub['slug']}/",
            })
            total_checks += count

        categories.append({
            "key": key,
            "name": meta["display_name"],
            "slug": key,
            "url": f"/dashboard/{platform}/{key}/",
            "total_checks": total_checks,
            "num_subcategories": len(subcategories),
            "subcategories": subcategories,
        })

    return {"categories": categories}
