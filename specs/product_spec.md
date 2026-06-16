# Auditmaton for Site Audits — Master Product Spec

## Product Overview

Auditmaton for Site Audits is a professional-grade site audit application for SEO practitioners and agencies. Users upload crawl data, complete an intake form, and work through a structured audit framework built around five core actions (the `-ate` framework). The output is a polished, exportable audit document built in a canvas interface.

**Target users:** SEO professionals, agencies, and in-house SEO teams. Minimum audit value in the market: $5k. No free tier.

**Tech stack:** Flask (Python), Anthropic API (claude-haiku for AI features), Plotly for visualizations, SQLite or PostgreSQL.

## The `-ate` Framework

Every audit check contains up to five action sections:

| Action | Description | Requires Crawl Data? | Requires AI? |
|--------|-------------|----------------------|--------------|
| **Educate** | Plain English explanation of the check, why it matters, analogies tailored to site type. Includes training mode toggle. | No | No |
| **Investigate** | Step-by-step instructions to run the check manually, filtered by tools the user has access to, tabbed by tool. | No | No |
| **Evaluate** | Analyzes uploaded crawl data, surfaces findings, shows affected URL sample (max 5 inline), flags issues. | Yes | No |
| **Validate** | Cross-references findings against Google algorithm updates CSV. Surfaces relevant updates with links. | Optional | Optional |
| **Generate** | Produces audit narrative text with dynamic variables + Plotly chart if applicable. Adds block to Canvas. | Yes | Yes (text) / No (charts) |

## Subscription Tiers

No free tier. Three paid tiers:

| Feature | Base | Viz Tier | AI Tier |
|---------|------|----------|---------|
| All `-ate` content (Educate, Investigate, Evaluate, Validate) | ✓ | ✓ | ✓ |
| Affected URL sample (max 5 rows inline) | ✓ | ✓ | ✓ |
| Charts | Ghost only (watermark, no axes/data labels) | ✓ Full | ✓ Full |
| CSV export (all affected URLs) | ✗ | ✓ | ✓ |
| AI Generate (narrative text) | ✗ | ✗ | ✓ |
| AI contextual queries | ✗ | ✗ | ✓ |
| Token budget | — | — | Annual allocation + top-ups |

**Ghost chart behavior:** Renders actual chart shape with real proportions but applies semi-transparent overlay + watermark. Axes and data labels hidden. Upgrade CTA overlaid. Generates mid-audit to maximize conversion intent. On upgrade, all ghost charts across completed checks unlock instantly.

**Token model:** Annual allocation (not monthly — audits are feast/famine). Top-up bundles available so users are never stranded mid-audit. Subtle usage gauge in nav/sidebar — visible on demand, not anxiety-inducing. No monthly rollover pressure.

**Export upgrade unlock:** CSV export buttons are visible but grayed out on Base tier. Unlock immediately on upgrade to Viz Tier.

## Intake Form

Sexy, Typeform-style, one question at a time. Every answer does real work.

### Question 1 — Site Type (multi-select checkboxes)
Drives site-type content overlays throughout all checks.

| Site Type | Conditional Sections Unlocked |
|-----------|-------------------------------|
| Ecommerce | Shopping section |
| Publishing / Blog | — |
| Local Business | Local section |
| Educational | — |
| Nonprofit | — |
| Professional Services | — |
| Healthcare / Wellness | — |
| Events | — |
| Recipe | — |
| Membership / Community | — |

Multi-select supported (e.g., Under Armour = Ecommerce + Blog). When multiple site types selected, Educate sections show tabs for each relevant overlay.

### Question 2 — Site Size
Approximate page count or traffic tier. Unlocks **Crawl Budget** subcheck for large sites.

### Question 3 — Crawl Tool Used
Drives column mapping screen. Options: Screaming Frog, Sitebulb, Ahrefs, Semrush, Moz, Other.

### Question 4 — SEO Tools Available (multi-select checkboxes)
Filters Investigate instructions to show only relevant tool tabs.
Options: Google Search Console, Google Analytics, Screaming Frog, Ahrefs, Semrush, Moz, Sitebulb, Other/None.

### Question 5 — Server Log Access
Yes / No. If yes, unlocks **Log File Analysis** as subcheck 11 in the Crawl section. Signals sophistication to enterprise and agency users.

### Question 6 — Brand Colors
Primary and secondary hex values. Stored in settings, referenced as `brand_primary` / `brand_secondary` variables in all Plotly chart configs. Change once, updates everywhere.

### Question 8 — Tag Manager
Do you use a tag manager? Yes / No. If yes: which one?
Options: Google Tag Manager, Tealium, Adobe Experience Platform Launch, Ensighten, Segment, Other.
Unlocks tag-manager-specific Investigate steps for relevant checks across Crawl, Content, Mobile, and AI/GEO sections.

Key checks where tag manager context matters:
- JavaScript-based redirects or canonicals invisible to crawlers
- Hreflang or schema implemented via tag manager (high misconfiguration risk)
- GTM container bloat contributing to CWV / page speed issues
- GA4 or analytics implementation verification
- Singular: "I found..." / "I recommend..."
- Plural: "We found..." / "We recommend..."
Stored in settings. Injected into all narrative templates via `{{voice_found}}` / `{{voice_recommend}}` variables.

