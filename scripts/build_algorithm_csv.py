# scripts/build_algorithm_csv.py
# Generates the google_algorithm_updates.csv with all columns including
# insights, recovery_time, rep_quote, and citation_url.
# Run once to rebuild the CSV, then discard or keep for future updates.

import csv
import os

# ========================================================================
#   Output Path
# ========================================================================

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "content", "updates", "google_algorithm_updates.csv"
)

# ========================================================================
#   Column Definitions
# ========================================================================

FIELDNAMES = [
    "date",
    "update_name",
    "update_type",
    "description",
    "typical_impact",
    "affected_factors",
    "confirmed",
    "reference_url",
    "insights",
    "recovery_time",
    "rep_quote",
    "rep_name",
    "citation_url",
]

# ========================================================================
#   Update Data
# ========================================================================

updates = [
    {
        "date": "2/5/26",
        "update_name": "February 2026 Discover Core Update",
        "update_type": "Core Update",
        "description": "First Discover-specific core update affecting Google Discover feed rankings without impacting traditional Search results",
        "typical_impact": "Discover feed visibility changes",
        "affected_factors": "Discover content quality, visual appeal, engagement signals",
        "confirmed": "Yes",
        "reference_url": "https://developers.google.com/search/blog/2026/02/discover-core-update",
        "insights": (
            "First time Google publicly labeled a core update as Discover-specific; the update does not affect traditional Search rankings (https://searchengineland.com/google-releases-discover-core-update-february-2026-468308)"
            "||The update favors locally relevant content from publishers based in a user's own country, reducing cross-border content in Discover feeds (https://searchengineland.com/google-february-2026-discover-core-update-is-now-complete-469450)"
            "||Sensational and clickbait headlines are explicitly demoted; in-depth, original, and timely content from sites with topic expertise is boosted (https://www.seroundtable.com/google-february-2026-discover-core-update-40887.html)"
            "||Discover's share of Google-sourced traffic to news publishers nearly doubled from 37% in 2023 to roughly 68%, while traditional Search traffic dropped from 51% to about 27% (https://searchengineland.com/google-releases-discover-core-update-february-2026-468308)"
            "||Non-US publishers saw reduced visibility in US Discover feeds, suggesting a strong geo-locality signal was introduced (https://www.searchenginejournal.com/googles-discover-core-update-finishes-rolling-out/568413/)"
        ),
        "recovery_time": "None found",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "12/11/25",
        "update_name": "December 2025 Core Update",
        "update_type": "Core Update",
        "description": "Final core update of 2025 rolling out Dec 11-29 with moderate ranking volatility",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, E-E-A-T, relevance signals",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-december-2025-core-update-rolling-out-now-465852",
        "insights": (
            "eCommerce and apparel sites were the biggest winners: Aritzia (+56%), JCPenney (+52%), The North Face (+52%), Zara (+34%), suggesting the update favored commercial content from established retail brands (https://www.amsive.com/insights/seo/googles-december-2025-core-update-winners-losers-analysis/)"
            "||Wikipedia was the largest absolute loser, dropping 435 visibility points; Reddit, Facebook, and Quora also saw significant declines, signaling a correction of UGC platform dominance (https://www.amsive.com/insights/seo/googles-december-2025-core-update-winners-losers-analysis/)"
            "||Health publishers experienced near-universal declines: Healthline (-27%), Medical News Today (-42%), WebMD, and Mayo Clinic all lost visibility (https://www.amsive.com/insights/seo/googles-december-2025-core-update-winners-losers-analysis/)"
            "||Thesaurus.com was the single biggest winner (+33%) while Merriam-Webster dropped 11%, showing a striking split among reference sites (https://www.amsive.com/insights/seo/googles-december-2025-core-update-winners-losers-analysis/)"
            "||IHG.com saw its biggest visibility spike in five years; travel and tourism averaged +10% gains, but review-focused travel platforms like TripAdvisor (-8%) declined (https://www.amsive.com/insights/seo/googles-december-2025-core-update-winners-losers-analysis/)"
            "||Several sites including Reddit, Facebook, NYT, BBC, and Reuters rebounded within one week after the Dec 29 rollout completion, while Quora and TikTok continued declining (https://www.amsive.com/insights/seo/googles-december-2025-core-update-winners-losers-analysis/)"
        ),
        "recovery_time": "1\u20132 weeks for quick rebounds; ongoing for others",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "10/7/25",
        "update_name": "October 2025 Unnamed Update",
        "update_type": "Unconfirmed",
        "description": "Heavy ranking flux hitting 123.0 F on MozCast with widespread volatility",
        "typical_impact": "Site-wide volatility",
        "affected_factors": "Unknown factors, possible algorithm testing",
        "confirmed": "No",
        "reference_url": "https://www.seroundtable.com/google-search-ranking-volatility-heated-40234.html",
        "insights": (
            "Multiple ranking tracking tools detected high volatility simultaneously, though Google did not confirm any update (https://www.seroundtable.com/google-search-ranking-volatility-heated-40234.html)"
            "||MozCast temperatures reached 123.0 F, well above baseline, suggesting significant but unacknowledged algorithmic changes (https://www.seroundtable.com/google-search-ranking-volatility-heated-40234.html)"
            "||The volatility was widespread across verticals rather than concentrated in specific niches, consistent with a broad algorithmic shift (https://www.seroundtable.com/google-search-ranking-volatility-heated-40234.html)"
        ),
        "recovery_time": "None found",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "8/26/25",
        "update_name": "August 2025 Spam Update",
        "update_type": "Spam Update",
        "description": "First spam update since end of 2024 with broadened spam definition per Liz Reid",
        "typical_impact": "Spam penalties",
        "affected_factors": "Expanded spam signals, content quality, link schemes",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-releases-august-2025-spam-update-461232",
        "insights": (
            "Google VP of Search Liz Reid expanded the definition of spam to include content that merely repeats what is already well known, without adding the creator's perspective or depth (https://searchengineland.com/google-releases-august-2025-spam-update-461232)"
            "||The rollout took 27 days (Aug 26 \u2013 Sep 22), making it one of the longer spam updates in Google's history (https://searchengineland.com/google-august-2025-spam-update-done-rolling-out-461560)"
            "||Google is giving more ranking weight to content from creators who bring unique perspective or expertise and invest real time and craft into their work (https://searchengineland.com/google-releases-august-2025-spam-update-461232)"
            "||This was a general and broad spam update; Google did not announce any unique or special targeting with this release (https://searchengineland.com/google-august-2025-spam-update-done-rolling-out-461560)"
        ),
        "recovery_time": "None found",
        "rep_quote": "We've extended the concept of spam to also include content that repeats what's already well known without bringing the creator's perspective and depth.",
        "rep_name": "Liz Reid",
        "citation_url": "https://searchengineland.com/google-releases-august-2025-spam-update-461232",
    },
    {
        "date": "6/30/25",
        "update_name": "June 2025 Core Update",
        "update_type": "Core Update",
        "description": "Second Core Update of 2025 with some Helpful Content Update (HCU) recoveries reported",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, HCU recovery signals, E-E-A-T",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-june-2025-core-update-rolling-out-now-457731",
        "insights": (
            "Many sites hit by the September 2023 Helpful Content Update saw their first meaningful recoveries, with rich snippets and featured snippets returning after nearly two years of suppressed visibility (https://www.seroundtable.com/google-june-2025-core-update-recoveries-39735.html)"
            "||Amazon was the biggest loser; LinkedIn dropped 50+ visibility points (-18%), concentrated in its /company/ subfolder (https://www.amsive.com/insights/seo/june-2025-core-update-winners-losers-trends/)"
            "||YouTube was the top winner (+307 visibility points, +12%), followed by Wikipedia (+276 points); arts and entertainment sites dominated the gains (https://www.amsive.com/insights/seo/june-2025-core-update-winners-losers-trends/)"
            "||Long-established independent sites with clear authorship saw significant gains: color-meanings.com (17 years old), explainthatstuff.com (13 years), and gamepressure.com (20 years) all recovered (https://www.amsive.com/insights/seo/june-2025-core-update-winners-losers-trends/)"
            "||Retail giants declined broadly: Amazon, eBay, Target, Wayfair, and Best Buy all lost visibility (https://www.amsive.com/insights/seo/june-2025-core-update-winners-losers-trends/)"
            "||Health was a highly volatile sector; YMYL sites swung dramatically, with some gaining in March only to drop sharply in June (https://searchengineland.com/data-providers-google-june-2025-core-update-was-a-big-update-459226)"
            "||This was one of the larger core updates in recent memory, with a 16-day rollout (Jun 30 \u2013 Jul 17) (https://searchengineland.com/google-june-2025-core-update-rollout-is-now-complete-458617)"
        ),
        "recovery_time": "2\u20133 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "3/13/25",
        "update_name": "March 2025 Core Update",
        "update_type": "Core Update",
        "description": "First Core Update of 2025 with historically high volatility (130.1 F)",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, user signals, relevance",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-march-2025-core-update-rolling-out-now-453253",
        "insights": (
            "Forum sites experienced a recalibration after roughly 18 months of elevated visibility following Google's mid-2023 'hidden gems' initiative (https://searchengineland.com/google-march-2025-core-update-rollout-is-now-complete-453364)"
            "||Google AI Overviews expanded massively during the rollout: +528% for entertainment queries, +387% for restaurant queries, and +381% for travel queries (https://searchengineland.com/google-ai-overviews-spike-march-2025-core-update-453841)"
            "||Home services keywords showed unprecedented movement, with Local SEO Guide's 100,000-keyword tracking revealing some of the most volatile SERPs in 12 months (https://searchengineland.com/data-providers-google-march-2025-core-update-had-similar-volatility-to-the-previous-update-453778)"
            "||The rollout lasted 14 days (Mar 13\u201327) and had similar overall volatility to the December 2024 core update, though it did not feel as widespread as some previous updates (https://searchengineland.com/data-providers-google-march-2025-core-update-had-similar-volatility-to-the-previous-update-453778)"
        ),
        "recovery_time": "2\u20134 weeks",
        "rep_quote": "There's nothing new or special that creators need to do for this update as long as they've been making satisfying content meant for people.",
        "rep_name": "A Google social media account",
        "citation_url": "https://searchengineland.com/google-march-2025-core-update-rolling-out-now-453253",
    },
    {
        "date": "3/5/25",
        "update_name": "March 2025 Unnamed Update",
        "update_type": "Unconfirmed",
        "description": "Pre-core update volatility reaching 121.7 F on MozCast",
        "typical_impact": "Site-wide volatility",
        "affected_factors": "Unknown factors, possible pre-update testing",
        "confirmed": "No",
        "reference_url": "https://www.seroundtable.com/pre-google-march-2025-core-update-39084.html",
        "insights": (
            "Volatility spiked just eight days before the confirmed March 2025 Core Update, a pattern sometimes seen as pre-update testing (https://www.seroundtable.com/pre-google-march-2025-core-update-39084.html)"
            "||MozCast recorded 121.7 F temperatures, significantly above the baseline, with multiple third-party tools confirming the flux (https://www.seroundtable.com/pre-google-march-2025-core-update-39084.html)"
            "||Google did not acknowledge this volatility, which is typical of unconfirmed ranking fluctuations (https://www.seroundtable.com/pre-google-march-2025-core-update-39084.html)"
        ),
        "recovery_time": "None found",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "2/19/25",
        "update_name": "February 2025 Unnamed Update",
        "update_type": "Unconfirmed",
        "description": "Significant ranking flux at 125.8 F with multiple tools showing spikes",
        "typical_impact": "Site-wide volatility",
        "affected_factors": "Unknown factors, algorithm testing",
        "confirmed": "No",
        "reference_url": "https://www.seroundtable.com/google-search-ranking-volatility-heats-38941.html",
        "insights": (
            "MozCast reached 125.8 F with widespread reports from webmasters confirming unusual ranking movement (https://www.seroundtable.com/google-search-ranking-volatility-heats-38941.html)"
            "||Multiple tracking tools showed simultaneous spikes, suggesting a real algorithmic change rather than data noise (https://www.seroundtable.com/google-search-ranking-volatility-heats-38941.html)"
            "||Google provided no acknowledgment; the update remained unconfirmed (https://www.seroundtable.com/google-search-ranking-volatility-heats-38941.html)"
        ),
        "recovery_time": "None found",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "12/19/24",
        "update_name": "December 2024 Spam Update",
        "update_type": "Spam Update",
        "description": "Year-end spam update targeting link spam and content manipulation",
        "typical_impact": "Spam penalties",
        "affected_factors": "Link spam, AI content abuse, cloaking",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-december-2024-spam-update-unleashed-449556",
        "insights": (
            "This was a general and broad spam update (not specifically link spam), and was considered one of the bigger spam updates in a long time, hitting very hard within a few days (https://www.seroundtable.com/google-december-2024-spam-update-done-38641.html)"
            "||The rollout lasted just 7 days (Dec 19\u201326), making it one of the faster spam updates; it was global, impacting all regions and languages (https://searchengineland.com/google-december-2024-spam-update-done-rolling-out-449651)"
            "||SpamBrain, Google's AI-based spam prevention system, was improved to catch both existing and new types of spam more effectively (https://searchengineland.com/google-december-2024-spam-update-unleashed-449556)"
            "||Google warned that recovery from spam penalties can take many months and recommended reviewing spam policies to ensure compliance (https://searchengineland.com/google-december-2024-spam-update-unleashed-449556)"
        ),
        "recovery_time": "Several months per Google's guidance",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "11/11/24",
        "update_name": "November 2024 Core Update",
        "update_type": "Core Update",
        "description": "Late year core update with focus on helpful content signals",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content helpfulness, expertise, user satisfaction",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-november-2024-core-update-rolling-out-now-448083",
        "insights": (
            "This was the least volatile core update of 2024, considered weaker overall compared to the March and August updates (https://searchengineland.com/data-providers-google-november-2024-core-update-was-less-volatile-449040)"
            "||Forbes.com saw visibility drop to zero across its /advisor/, /health/, and /home-improvement/ subfolders, continuing Google's crackdown on site reputation abuse (https://www.seroundtable.com/google-november-2024-core-update-movement-38414.html)"
            "||The travel industry showed the highest fluctuation levels; health and finance niches experienced lower volatility in top positions (https://searchengineland.com/data-providers-google-november-2024-core-update-was-less-volatile-449040)"
            "||Rollout lasted 24 days (Nov 11 \u2013 Dec 5), longer than typical for a less volatile update (https://searchengineland.com/google-november-2024-core-update-rollout-is-now-complete-448428)"
        ),
        "recovery_time": "3\u20134 weeks",
        "rep_quote": "This update is designed to continue our work to improve the quality of our search results by showing more content that people find genuinely useful and less content that feels like it was made just to perform well on Search.",
        "rep_name": "A Google social media account",
        "citation_url": "https://searchengineland.com/google-november-2024-core-update-rolling-out-now-448083",
    },
    {
        "date": "8/15/24",
        "update_name": "August 2024 Core Update",
        "update_type": "Core Update",
        "description": "Summer core update with focus on relevance and content quality",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, relevance, technical SEO",
        "confirmed": "Yes",
        "reference_url": "https://developers.google.com/search/blog/2024/08/august-2024-core-update",
        "insights": (
            "Semrush reported peak volatility significantly higher than the March 2024 update; 44% of poll respondents said rankings were down vs. 27% up (https://searchengineland.com/data-providers-google-august-2024-core-update-was-very-volatile-446597)"
            "||A ranking bug affected the first four days of the rollout; Google fixed it and advised disregarding early movement (https://searchengineland.com/google-august-2024-core-update-what-were-seeing-early-on-445290)"
            "||Of 380+ sites tracked from the September 2023 HCU, only 47 showed signs of improvement; most did not see meaningful recoveries (https://searchengineland.com/google-august-2024-core-update-rollout-is-now-complete-446225)"
            "||Google stated the update aims to promote useful content from small and independent publishers, a direct response to feedback from creators (https://searchengineland.com/google-august-2024-core-update-rolling-out-now-445221)"
            "||Rollout lasted 20 days (Aug 15 \u2013 Sep 3), slightly shorter than originally expected (https://searchengineland.com/google-august-2024-core-update-rollout-is-now-complete-446225)"
        ),
        "recovery_time": "2\u20134 weeks",
        "rep_quote": "This update took into account feedback we heard from some creators and others over the past few months. We will continue this work in future updates to show more useful content made by people.",
        "rep_name": "John Mueller",
        "citation_url": "https://searchengineland.com/google-august-2024-core-update-rolling-out-now-445221",
    },
    {
        "date": "6/20/24",
        "update_name": "June 2024 Spam Update",
        "update_type": "Spam Update",
        "description": "AI-generated content spam and link spam targeting",
        "typical_impact": "Penalties for spam content",
        "affected_factors": "AI content abuse, link schemes, thin content",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-unleashes-june-2024-spam-update-443374",
        "insights": (
            "This was a general broad spam update that did not specifically target link spam and did not automate the site reputation abuse policy (still manual actions only) (https://searchengineland.com/google-june-2024-spam-update-done-rolling-out-443504)"
            "||SpamBrain improvements targeted new types of spam while maintaining detection of existing spam patterns (https://searchengineland.com/google-unleashes-june-2024-spam-update-443374)"
            "||Sites with AI detection scores near 100% continued to see pages, site sections, or entire sites deindexed throughout 2024 (https://www.amsive.com/insights/seo/googles-helpful-content-update-ranking-system-what-happened-and-what-changed-in-2024/)"
            "||The rollout completed in approximately one week, making it one of the faster spam updates (https://searchengineland.com/google-june-2024-spam-update-done-rolling-out-443504)"
        ),
        "recovery_time": "1\u20132 weeks rollout; months for recovery",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "3/5/24",
        "update_name": "March 2024 Core Update",
        "update_type": "Core Update",
        "description": "Simultaneous core and spam update rollout",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, site reputation, technical health",
        "confirmed": "Yes",
        "reference_url": "https://developers.google.com/search/blog/2024/03/core-update-spam-policies",
        "insights": (
            "The longest core update in Google's history at 45 days (Mar 5 \u2013 Apr 19); Google reported removing 45% of low-quality, unoriginal content from search results, exceeding the original 40% target (https://searchengineland.com/google-march-2024-core-update-rollout-is-now-complete-438713)"
            "||Over 800 websites were completely deindexed; 100% of deindexed sites showed signs of AI-generated content, with 50% having 90\u2013100% AI-generated posts (https://www.searchenginejournal.com/googles-march-2024-core-update-impact-hundreds-of-websites-deindexed/510981/)"
            "||Reddit was the biggest winner overall (+1,000 visibility points in 2024), followed by Amazon (+531 points); user-generated content and forum sites replaced many traditional publishers (https://www.amsive.com/insights/seo/seo-in-2024-winners-losers-and-overall-trends/)"
            "||The vast majority of percentage losers were informational sites monetizing through display ads and/or affiliate links (https://www.amsive.com/insights/seo/the-march-2024-spam-core-updates-on-google/)"
            "||Wikipedia lost 135 visibility points; other major institutional losers included Cambridge.org (-60), Britannica (-47), and NYT (-48), despite being traditionally authoritative (https://www.amsive.com/insights/seo/the-march-2024-spam-core-updates-on-google/)"
            "||This update ended the standalone Helpful Content Update; the HCU classifier was folded into the core ranking system (https://searchengineland.com/google-march-2024-core-update-rollout-is-now-complete-438713)"
        ),
        "recovery_time": "6\u20138 weeks for rollout; months\u2013years for recovery",
        "rep_quote": "Some things take much longer to be reassessed (sometimes months), and some bigger effects require another update cycle. 'Recover' implies going back to how things were before, and IMO that is always unrealistic, since the world, user-expectations, and the rest of the web continues to change.",
        "rep_name": "John Mueller",
        "citation_url": "https://www.searchenginejournal.com/googles-john-mueller-on-website-recovery-after-core-updates/515122/",
    },
    {
        "date": "3/5/24",
        "update_name": "March 2024 Spam Update",
        "update_type": "Spam Update",
        "description": "Targeting scaled content abuse and expired domain abuse",
        "typical_impact": "Penalties for spam tactics",
        "affected_factors": "Scaled content, expired domains, site reputation abuse",
        "confirmed": "Yes",
        "reference_url": "https://developers.google.com/search/blog/2024/03/core-update-spam-policies",
        "insights": (
            "Three new spam policies were introduced simultaneously: scaled content abuse, site reputation abuse, and expired domain abuse (https://searchengineland.com/google-released-massive-search-quality-improvements-with-march-2024-core-update-and-multiple-spam-updates-438144)"
            "||Scaled content abuse targets mass-produced content regardless of whether it is AI-generated, human-created, or a combination (https://searchengineland.com/google-march-2024-core-update-things-you-need-to-know-438370)"
            "||Expired domain abuse targets the practice of purchasing expired domains and repurposing them to boost search ranking of low-quality content (https://developers.google.com/search/blog/2024/03/core-update-spam-policies)"
            "||Site reputation abuse (parasite SEO) targets third-party content published on high-authority domains primarily for ranking manipulation; enforcement began May 5, 2024 via manual actions (https://searchengineland.com/google-march-2024-core-update-things-you-need-to-know-438370)"
        ),
        "recovery_time": "Months; no fixed timeline per Google",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "11/8/23",
        "update_name": "November 2023 Reviews Update",
        "update_type": "Reviews Update",
        "description": "Improvements to review content evaluation systems",
        "typical_impact": "Review page rankings",
        "affected_factors": "Review quality, evidence of experience, detailed reviews",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-releases-november-2023-reviews-update-434262",
        "insights": (
            "This was the final standalone reviews update; Google announced the reviews system would be incorporated into core updates going forward (https://searchengineland.com/google-releases-november-2023-reviews-update-434262)"
            "||The rollout took 29 days (Nov 8 \u2013 Dec 7), overlapping entirely with the November 2023 Core Update, making it difficult to isolate which update caused specific ranking changes (https://searchengineland.com/google-algorithm-updates-2023-recap-435846)"
            "||Sites reliant on review traffic saw continued volatility, with gains or losses depending on alignment with Google's evolving experience signals (https://searchengineland.com/google-algorithm-updates-2023-recap-435846)"
        ),
        "recovery_time": "4\u20135 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "11/2/23",
        "update_name": "November 2023 Core Update",
        "update_type": "Core Update",
        "description": "Year-end core update with focus on helpful content",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content helpfulness, E-E-A-T, user satisfaction",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-november-2023-core-update-released-434123",
        "insights": (
            "The longest documented core update rollout at 26 days (Nov 2\u201328), ten days longer than the previous record held by the August 2023 core update (https://searchengineland.com/google-november-2023-core-update-rollout-is-now-complete-434529)"
            "||More volatile than the October 2023 core update; SimilarWeb's SERP Seismometer peaked at 71 out of 100 on November 7th (https://searchengineland.com/data-providers-google-november-2023-core-update-was-more-volatile-than-the-october-2023-core-update-435494)"
            "||12.75% of top 10 results were pages that previously ranked beyond position 20, indicating significant ranking reshuffling (https://www.semrush.com/blog/the-impact-of-the-november-core-update/)"
            "||eCommerce was the hardest-hit category with an average decline of nearly -24% across 32 tracked domains (https://www.amsive.com/insights/seo/seo-in-2023-winners-losers-and-overall-trends/)"
        ),
        "recovery_time": "3\u20134 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "10/5/23",
        "update_name": "October 2023 Core Update",
        "update_type": "Core Update",
        "description": "Broad core update with SERP volatility",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, relevance, technical SEO",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-releases-october-2023-broad-core-update-432935",
        "insights": (
            "Rolled out in 14 days (Oct 5\u201319), overlapping with the October 2023 Spam Update, making impact attribution difficult (https://searchengineland.com/google-october-2023-core-update-rollout-is-now-complete-433191)"
            "||Less impactful overall than the August 2023 update; the average position change was about 2.5 positions compared to 3 positions in August (https://searchengineland.com/data-providers-on-the-google-october-2023-core-and-spam-update-433697)"
            "||Volatility was felt broadly but was hard to measure cleanly because of the simultaneous spam update rollout (https://searchengineland.com/data-providers-on-the-google-october-2023-core-and-spam-update-433697)"
        ),
        "recovery_time": "2\u20133 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "10/4/23",
        "update_name": "October 2023 Spam Update",
        "update_type": "Spam Update",
        "description": "Targeting multiple spam tactics including cloaking",
        "typical_impact": "Penalties for spam tactics",
        "affected_factors": "Cloaking, link spam, content spam",
        "confirmed": "Yes",
        "reference_url": "https://developers.google.com/search/blog/2023/10/october-2023-spam-update",
        "insights": (
            "Primarily targeted cloaking, hacked sites, auto-generated content, and scraped spam, with expanded coverage in Turkish, Vietnamese, Indonesian, Hindi, and Chinese (https://www.seroundtable.com/google-releases-october-2023-spam-update-36163.html)"
            "||Spam sites were visibly hit around October 9; well-maintained sites were largely unaffected (https://searchengineland.com/google-october-2023-spam-update-done-rolling-out-433189)"
            "||The overlap with the core update made it hard to isolate spam update impact, but clear spam demotions were observed in non-English markets (https://www.searchenginejournal.com/google-rolls-out-october-2023-spam-update/497794/)"
        ),
        "recovery_time": "2\u20133 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "9/14/23",
        "update_name": "September 2023 Helpful Content Update",
        "update_type": "Helpful Content Update (HCU)",
        "description": "Major HCU iteration with stronger classifier",
        "typical_impact": "Site-wide content evaluation",
        "affected_factors": "User-first content, content pruning, topical authority",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-september-2023-helpful-content-system-update-rolling-out-431978",
        "insights": (
            "This was the most devastating algorithm update for independent publishers in recent memory; educational sites, review sites, content blogs, and gaming sites saw 50\u201390%+ traffic drops with virtually no recovery path (https://searchengineland.com/impact-of-the-google-september-2023-helpful-content-was-big-for-the-seo-industry-432751)"
            "||Travel sites were among the hardest hit; sites with 90%+ visibility drops frequently had high AI-generated content scores (some as high as 91%) (https://www.amsive.com/insights/seo/googles-helpful-content-update-ranking-system-what-happened-and-what-changed-in-2024/)"
            "||As of March 2024, there were no known significant recoveries; Glenn Gabe tracked 400+ affected sites and only 22% saw even a 20% improvement by August 2024, with full recovery being an anomaly (https://www.seroundtable.com/google-helpful-content-update-recovery-data-38358.html)"
            "||The classifier operated at the site level, not the page level, meaning a single section of unhelpful content could suppress the entire domain's rankings (https://searchengineland.com/google-september-2023-helpful-content-system-update-rolling-out-431978)"
            "||Common traits of affected sites: excessive ads disrupting user experience, excessive affiliate links without substantial content, insufficient E-E-A-T signals, and attempts to cover every topic within a niche without real expertise (https://searchengineland.com/google-helpful-content-updates-survive-thrive-432843)"
            "||Recovery required sweeping content strategy changes rather than quick technical fixes; many site owners were advised to prune low-quality content aggressively (https://searchengineland.com/google-helpful-content-updates-survive-thrive-432843)"
        ),
        "recovery_time": "Months\u2013years; many sites never fully recovered",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "8/22/23",
        "update_name": "August 2023 Core Update",
        "update_type": "Core Update",
        "description": "Late summer core update with ranking volatility",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, E-E-A-T, page experience",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-releases-august-2023-broad-core-update-431043",
        "insights": (
            "Reddit was the dominant winner with +183 visibility points (+64.68%); UGC sites as a category saw the greatest visibility increase despite only four sites qualifying (https://www.amsive.com/insights/seo/google-august-2023-core-update-winners-losers-analysis/)"
            "||WebMD was the biggest health winner (+42 visibility points, +20%); NIH and government health sites also gained substantially (https://www.amsive.com/insights/seo/google-august-2023-core-update-winners-losers-analysis/)"
            "||Major news publishers including the New York Times, Washington Post, and the Guardian saw declines despite high E-E-A-T signals (https://www.amsive.com/insights/seo/google-august-2023-core-update-winners-losers-analysis/)"
            "||Music, lyrics, and entertainment sites that gained in March 2023 had those gains reversed in August (https://searchengineland.com/how-the-august-2023-google-core-update-compared-to-march-2023-core-updates-431851)"
            "||Universities and education sites saw broad increases; official government sites from the US and abroad gained massively (https://www.amsive.com/insights/seo/google-august-2023-core-update-winners-losers-analysis/)"
        ),
        "recovery_time": "2\u20133 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "4/12/23",
        "update_name": "April 2023 Reviews Update",
        "update_type": "Reviews Update",
        "description": "Product review update expanded to all review types",
        "typical_impact": "Review page rankings",
        "affected_factors": "Review depth, evidence, comparisons",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-releases-april-2023-reviews-update-395561",
        "insights": (
            "First reviews update to target all review types, not just product reviews: services, businesses, destinations, and media reviews were now evaluated (https://searchengineland.com/google-releases-april-2023-reviews-update-395561)"
            "||More volatile than the February 2023 update: 72% of rankings were affected vs. 49% in February, according to Semrush and Rank Ranger (https://searchengineland.com/googles-april-2023-reviews-update-was-more-volatile-than-the-previous-product-reviews-update-data-providers-say-398825)"
            "||The update leaned heavily on signals of experience; Google documentation encouraged publishers to demonstrate evidence that products were handled, tested, used, and measured (https://www.amsive.com/insights/seo/googles-newest-reviews-update-elevates-real-life-experience/)"
            "||Rollout took 13 days (Apr 12\u201325) (https://searchengineland.com/google-april-2023-reviews-update-is-finished-rolling-out-395916)"
        ),
        "recovery_time": "2\u20133 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "3/15/23",
        "update_name": "March 2023 Core Update",
        "update_type": "Core Update",
        "description": "Spring core update with broad impact",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, authority, user signals",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-releases-march-2023-broad-core-update-394316",
        "insights": (
            "eCommerce and shopping sites were the biggest winning category; direct hotel brand sites like IHG, Hilton, Marriott, and Four Seasons gained at the expense of travel affiliates (https://www.amsive.com/insights/seo/googles-march-2023-core-update-winners-losers-analysis/)"
            "||8.7% of top 10 results were pages that previously ranked beyond position 20, indicating significant new entries into top rankings (https://searchengineland.com/how-the-march-2023-google-core-update-compared-to-previous-core-updates-394995)"
            "||Google's newly added 'Experience' signal (E-E-A-T, announced December 2022) appeared to play a major role, with sites showing clear evidence of experience in writing style and named authors gaining visibility (https://www.amsive.com/insights/seo/googles-march-2023-core-update-winners-losers-analysis/)"
            "||Amazon lost 13.84% visibility; Zara dropped 24% and Expedia UK dropped 20.60% (https://www.amsive.com/insights/seo/googles-march-2023-core-update-winners-losers-analysis/)"
            "||Rollout lasted 13 days and 7 hours; the update was considered big with significant volatility across many verticals (https://searchengineland.com/google-march-2023-broad-core-update-done-rolling-out-394724)"
        ),
        "recovery_time": "2\u20133 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "2/21/23",
        "update_name": "February 2023 Product Reviews Update",
        "update_type": "Reviews Update",
        "description": "Final standalone product reviews update before system was folded into core updates",
        "typical_impact": "Product review rankings",
        "affected_factors": "Review quality, first-hand experience, detailed analysis",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-releases-february-2023-product-reviews-update-393426",
        "insights": (
            "This was the last product-reviews-only update; subsequent reviews updates expanded to all review types (https://searchengineland.com/google-algorithm-updates-2023-recap-435846)"
            "||49% of rankings were affected, moderate compared to the 72% affected by the April 2023 reviews update that followed (https://searchengineland.com/googles-april-2023-reviews-update-was-more-volatile-than-the-previous-product-reviews-update-data-providers-say-398825)"
            "||Sites with first-hand product experience and detailed analysis continued to be rewarded over thin affiliate content (https://searchengineland.com/google-releases-february-2023-product-reviews-update-393426)"
        ),
        "recovery_time": "2\u20133 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "12/14/22",
        "update_name": "December 2022 Link Spam Update",
        "update_type": "Spam Update",
        "description": "SpamBrain AI targeting unnatural links",
        "typical_impact": "Link-based penalties",
        "affected_factors": "Link schemes, paid links, PBNs",
        "confirmed": "Yes",
        "reference_url": "https://developers.google.com/search/blog/2022/12/december-22-link-spam-update",
        "insights": (
            "First time Google used SpamBrain AI to both detect sites buying links and identify sites created specifically for the purpose of passing outgoing links (https://searchengineland.com/google-releases-december-2022-link-spam-update-390336)"
            "||The update neutralized unnatural links rather than penalizing sites directly, removing any ranking signals previously passed through those links (https://searchengineland.com/google-december-2022-link-spam-update-done-rolling-out-390572)"
            "||The rollout lasted nearly a month (Dec 14 \u2013 Jan 12, 2023); sites that relied on link building schemes saw significant impact (https://www.seroundtable.com/google-december-2022-link-spam-update-impact-34593.html)"
        ),
        "recovery_time": "4\u20135 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "12/5/22",
        "update_name": "December 2022 Helpful Content Update",
        "update_type": "Helpful Content Update (HCU)",
        "description": "Expansion of helpful content system",
        "typical_impact": "Site-wide content evaluation",
        "affected_factors": "Content helpfulness, search-focused content, user value",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-helpful-content-system-update-rolling-out-now-390047",
        "insights": (
            "Less impactful than the first helpful content update; the rollout did not feel widespread compared to core updates or product review updates (https://searchengineland.com/ranking-data-during-the-december-2022-google-helpful-content-update-and-link-spam-update-390620)"
            "||Coincided with Google changing E-A-T to E-E-A-T, adding 'Experience' as a new quality signal in the Search Quality Rater Guidelines (https://searchengineland.com/google-algorithm-updates-2022-in-review-core-updates-product-reviews-helpful-content-updates-spam-updates-and-beyond-390573)"
            "||The rollout lasted 38 days (Dec 5 \u2013 Jan 12, 2023), the longest of any HCU iteration (https://searchengineland.com/googles-december-2022-helpful-content-and-link-spam-update-still-rolling-out-391120)"
            "||Sites that had avoided impact from the August 2022 HCU began feeling effects in December, suggesting the classifier was broadened (https://www.amsive.com/insights/seo/how-googles-latest-helpful-content-system-update-is-impacting-serps/)"
        ),
        "recovery_time": "5\u20136 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "10/19/22",
        "update_name": "October 2022 Spam Update",
        "update_type": "Spam Update",
        "description": "Broad spam update using SpamBrain",
        "typical_impact": "Penalties for spam tactics",
        "affected_factors": "Multiple spam types, thin content, hidden text",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-releases-october-2022-spam-update-388880",
        "insights": (
            "A broad SpamBrain-powered update targeting multiple spam types including thin content and hidden text (https://searchengineland.com/google-releases-october-2022-spam-update-388880)"
            "||The update was global and impacted search results in all languages (https://searchengineland.com/google-releases-october-2022-spam-update-388880)"
            "||Rolled out quickly; sites engaging in clear spam practices saw immediate visibility drops (https://searchengineland.com/google-releases-october-2022-spam-update-388880)"
        ),
        "recovery_time": "None found",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "9/20/22",
        "update_name": "September 2022 Product Reviews Update",
        "update_type": "Reviews Update",
        "description": "Third product reviews update refining how Google evaluates review content",
        "typical_impact": "Product review rankings",
        "affected_factors": "Review depth, original research, quantitative measurements",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-releases-september-2022-product-reviews-update-387293",
        "insights": (
            "Rolled out concurrently with the September 2022 Core Update and shortly after the Helpful Content Update, making it the third major update in rapid succession (https://www.amsive.com/insights/seo/winners-losers-of-the-september-2022-core-update-product-reviews-update/)"
            "||Sites were rewarded for quantitative measurements, original research, and visual proof of product experience (https://searchengineland.com/google-releases-september-2022-product-reviews-update-387293)"
            "||The stacking of three updates in August\u2013September 2022 made it nearly impossible to isolate individual update effects (https://www.amsive.com/insights/seo/winners-losers-of-the-september-2022-core-update-product-reviews-update/)"
        ),
        "recovery_time": "None found",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "9/12/22",
        "update_name": "September 2022 Core Update",
        "update_type": "Core Update",
        "description": "Second September update with significant impact",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, E-A-T, relevance",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-releases-september-2022-broad-core-update-387857",
        "insights": (
            "Significantly weaker overall than the May 2022 core update; it hit fast but was less impactful (https://searchengineland.com/googles-september-2022-core-update-hit-fast-but-was-less-significant-than-previous-updates-388088)"
            "||Wiktionary saw a significant visibility boost while yourdictionary.com and Merriam-Webster were among the biggest losers (https://www.amsive.com/insights/seo/winners-losers-of-the-september-2022-core-update-product-reviews-update/)"
            "||Amazon was the biggest eCommerce winner, but other giants like Walmart, Target, and eBay that gained in previous updates saw declines (https://www.amsive.com/insights/seo/winners-losers-of-the-september-2022-core-update-product-reviews-update/)"
        ),
        "recovery_time": "2\u20133 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "8/25/22",
        "update_name": "August 2022 Helpful Content Update",
        "update_type": "Helpful Content Update (HCU)",
        "description": "First helpful content update targeting search-first content",
        "typical_impact": "Site-wide content evaluation",
        "affected_factors": "Search-first content, thin content, content farms",
        "confirmed": "Yes",
        "reference_url": "https://developers.google.com/search/blog/2022/08/helpful-content-update",
        "insights": (
            "The first-ever Helpful Content Update; it evaluated entire websites rather than individual pages, meaning unhelpful content in one section could suppress the whole domain (https://developers.google.com/search/blog/2022/08/helpful-content-update)"
            "||Initial impact was muted and disappointed SEOs who expected a massive shakeup; the real effects appeared more gradually over the following months, especially after the December 2022 iteration (https://www.amsive.com/insights/seo/how-googles-latest-helpful-content-system-update-is-impacting-serps/)"
            "||Travel sites with thin, generic content were among the earliest and most visible casualties, particularly those creating mass pages about cities using aggregated information without original insights (https://www.amsive.com/insights/seo/googles-helpful-content-update-to-devalue-search-engine-first-content-and-elevate-authentic-expert-voices-in-search/)"
            "||Sites with thousands of articles covering every topic in their niche without real experience, expertise, authority, or trust were most affected (https://www.amsive.com/insights/seo/how-googles-latest-helpful-content-system-update-is-impacting-serps/)"
            "||Rollout lasted 15 days (Aug 25 \u2013 Sep 9); English-language content was targeted first, with other languages added in later iterations (https://www.semrush.com/blog/helpful-content/)"
        ),
        "recovery_time": "Weeks for rollout; months\u2013years for impacted sites",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "7/27/22",
        "update_name": "July 2022 Product Reviews Update",
        "update_type": "Reviews Update",
        "description": "Second product reviews update of 2022 with expanded evaluation criteria",
        "typical_impact": "Product review rankings",
        "affected_factors": "Evidence of experience, visual proof, expert analysis",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-releases-july-2022-product-reviews-update-386763",
        "insights": (
            "Expanded signals for visual proof of product experience: photos, videos, and screenshots showing actual product testing were rewarded (https://searchengineland.com/google-releases-july-2022-product-reviews-update-386763)"
            "||Expert analysis and first-hand experience became more heavily weighted compared to rehashed manufacturer specifications (https://www.amsive.com/insights/seo/googles-2021-2022-product-reviews-updates-what-happened/)"
            "||This was the fourth product reviews update overall and the second of 2022, continuing a pattern of rapid iteration on review quality signals (https://searchengineland.com/google-releases-july-2022-product-reviews-update-386763)"
        ),
        "recovery_time": "None found",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "5/25/22",
        "update_name": "May 2022 Core Update",
        "update_type": "Core Update",
        "description": "Broad core update with E-A-T focus",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "E-A-T, content quality, user experience",
        "confirmed": "Yes",
        "reference_url": "https://developers.google.com/search/blog/2022/05/may-2022-core-update",
        "insights": (
            "A significant and fast-hitting update; data providers agreed it was one of the bigger core updates in 2022 (https://searchengineland.com/googles-may-2022-core-update-impact-was-mixed-but-it-touched-down-fast-and-seemed-very-large-385479)"
            "||Health, medical, nutrition, and wellness sites previously hit by core updates saw some recoveries, including Examine.com, draxe.com, dietdoctor.com, psychcentral.com, and bodybuilding.com (https://www.amsive.com/insights/seo/google-may-2022-core-update-winners-losers-analysis/)"
            "||The update touched down fast but impact was mixed across sectors, with some categories seeing big wins and others barely moving (https://searchengineland.com/googles-may-2022-core-update-impact-was-mixed-but-it-touched-down-fast-and-seemed-very-large-385479)"
        ),
        "recovery_time": "2\u20133 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "3/23/22",
        "update_name": "March 2022 Product Reviews Update",
        "update_type": "Reviews Update",
        "description": "Second product reviews update strengthening original content signals",
        "typical_impact": "Product review rankings",
        "affected_factors": "Original content, in-depth analysis, product expertise",
        "confirmed": "Yes",
        "reference_url": "https://developers.google.com/search/blog/2022/03/product-review-ranking-one-year-on",
        "insights": (
            "Introduced new ranking criteria including evidence of products being physically tested, unique quantitative measurements, and pros/cons lists with detailed justification (https://searchengineland.com/google-releases-march-2022-product-reviews-update-with-additional-ranking-criteria-382995)"
            "||Google explicitly documented new best practices for review content, including demonstrating what a product is physically like and what differentiates it from competitors (https://developers.google.com/search/blog/2022/03/product-review-ranking-one-year-on)"
            "||One year after the first product reviews update, Google continued to refine signals targeting thin affiliate content that lacked genuine product experience (https://developers.google.com/search/blog/2022/03/product-review-ranking-one-year-on)"
        ),
        "recovery_time": "None found",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "12/1/21",
        "update_name": "December 2021 Product Reviews Update",
        "update_type": "Reviews Update",
        "description": "Second product reviews update expanding signals for high-quality review content",
        "typical_impact": "Product review rankings",
        "affected_factors": "Original research, expert analysis, product comparison depth",
        "confirmed": "Yes",
        "reference_url": "https://developers.google.com/search/blog/2021/12/product-reviews-update-and-your-site",
        "insights": (
            "Bigger and more volatile than the April 2021 product reviews update; the update remained volatile throughout its entire rollout (https://searchengineland.com/googles-december-2021-product-reviews-update-was-bigger-than-the-april-product-reviews-update-say-data-providers-377056)"
            "||The categories most affected were finance, law and government, jobs and education, autos and vehicles, and health (https://www.amsive.com/insights/seo/googles-2021-2022-product-reviews-updates-what-happened/)"
            "||Many keywords for which sites lost page 1 rankings did not include the word 'best' and were simply transactional head terms without modifiers (https://www.searchenginejournal.com/google-product-reviews-winners-losers/403301/)"
        ),
        "recovery_time": "None found",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "11/17/21",
        "update_name": "November 2021 Core Update",
        "update_type": "Core Update",
        "description": "Late year core update with broad impact",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, authority, relevance",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-november-2021-core-update-rolling-out-today-376124",
        "insights": (
            "The health industry was hit hardest by this update, more than any other vertical (https://searchengineland.com/google-algorithm-updates-2021-in-review-core-updates-product-reviews-page-experience-and-beyond-378017)"
            "||Hit almost every vertical harder than the previous July 2021 core update (https://searchengineland.com/google-algorithm-updates-2021-in-review-core-updates-product-reviews-page-experience-and-beyond-378017)"
            "||Rollout lasted 13 days (Nov 17\u201330) (https://searchengineland.com/google-algorithm-updates-2021-in-review-core-updates-product-reviews-page-experience-and-beyond-378017)"
        ),
        "recovery_time": "2\u20133 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "11/3/21",
        "update_name": "November 2021 Spam Update",
        "update_type": "Spam Update",
        "description": "Spam update targeting various webspam tactics across multiple languages",
        "typical_impact": "Penalties for spam tactics",
        "affected_factors": "Link spam, content spam, multiple languages",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-releases-november-2021-spam-update-375776",
        "insights": (
            "Rolled out in 8 days (Nov 3\u201311), making it one of the faster spam updates (https://searchengineland.com/google-november-spam-update-is-fully-rolled-out-375966)"
            "||Targeted spam across multiple languages, not just English (https://searchengineland.com/google-releases-november-2021-spam-update-375776)"
            "||The update appeared relatively contained, primarily affecting sites engaging in clear spam practices (https://www.seroundtable.com/google-november-2021-spam-update-32365.html)"
        ),
        "recovery_time": "1\u20132 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "7/26/21",
        "update_name": "July 2021 Link Spam Update",
        "update_type": "Spam Update",
        "description": "Dedicated link spam update using SpamBrain to neutralize unnatural links",
        "typical_impact": "Link-based penalties",
        "affected_factors": "Link schemes, paid links, link spam",
        "confirmed": "Yes",
        "reference_url": "https://developers.google.com/search/blog/2021/07/link-tagging-and-link-spam-update",
        "insights": (
            "Introduced SpamBrain for link spam detection; the AI system could identify both sites buying links and sites created specifically to sell links (https://developers.google.com/search/blog/2021/07/link-tagging-and-link-spam-update)"
            "||Took about four weeks to fully roll out (Jul 26 \u2013 Aug 24), double the expected two-week timeframe (https://searchengineland.com/google-algorithm-updates-2021-in-review-core-updates-product-reviews-page-experience-and-beyond-378017)"
            "||Unnatural links were neutralized (their ranking signals removed) rather than sites being directly penalized (https://developers.google.com/search/blog/2021/07/link-tagging-and-link-spam-update)"
        ),
        "recovery_time": "4 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "7/1/21",
        "update_name": "July 2021 Core Update",
        "update_type": "Core Update",
        "description": "Two-part summer core update",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, E-A-T, user signals",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-july-2021-core-update-rolling-out-now-350176",
        "insights": (
            "Rolled out quickly in 11 days (Jul 1\u201312); only 15 of the top 200 most impacted domains overlapped with the June 2021 core update, suggesting different algorithmic signals (https://www.amsive.com/insights/seo/google-july-2021-core-update-winners-losers-analysis/)"
            "||'Alternative and Natural Medicine' sites were among the biggest percentage losers, a topic area frequently discussed in relation to E-A-T standards (https://www.amsive.com/insights/seo/google-july-2021-core-update-winners-losers-analysis/)"
            "||This was the second part of a two-phase summer core update series (https://searchengineland.com/googles-july-2021-core-update-rolled-out-quickly-here-is-what-the-data-providers-saw-350243)"
        ),
        "recovery_time": "2 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "6/23/21",
        "update_name": "June 2021 Spam Update",
        "update_type": "Spam Update",
        "description": "First of two consecutive spam updates targeting webspam in search results",
        "typical_impact": "Penalties for spam tactics",
        "affected_factors": "Content spam, link spam, various spam techniques",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-search-releases-spam-update-349848",
        "insights": (
            "First of two consecutive spam updates released within days of each other (June 23 and June 28) (https://searchengineland.com/google-search-releases-spam-update-349848)"
            "||The twin spam updates occurred during a very active period that also included the June Core Update and the Page Experience Update (https://searchengineland.com/google-algorithm-updates-2021-in-review-core-updates-product-reviews-page-experience-and-beyond-378017)"
            "||Sites engaging in various spam techniques saw penalties, but the overall impact was overshadowed by the concurrent core and page experience updates (https://searchengineland.com/google-search-releases-spam-update-349848)"
        ),
        "recovery_time": "None found",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "6/15/21",
        "update_name": "June 2021 Page Experience Update",
        "update_type": "Page Experience",
        "description": "Core Web Vitals becomes ranking factor",
        "typical_impact": "Page-level ranking changes",
        "affected_factors": "LCP, FID/INP, CLS, mobile friendliness, HTTPS",
        "confirmed": "Yes",
        "reference_url": "https://developers.google.com/search/blog/2021/04/more-details-page-experience",
        "insights": (
            "Core Web Vitals (LCP, FID, CLS) became official ranking signals, but Google emphasized this was a lightweight factor compared to content relevance (https://searchengineland.com/google-page-experience-update-now-slowly-rolling-out-349649)"
            "||The full rollout did not complete until end of August 2021, taking about 2.5 months from mid-June (https://searchengineland.com/page-experience-seo-448564)"
            "||Google explicitly stated sites should not expect drastic ranking changes from this update alone; page experience is one of many factors (https://searchengineland.com/google-page-experience-update-rolls-out-just-as-core-update-finishes-wednesdays-daily-brief-349658)"
            "||The update launched just as the June 2021 Core Update finished rolling out, making it difficult to isolate page experience effects (https://searchengineland.com/google-page-experience-update-rolls-out-just-as-core-update-finishes-wednesdays-daily-brief-349658)"
        ),
        "recovery_time": "Gradual rollout over 2\u20133 months",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "6/2/21",
        "update_name": "June 2021 Core Update",
        "update_type": "Core Update",
        "description": "First part of two-part summer core update with broad ranking impact",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, E-A-T, relevance",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-june-2021-core-update-rolling-out-349121",
        "insights": (
            "First part of a two-phase core update; Google pre-announced a second part would follow in July (https://searchengineland.com/google-june-2021-core-update-rolling-out-349121)"
            "||Top losing domains included HuffPost, Lifehacker, Vanity Fair, and moneyunder30.com; winners included IMDB, Cambridge.org, and Amazon (https://www.amsive.com/insights/seo/winners-and-losers-of-googles-june-2021-core-update/)"
            "||Health, autos, pets & animals, science, and travel were the most affected categories (https://www.amsive.com/insights/seo/winners-and-losers-of-googles-june-2021-core-update/)"
            "||The rollout was slow, taking about 10 days to complete (Jun 2\u201312) (https://searchengineland.com/googles-june-2021-core-update-was-slow-to-roll-out-here-is-what-the-data-providers-saw-349349)"
        ),
        "recovery_time": "2 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "4/8/21",
        "update_name": "April 2021 Product Reviews Update",
        "update_type": "Reviews Update",
        "description": "First dedicated product review update",
        "typical_impact": "Product review rankings",
        "affected_factors": "In-depth analysis, expert insights, original content",
        "confirmed": "Yes",
        "reference_url": "https://developers.google.com/search/blog/2021/04/product-reviews-update",
        "insights": (
            "The first-ever Product Reviews Update, designed to reward reviews that share 'in-depth research rather than thin content that simply summarizes a bunch of products' (https://developers.google.com/search/blog/2021/04/product-reviews-update)"
            "||Impact was significant for affected sites but not as broad as a core update; affiliate and review sites that relied on manufacturer specs without original testing were hit hardest (https://searchengineland.com/google-product-reviews-algorithm-update-was-big-but-not-like-a-core-update-say-data-providers-347888)"
            "||Google laid out new expectations: show evidence of physical product testing, provide quantitative measurements, and explain what makes a product different from competitors (https://developers.google.com/search/blog/2021/04/product-reviews-update)"
            "||Rollout took approximately two weeks (Apr 8\u201322) (https://searchengineland.com/google-product-reviews-algorithm-update-was-big-but-not-like-a-core-update-say-data-providers-347888)"
        ),
        "recovery_time": "2 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "12/3/20",
        "update_name": "December 2020 Core Update",
        "update_type": "Core Update",
        "description": "Year-end broad algorithm update",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, E-A-T, user experience",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-december-2020-core-update-rolling-out-344333",
        "insights": (
            "Possibly even bigger than the May 2020 core update, which was already considered an 'absolute monster'; this was the largest update of the year (https://searchengineland.com/googles-december-2020-core-update-was-big-even-bigger-than-may-2020-says-data-providers-344429)"
            "||Clear ranking shifts in E-A-T-sensitive areas: music, health, finance, news, and eCommerce all showed major movement (https://searchengineland.com/some-early-observations-on-the-google-december-core-update-345064)"
            "||Came after a seven-month gap since the May 2020 update, the longest stretch without a confirmed core update at that time (https://searchengineland.com/google-algorithm-updates-2020-in-review-core-updates-passage-indexing-and-page-experience-345070)"
            "||Amsive tracked over 1,000 winners and losers across multiple categories (https://www.amsive.com/insights/seo/1000-winners-and-losers-of-the-december-2020-google-core-algorithm-update/)"
        ),
        "recovery_time": "2\u20134 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "5/4/20",
        "update_name": "May 2020 Core Update",
        "update_type": "Core Update",
        "description": "Major core update during pandemic",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, YMYL content, authority",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-may-2020-core-update-rolling-out-today-334128",
        "insights": (
            "Described as an 'absolute monster' and bigger than the January 2020 update; it rolled out over two weeks (May 4\u201318) (https://searchengineland.com/googles-may-2020-core-update-was-big-and-broad-search-data-tools-show-334393)"
            "||Travel, real estate, health, pets & animals, and people & society were the most impacted industries (https://searchengineland.com/googles-may-2020-core-update-was-big-and-broad-search-data-tools-show-334393)"
            "||Many believed the update targeted health misinformation during COVID; YMYL health content with strong E-A-T saw gains while lower-authority health sites declined (https://www.searchenginejournal.com/google-update-analysis/367604/)"
            "||Notable losers included LinkedIn, NY Post, Eventbrite, and AllMusic; winners included local directory sites and press release platforms (https://www.seroundtable.com/impacted-google-may-2020-core-update-29410.html)"
            "||The COVID-19 pandemic context amplified the update's focus on authoritative health information; the Amsive analysis showed Google prioritizing verified health sources (https://www.amsive.com/insights/seo/impact-of-the-coronavirus-covid-19-on-google-organic-search-visibility/)"
        ),
        "recovery_time": "2\u20134 weeks",
        "rep_quote": "",
        "rep_name": "",
        "citation_url": "",
    },
    {
        "date": "1/13/20",
        "update_name": "January 2020 Core Update",
        "update_type": "Core Update",
        "description": "First core update of 2020 with broad ranking impact across many verticals",
        "typical_impact": "Site-wide ranking changes",
        "affected_factors": "Content quality, E-A-T, relevance",
        "confirmed": "Yes",
        "reference_url": "https://searchengineland.com/google-january-2020-core-update-begins-rolling-out-327501",
        "insights": (
            "A big update impacting a large number of sites globally; all data providers agreed on its significance (https://searchengineland.com/the-latest-data-on-the-january-2020-google-core-update-327683)"
            "||Most volatile categories included sports, news, online communities, games, arts & entertainment, and finance (https://searchengineland.com/the-latest-data-on-the-january-2020-google-core-update-327683)"
            "||The update was global, not specific to any region, language, or category of websites (https://searchengineland.com/the-latest-data-on-the-january-2020-google-core-update-327683)"
            "||Most of the rollout completed within three days (Jan 13\u201316) (https://searchengineland.com/the-latest-data-on-the-january-2020-google-core-update-327683)"
        ),
        "recovery_time": "1\u20132 weeks",
        "rep_quote": "It's not something that requires a site to kind of wait for the next update to have a chance to be seen differently. They can continue working on things and things can improve over time.",
        "rep_name": "John Mueller",
        "citation_url": "https://searchengineland.com/google-says-you-can-recover-from-core-updates-without-a-new-core-update-340396",
    },
]


# ========================================================================
#   Write CSV
# ========================================================================

def write_csv():
    """Writes the algorithm updates data to CSV."""

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(updates)

    print(f"Wrote {len(updates)} updates to {OUTPUT_PATH}")


if __name__ == "__main__":
    write_csv()
