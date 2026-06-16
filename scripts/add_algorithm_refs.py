# scripts/add_algorithm_refs.py
# Adds algorithm update references to JSON audit subcheck files
# where the validate.impactful_updates array is empty and the
# subcheck topic is relevant to a known Google algorithm update.

import json
import os
import glob

# ========================================================================
#   Base Path
# ========================================================================

BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "json"
)

# ========================================================================
#   Reusable Update Entries
# ========================================================================

TIMELINE = "/timeline"

def entry(title, date, source, summary, link):
    """Builds a single impactful_updates entry with citation and timeline link."""
    return {
        "update_title": title,
        "update_date": date,
        "update_source": source,
        "update_summary": f'{summary} (<a href="{link}">source</a>). See more updates in the <a href="{TIMELINE}">interactive timeline</a>.',
        "update_link": link,
    }


# ========================================================================
#   Update Definitions by Category / Subcategory
# ========================================================================

# Keyed by subcategory name (matches JSON files)
UPDATES_BY_SUBCATEGORY = {
    # ---- CONTENT ----
    "headings": [
        entry(
            "September 2023 Helpful Content Update", "09/14/2023", "Google",
            "The Helpful Content classifier penalizes sites with unhelpful content at the site level; heading structure that misleads users or stuffs keywords can contribute to a negative sitewide assessment",
            "https://searchengineland.com/impact-of-the-google-september-2023-helpful-content-was-big-for-the-seo-industry-432751",
        ),
    ],
    "keyword_cannibalization": [
        entry(
            "September 2023 Helpful Content Update", "09/14/2023", "Google",
            "When multiple pages compete for the same keyword, the Helpful Content system may view overlapping content as low-value; consolidating cannibalized pages improves sitewide quality signals",
            "https://searchengineland.com/impact-of-the-google-september-2023-helpful-content-was-big-for-the-seo-industry-432751",
        ),
        entry(
            "March 2024 Core Update", "03/05/2024", "Google",
            "The March 2024 Core Update removed 45% of low-quality content from search results; sites with keyword cannibalization often have multiple thin pages that were targeted by this update",
            "https://searchengineland.com/google-march-2024-core-update-rollout-is-now-complete-438713",
        ),
    ],
    "meta_descriptions": [
        entry(
            "September 2023 Helpful Content Update", "09/14/2023", "Google",
            "While meta descriptions are not a direct ranking factor, misleading or generic descriptions contribute to poor user experience metrics that the Helpful Content system considers",
            "https://searchengineland.com/google-september-2023-helpful-content-system-update-rolling-out-431978",
        ),
    ],

    # ---- LINKS ----
    "external_links": [
        entry(
            "December 2022 Link Spam Update", "12/14/2022", "Google",
            "SpamBrain AI can now detect both sites buying links and sites created for passing outgoing links; unnatural outbound links are neutralized and their ranking signals removed",
            "https://developers.google.com/search/blog/2022/12/december-22-link-spam-update",
        ),
        entry(
            "July 2021 Link Spam Update", "07/26/2021", "Google",
            "Google introduced SpamBrain for link spam detection, identifying both link buyers and link sellers; sites with manipulative outbound link patterns saw penalties",
            "https://developers.google.com/search/blog/2021/07/link-tagging-and-link-spam-update",
        ),
    ],
    "internal_links": [
        entry(
            "September 2023 Helpful Content Update", "09/14/2023", "Google",
            "Strong internal linking helps Google understand site structure and content relationships; sites with poor internal linking and orphaned pages were disproportionately affected by the Helpful Content Update",
            "https://searchengineland.com/google-helpful-content-updates-survive-thrive-432843",
        ),
    ],
    "broken_links": [
        entry(
            "March 2024 Core Update", "03/05/2024", "Google",
            "The March 2024 Core Update strengthened quality signals; high volumes of broken internal links signal poor site maintenance and reduce overall content quality assessment",
            "https://developers.google.com/search/blog/2024/03/core-update-spam-policies",
        ),
    ],
    "orphaned_pages": [
        entry(
            "September 2023 Helpful Content Update", "09/14/2023", "Google",
            "Orphaned pages with no internal links are difficult for Google to discover and may be perceived as abandoned content, contributing negatively to sitewide quality assessment under the Helpful Content system",
            "https://searchengineland.com/google-helpful-content-updates-survive-thrive-432843",
        ),
    ],
    "anchor_text": [
        entry(
            "December 2022 Link Spam Update", "12/14/2022", "Google",
            "SpamBrain analyzes anchor text patterns to detect link manipulation; exact-match anchor text over-optimization is a strong spam signal",
            "https://developers.google.com/search/blog/2022/12/december-22-link-spam-update",
        ),
    ],
    "backlink_profile": [
        entry(
            "December 2022 Link Spam Update", "12/14/2022", "Google",
            "Google's SpamBrain AI can detect sites buying links and sites used for passing outgoing links; unnatural links are neutralized rather than penalized directly",
            "https://developers.google.com/search/blog/2022/12/december-22-link-spam-update",
        ),
        entry(
            "March 2024 Spam Update", "03/05/2024", "Google",
            "The March 2024 Spam Update introduced three new policies targeting scaled content abuse, site reputation abuse, and expired domain abuse, all of which can involve manipulative link-building tactics",
            "https://developers.google.com/search/blog/2024/03/core-update-spam-policies",
        ),
    ],

    # ---- EEAT ----
    "brand_signals": [
        entry(
            "December 2025 Core Update", "12/11/2025", "Google",
            "The December 2025 Core Update favored established retail brands: Aritzia (+56%), JCPenney (+52%), The North Face (+52%), while user-generated content platforms like Wikipedia, Reddit, and Quora saw declines",
            "https://www.amsive.com/insights/seo/googles-december-2025-core-update-winners-losers-analysis/",
        ),
        entry(
            "August 2023 Core Update", "08/22/2023", "Google",
            "Official government sites, university domains, and authoritative health organizations like WebMD and NIH saw major visibility gains, demonstrating the value of strong brand authority signals",
            "https://www.amsive.com/insights/seo/google-august-2023-core-update-winners-losers-analysis/",
        ),
    ],
    "entity_establishment": [
        entry(
            "March 2023 Core Update", "03/15/2023", "Google",
            "Google's E-E-A-T framework update added 'Experience' as a quality signal; sites with clear evidence of experience in writing, named authors and experts saw visibility gains",
            "https://www.amsive.com/insights/seo/googles-march-2023-core-update-winners-losers-analysis/",
        ),
    ],
}


# ========================================================================
#   Apply Updates
# ========================================================================

def apply_updates():
    """Walks all JSON files and adds impactful_updates where relevant."""

    updated_count = 0

    for subcat, new_entries in UPDATES_BY_SUBCATEGORY.items():

        # Find matching JSON file(s) for this subcategory
        pattern = os.path.join(BASE, "**", f"{subcat}.json")
        matches = glob.glob(pattern, recursive=True)

        for filepath in matches:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            changed = False

            for check in data:
                validate = check.get("validate", {})
                existing = validate.get("impactful_updates", [])

                # Only add to checks with empty updates
                if existing == []:
                    validate["impactful_updates"] = new_entries
                    check["validate"] = validate
                    changed = True

            if changed:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"  Updated: {filepath}")
                updated_count += 1

    print(f"\nDone. Updated {updated_count} files.")


if __name__ == "__main__":
    apply_updates()