## Column Mapping

After intake, user maps their crawl file columns to canonical internal keys.

Each column has three values:
1. **Canonical key** — internal reference used in all code (e.g., `meta_title`, `status_code`). Never changes.
2. **User's crawl file header** — what their file actually calls it (e.g., `response_code`, `title_tag_1`). Set during mapping.
3. **Display label** — cosmetic name shown in UI, tables, and chart axes. Defaults provided (e.g., "Meta Title", "Status Code"). User can customize.

If a check's required column is not mapped, the check degrades gracefully with a message: "Insufficient data — see Investigate for manual instructions."

## Architecture

### JSON File Structure (lazy loading)
JSON is split by section and site type to keep the app responsive. Only relevant files are loaded per audit.

```
/content
  /crawl
    crawl_base.json
    crawl_ecommerce.json
    crawl_publishing.json
    crawl_local.json
    ...
  /content
    content_base.json
    content_ecommerce.json
    ...
  /ai_geo
    ai_geo_base.json
    ...
```

At intake, app fetches only: base file + overlays matching selected site types.

### Master Check Schema Fields

```json
{
  "id": "unique-slug",
  "title": "Display title of the check",
  "category": "crawl",
  "subcategory": "robots_txt",
  "impact_score": 1-5,
  "impact_rationale": "One-line explanation of score",
  "has_chart": true/false,
  "has_code_snippet": true/false,
  "has_export": true/false,
  "image_count": 0,
  "conditional": null or ["ecommerce", "publishing"],
  "column_dependencies": [
    {
      "canonical_key": "status_code",
      "display_default": "Status Code",
      "required": true/false
    }
  ],
  "educate": {
    "base": "Universal explanation",
    "site_type_overlays": {
      "ecommerce": "Ecom-specific context",
      "publishing": "Publishing-specific context"
    }
  },
  "investigate": {
    "intro": "Intro text",
    "tools": {
      "free": {
        "manual": { "label": "Manual", "steps": [] },
        "google_search_console": { "label": "GSC", "steps": [] }
      },
      "paid": {
        "screaming_frog": { "label": "Screaming Frog", "steps": [] },
        "screaming_frog_log_analyser": { "label": "Screaming Frog Log File Analyser", "steps": [] },
        "ahrefs": { "label": "Ahrefs", "steps": [] },
        "semrush": { "label": "Semrush", "steps": [] },
        "sitebulb": { "label": "Sitebulb", "steps": [] }
      }
    }
  },
  "evaluate": {
    "logic": "Description of evaluation logic",
    "column_dependencies": ["canonical_key_1", "canonical_key_2"],
    "url_sample": {
      "max_rows": 5,
      "columns": ["url", "status_code", "issue"],
      "issue_label": "Label for issue column"
    },
    "export_available": true/false,
    "fallback_message": "Shown when required columns are missing"
  },
  "validate": {
    "impactful_updates": [
      {
        "update_title": "Update name",
        "update_date": "mm/dd/yyyy",
        "update_source": "Google",
        "update_summary": "Brief summary",
        "update_link": "https://..."
      }
    ]
  },
  "visualizations": [
    {
      "type": "bar/histogram/scatter/donut/heatmap/wordcloud",
      "chart_title": "Title",
      "metrics": ["metric_column"],
      "dimensions": ["dimension_column"],
      "gridlines": false,
      "colors": {
        "primary": "brand_primary",
        "secondary": "brand_secondary"
      }
    }
  ],
  "generate": {
    "narrative_template": "{{voice_found}} that... {{site_name}}... {{affected_url_count}}...",
    "code_snippet": {
      "label_before": "Label",
      "before": "<!-- broken code -->",
      "label_after": "Label",
      "after": "<!-- fixed code -->"
    }
  },
  "learn_more": [
    {
      "source_type": "Search Engine | Industry Publication | Blog Post | Other",
      "source_title": "Page title",
      "source_url": "https://...",
      "publish_date": "mm/dd/yyyy"
    }
  ]
}
```

## UI / Navigation

### Card Grid Navigation
- **Level 1:** Top-level category cards (Crawl, Content, Links, etc.)
- **Level 2:** Subcategory facets in left column (e.g., Robots.txt, XML Sitemap, Indexability), checks populate right panel
- Facets show **issue counts** pulled from crawl data (e.g., "Status Codes (47 issues)") — colored red/amber/green
- No free-standing third level of card drilling

### Check Cards
Each check card displays:
- Title
- Impact score (1–5, colored indicator — reuse ML Model Picker difficulty score UI)
- Chart indicator icon (if `has_chart: true`)
- Export indicator (if `has_export: true`)
- CTAs: **EVALUATE**, **INVESTIGATE**, **GENERATE** (verb-driven, consistent with `-ate` framework)

### Canvas
- Output document built by adding generated blocks
- Blocks: text narrative, Plotly chart, URL sample table, code snippet, learn more
- Drag-and-drop reordering
- Blocks are portable — user can move any generated block to any section
- No rigid section containers — sections are suggestions, not locks

### Training Mode Toggle
- Available in user settings
- ON: Educate sections show full depth, analogies, plain English explanations (for junior SEOs, onboarding)
- OFF: Condensed Educate for experienced practitioners

## Audit Categories & Subcategories

### Universal Sections (all site types)

**1. Crawl**
Robots.txt, XML Sitemap, Indexability, Status Codes, Redirects, Canonicalization, Crawl Depth / Site Architecture, Crawl Budget *(large sites only)*, Pagination, URL Structure, Log File Analysis *(server log access confirmed at intake)*

**2. Content**
Readability, Word Count, Thin Content, Duplicate Content, Content Freshness, Meta Titles, Meta Descriptions, Headings (Hx)

**3. Links**
Internal Links, External Links, Broken Links, Anchor Text, Site Architecture / Link Depth

**4. Media**
Images (Alt Text, File Size, Naming), Video *(conditional: video-heavy sites)*

**5. Mobile**
Mobile Usability, Core Web Vitals (LCP, CLS, INP), Tap Targets / UX, Interstitials

**6. E-E-A-T**
Author Pages & Bios, About / Contact Completeness, Reviews & Testimonials, Entity Establishment, Brand Signals

**7. AI / GEO**
AI Overview Visibility, Entity Optimization, LLM-friendly Structured Data, Featured Snippets, Q&A / FAQ Content, Brand Mentions Across the Web, Generative Crawl Access

### Conditional Sections

**8. Shopping** *(Ecommerce only)*
Product Schema, Review / Rating Markup, Breadcrumb Schema, Faceted Navigation / Crawl Budget, Pagination, Thin Product Pages, Duplicate Content from Variants, Shopping Feed / Merchant Center

**9. Local** *(Local Business only)*
NAP Consistency, Google Business Profile, Local Schema, Local Content

**10. International** *(flagged at intake)*
Hreflang Implementation, URL Structure, Content Localization

## Inline Features Per Check

- **Affected URL sample:** Max 5 rows inline. Columns vary by check. Representative sample.
- **CSV export:** Full affected URL list. Viz Tier+. Export button grayed out on Base.
- **Before/after code snippet:** For technical checks (canonicalization, robots.txt, schema, etc.)
- **Plotly chart:** Inline, generated from crawl data. Ghost version on Base tier.
- **Supplementary images:** `image_count` field. Stored at `/static/images/checks/{check_id}/`. Named `{check-id}-01.jpg` etc.
- **Learn More:** Sourced links rendered as footnotes or collapsible section. Includes source type, title, URL, publish date.
- **Impactful Updates:** Relevant Google algorithm updates surfaced inline with link to read more.

## Dynamic Narrative Variables

All narrative templates use `{{variable}}` syntax resolved at generate time:

| Variable | Source |
|----------|--------|
| `{{voice_found}}` | Intake: "I found" or "We found" |
| `{{voice_recommend}}` | Intake: "I recommend" or "We recommend" |
| `{{site_name}}` | Intake form |
| `{{root_domain}}` | Intake form |
| `{{affected_url_count}}` | Evaluate logic |
| `{{affected_page_types}}` | Evaluate logic |
| `{{affected_patterns}}` | Evaluate logic |
| `{{status_code}}` | Evaluate logic |
| `{{file_size_kb}}` | Evaluate logic |
| `{{size_status}}` | Evaluate logic |
| `{{conflict_summary}}` | Evaluate logic |

## Impact Scoring

- Scale: 1 (low) to 5 (critical)
- Assigned by AI agent pass after JSON content is authored
- Each check includes `impact_score` and `impact_rationale`
- Displayed on check cards as colored indicator (reuse existing UI component)
- Future: agent re-scores quarterly as Google best practices evolve

## Citations & Trust

- All Educate content cites sources via `learn_more` array
- Algorithm updates cite source URL via `impactful_updates`
- AI-generated narrative sections flagged with "AI-assisted analysis based on your crawl data"
- Source types: Search Engine, Industry Publication, Blog Post, Other

## Future / Phase 2 Features

- **404 No More integration** — NLP-based redirect suggestions for broken URLs. Premium add-on.
- **Quotes from industry leaders** — Cherry-pick quotes per check. `"quotes": []` placeholder in schema now.
- **Image library per check** — Supplementary visuals. `image_count` field already in schema.
- **Agent-maintained Investigate steps** — Periodic agent pass checks that tool UIs / steps haven't gone stale.
- **Platform expansion** — Same codebase, new JSON content: Analytics Audit, Accessibility Audit, Market Analysis / Brief Builder tool.

## Settings Stored at Intake

- `brand_primary` — hex color
- `brand_secondary` — hex color
- `narrative_voice` — "singular" or "plural"
- `site_types` — array of selected site types
- `site_size` — page count tier
- `crawl_tool` — tool used for upload
- `seo_tools` — array of available tools
- `server_log_access` — boolean
- `column_map` — object mapping canonical keys to user's file headers and display labels
