# Build the Auditmaton for Site Audits Category Dashboard (Homescreen)

## What This Is

The Category Dashboard is Level 1 of the three-level navigation hierarchy.
It is the first screen users see after completing intake for an audit.
It shows 10 audit category cards with progress indicators and serves as the
primary orientation point throughout the audit process.

Read CLAUDE.md thoroughly before starting. Follow all coding conventions,
directory structure, and naming patterns exactly.


## Reference Architecture

The reference codebase is a production Flask app (AI Timeline) that
establishes all reusable patterns for Auditmaton for Site Audits. Every structural
decision below traces back to working, tested code from that app. Do not
invent new patterns when a reference pattern exists.


## FILE 1: templates/base.html

Adapt the AI Timeline base.html for Auditmaton for Site Audits. Preserve these exact
patterns from the reference:

### Head Section
- Google Tag Manager script block (keep GTM-5FJGP2 as placeholder; Annie
  will update)
- `{% block title %}Auditmaton for Site Audits{% endblock %}`
- Canonical tag placeholder
- Meta description for Auditmaton for Site Audits
- Favicon via `url_for('static', filename='img/favicon.png')`
- Open Graph and Twitter Card meta tags with `{% block %}` overrides for
  og_title, og_description, og_url, og_image, twitter_title, etc.
- `<meta name="author" content="Annie Cushing">`

### CDN Links (keep these exact versions)
- Bootstrap 4.5.2: `https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css`
- Font Awesome 6.5.0: `https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css`
- jQuery 3.6.0 (at bottom of body): `https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js`
- DO NOT include DataTables or Vis Timeline CSS/JS in base.html. Pages that
  need them will load them via `{% block extra_head %}` or `{% block scripts %}`.
- Add Plotly.js CDN in `{% block extra_head %}` only on pages that need charts.

### Custom Stylesheets
- `{{ url_for('static', filename='css/styles.css') }}` — The main app stylesheet
- `{% block extra_head %}{% endblock %}` — For page-specific CSS/JS in head

### Body Structure

```html
<body>
    {# Google Tag Manager noscript fallback #}
    <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-5FJGP2"
    height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>

    <!-- ===================================================================
         Site Header
         =================================================================== -->
    <header class="site-header">
        <div class="{{ self.header_class() if self.header_class is defined else 'wrap' }}">

            {# Logo #}
            <div class="title-area">
                <a href="/dashboard">
                    <img src="{{ url_for('static', filename='img/crawl-canvas-logo.png') }}"
                         alt="Auditmaton for Site Audits Logo" class="header-logo">
                </a>
            </div>

            {# Checkbox-hack hamburger — keep this exact pattern #}
            <input type="checkbox" id="menu-toggle-checkbox" class="hidden">
            <label for="menu-toggle-checkbox" class="menu-toggle"
                   aria-expanded="false">MENU</label>

            {# Primary nav #}
            <nav class="nav-primary">
                <ul class="menu">
                    <li><a href="/dashboard">Dashboard</a></li>
                    <li><a href="/audits">My Audits</a></li>
                    <li><a href="/account">Account</a></li>
                    <li><a href="/help">Help</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <!-- ===================================================================
         Audit Context Bar (only visible when audit is active)
         =================================================================== -->
    {% if active_audit %}
    <div class="audit-context-bar">
        <div class="wrap">
            <span class="audit-context-domain">{{ active_audit.domain }}</span>
            <span class="audit-context-tier tier-{{ active_audit.tier }}">
                {{ active_audit.tier_display }}
            </span>
            {% if active_audit.tier == 'ai' %}
            <span class="audit-context-tokens">
                <i class="fa-solid fa-coins"></i> {{ active_audit.tokens_remaining }} tokens
            </span>
            {% endif %}
        </div>
    </div>
    {% endif %}

    <!-- ===================================================================
         Page Title
         =================================================================== -->
    <div class="entry-header">
        <h1 class="entry-title">{% block page_title %}Dashboard{% endblock %}</h1>
    </div>

    <!-- ===================================================================
         Main Content
         =================================================================== -->
    {% block container %}
    <div class="main-content">
        {# Flash messages #}
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-info">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>
    {% endblock %}

    <!-- ===================================================================
         Footer
         =================================================================== -->
    <footer class="footer">
        <nav class="footer-nav">
            <a href="/terms" class="footer-link">Terms</a>
            <a href="/privacy" class="footer-link">Privacy</a>
            <a href="/support" class="footer-link">Support</a>
            <a href="/feedback" class="footer-link">Feedback</a>
        </nav>
    </footer>

    {# jQuery (required before page scripts) #}
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>

    {# Page-specific JS #}
    {% block scripts %}{% endblock %}

    {# Hamburger menu toggle — keep this exact pattern #}
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const menuToggle = document.getElementById('menu-toggle-checkbox');
            const menu = document.querySelector('.nav-primary .menu');
            menuToggle.addEventListener('change', function() {
                if (this.checked) {
                    menu.classList.add('visible');
                } else {
                    menu.classList.remove('visible');
                }
            });
        });
    </script>
</body>
```

NOTE: The hamburger menu JS in the `<script>` tag at the bottom of body is
the ONE exception to the "no inline JS" rule in CLAUDE.md. It must stay
inline because it controls the menu toggle for every page and needs to
execute without an external file dependency. Flag it with a comment.


## FILE 2: static/css/styles.css

This is the main app stylesheet. Port the reusable patterns from the AI
Timeline styles.css. Include ONLY the reusable patterns, not the
app-specific ones (timeline, DataTable column widths, vis.js overrides).

### Section 1: Variables

Copy the EXACT `:root` block from CLAUDE.md, but fix these two bugs
from the reference file:
- `--color-brand-blue-light` was incorrectly declared as a second
  `--color-brand-blue`. Fix: `--color-brand-blue-light: #4E9DD2;`
- `--color-light-gray` had a double hash. Fix: `--color-light-gray: #DEDEDE;`

Also add these link color variables that exist in the CLAUDE.md reference:
```css
--link-color: #FFA500;
--link-hover: #0273BE;
--link-visited: #4E9DD2;
```

### Section 2: Base Styles

From reference — port exactly:
```css
body {
    font-family: 'Ek Mukta', sans-serif;
    color: #333;
    font-size: 0.9em;
    font-weight: 200;
    width: 100%;
    overflow-x: hidden;
}
```

### Section 3: Heading Styles

Port the full heading hierarchy from reference:
- h1-h6 with `font-weight: 200; line-height: 1.2;`
- h2: `color: #0273be; font-size: 40px;`
- h3: `color: #ffa500; font-size: 1.8em;`
- h4: `color: #8bb42d; font-size: 1.4em;`
- h5: `font-size: 0.8em; color: #333;`
- `.entry-content h3 { color: #E90555; }` (fuscia override in content pages)
- `.hidden { display: none !important; }`

### Section 4: Header Styles

Port all `.site-header`, `.title-area`, `.header-logo`, `.wrap`, `.wrap-fluid`
styles exactly. Include the `.entry-header`, `.entry-title`, and
`.entry-header::after` decorative line styles.

### Section 5: Navigation

Port all `.nav-primary`, `.menu`, `.menu a`, `.menu a:hover`, `.menu-toggle`
styles exactly, including the checkbox-hack hamburger and `::before` content.

### Section 6: Main Content

Port `.main-content`, `.main-content p`, `.main-content li`, `.entry-content`,
`.image-credit` styles.

### Section 7: Footer

Port all `.footer`, `.footer::before`, `.footer-nav`, `.footer-link` styles.

### Section 8: Buttons

Port the `.button` styles exactly (orange background, blue hover, uppercase,
letter-spacing, box-shadow). These are used throughout the app.

### Section 9: Links

Port `.tools-link-no-padding`, `.hire-me-link` styles.

### Section 10: Filter Styles

Port `.filter-section`, `.filter-container`, `.filter-controls` and the
select/input styles. These will be reused on the subcategory browser (Level 2)
and potentially the dashboard for audit filtering.

### Section 11: Cards / Container Panels

Port the container panel pattern used by `.timeline-container` and
`.table-container` in the reference. Generalize to a `.panel` class:

```css
.panel {
    position: relative;
    background-color: #fff;
    padding: 15px;
    margin-bottom: 30px;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.11);
    border: 1px solid rgba(221, 221, 221, 0.5);
}

.panel-muted {
    background-color: #f8f9fa;
}
```

ALSO keep `.timeline-container` and `.table-container` as aliases that
extend `.panel` so existing timeline pages still work.

### Section 12: Pill Styles

Port `.company-pill` and `.tag-pill` styles. Generalize to a base `.pill`
class with color variants:

```css
.pill { /* base pill from reference .company-pill/.tag-pill */ }
.pill-blue { /* blue variant (default, from reference) */ }
.pill-orange { /* orange variant for tags */ }
.pill-green { /* green variant for status/progress */ }
```

### Section 13: Tooltip Styles

Port the `.info-icon` and `[data-tooltip]` tooltip pattern exactly.

### Section 14: Spinner

Port the `.spinner-overlay`, `.spinner`, and `@keyframes spin` exactly.
The spinner pattern will be reused for any async loading in Auditmaton for Site Audits.

### Section 15: Search Field

Port `.clearable-input`, `.clear-input` styles for reuse in search/filter
inputs across the app.

### Section 16: Audit Context Bar (NEW for Auditmaton for Site Audits)

Add styles for the audit context bar that sits below the header:

```css
.audit-context-bar {
    background-color: var(--color-app-bg);
    border-bottom: 1px solid var(--color-light-gray);
    padding: 8px 0;
    font-size: 14px;
}

.audit-context-bar .wrap {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.audit-context-domain {
    font-weight: var(--font-weight-bold);
    color: var(--color-dark-gray);
}

.audit-context-tier {
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: var(--font-weight-bold);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.tier-base { background-color: var(--color-light-gray); color: var(--color-dark-gray); }
.tier-viz { background-color: rgba(139, 180, 45, 0.2); color: var(--color-brand-green); }
.tier-ai { background-color: rgba(2, 115, 190, 0.2); color: var(--color-brand-blue); }

.audit-context-tokens {
    color: var(--color-dark-gray);
}
```

### Section 17: Responsive Design

Port ALL responsive breakpoints from reference with the same media query
structure. The breakpoints are:

- `>= 1500px` — Extra large
- `>= 1024px` — Large (desktop nav, header height 76px, `.menu-toggle` hidden)
- `1023px - 801px` — Medium (centered logo, centered nav, no hamburger)
- `<= 800px` — Small (hamburger menu, stacked filters, stacked layout)
- `800px - 601px` — Small-medium (stacked filter variant)
- `<= 600px` — Extra small (tighter padding, container margins)
- `<= 500px` — Tiny (grid footer links, card-style footer)

For each breakpoint, port both the REUSABLE rules (header, nav, footer,
typography, buttons) and add Auditmaton for Site Audits SPECIFIC rules for the dashboard
card grid.

Dashboard card responsive behavior:
- `>= 1024px`: 3 columns (Bootstrap `col-lg-4`)
- `801px - 1023px`: 2 columns (`col-md-6`)
- `<= 800px`: 1 column (`col-12`)


## FILE 3: static/js/dashboard.js

Start with a file-level comment describing purpose. Use banner-style
comment headings matching the JS pattern from CLAUDE.md.

### Section 1: Spinner

Port the `showTimelineSpinner()` / `hideTimelineSpinner()` pattern but
generalize it. Name it `showSpinner(elementId)` / `hideSpinner(elementId)`
so it works for any spinner overlay. Keep the fade-out timing (opacity
transition + setTimeout 300ms + `.hidden` class toggle).

### Section 2: Progress Bar Animation

On DOM ready, animate all `.progress-fill` elements from width 0 to their
target width. Use jQuery since it's available:

```javascript
$(document).ready(function() {
    $(".progress-fill").each(function() {
        const target = $(this).data("progress");
        $(this).css("width", target + "%");
    });
});
```

The CSS transition on `.progress-fill` handles the animation. No JS
animation library needed.

### Section 3: Card Click Handlers

Use event delegation (jQuery `.on()`) for category card clicks:

```javascript
$(document).on("click", ".category-card:not(.category-card-locked)", function() {
    const categoryKey = $(this).data("category");
    window.location.href = "/audit/" + categoryKey;
});
```

Locked cards (`.category-card-locked`) are excluded from the click handler.

### Section 4: Tooltips

Initialize Bootstrap tooltips for locked category cards:

```javascript
$(function () {
    $('[data-toggle="tooltip"]').tooltip();
});
```

### Section 5: URL Parameter Handling

Port the `getUrlParams()` / `updateUrlParams()` pattern from the reference
JS. This foundation will be reused when the dashboard adds filter/sort
capabilities later. For v1, it only needs to handle `?audit=<id>` to track
the active audit session.


## FILE 4: blueprints/audit/routes.py

Start with a file-level comment. Use Python banner-style headings from
CLAUDE.md. Follow all docstring and comment conventions.

```python
# blueprints/audit/routes.py
# Handles audit session management, dashboard, and category/subcategory views.
```

### Blueprint Setup

```python
from flask import Blueprint, render_template

audit_bp = Blueprint(
    "audit",
    __name__,
    template_folder="templates",
    static_folder=None,
)
```

### Mock Data

Create a `get_mock_dashboard_data()` function that returns realistic
category progress. Make it look lived-in:
- AI/GEO: 1 of 4 (25%)
- Crawl: 8 of 12 complete (67%)
- E-E-A-T: 3 of 8 complete (38%)
- Content: 7 of 7 (complete)
- Media: 2 of 9 (22%)
- Mobile: 0 of 6 (not started)
- Links: 0 of 7 (not started)
- International: 0 of 10 (not started)
- Local: locked (site type is "SaaS")
- Shopping: 6 of 6 (complete)

### Dashboard Route

```python
@audit_bp.route("/dashboard")
def dashboard():
    """
    Renders the Category Dashboard (Level 1 navigation).

    Loads the active audit session and calculates per-category
    progress. Passes category data as a list of dicts to the template.

    Returns:
        Rendered dashboard.html template.
    """
    categories = get_mock_dashboard_data()
    active_audit = get_mock_active_audit()
    return render_template(
        "audit/dashboard.html",
        categories=categories,
        active_audit=active_audit,
    )
```

Also create `get_mock_active_audit()` returning a simple object/dict with
domain, tier, tier_display, and tokens_remaining for the context bar.

### Category Data Structure

Each category dict MUST include:

```python
{
    "key": "crawlability_indexation",
    "display_name": "Crawlability & Indexation",
    "description": "How search engines discover and access your pages",
    "icon_class": "fa-solid fa-spider",
    "total_subchecks": 12,
    "completed": 8,
    "percentage": 67,
    "status": "in_progress",        # "not_started", "in_progress", "complete"
    "conditional": False,
    "locked": False,
    "locked_reason": None,
}
```

For Local SEO when locked:
```python
{
    "key": "local_seo",
    "display_name": "Local SEO",
    "description": "Google Business Profile, NAP consistency, and local signals",
    "icon_class": "fa-solid fa-location-dot",
    "total_subchecks": 5,
    "completed": 0,
    "percentage": 0,
    "status": "locked",
    "conditional": True,
    "locked": True,
    "locked_reason": "Local SEO is available for local-relevant site types (Local Business, Healthcare, Legal, Financial Services, Recipe)",
}
```

### All 10 Categories with Icons

| Key                      | Display Name              | Icon                      | Subchecks |
|--------------------------|---------------------------|---------------------------|-----------|
| crawlability_indexation  | Crawlability & Indexation | fa-solid fa-spider        | 12        |
| site_architecture        | Site Architecture         | fa-solid fa-sitemap       | 8         |
| on_page_seo              | On-Page SEO               | fa-solid fa-file-lines    | 10        |
| content_quality          | Content Quality           | fa-solid fa-pen-fancy     | 7         |
| technical_performance    | Technical Performance     | fa-solid fa-gauge-high    | 9         |
| mobile_ux                | Mobile & UX               | fa-solid fa-mobile-screen | 6         |
| link_profile             | Link Profile              | fa-solid fa-link          | 7         |
| local_seo                | Local SEO                 | fa-solid fa-location-dot  | 5         |
| structured_data          | Structured Data & Schema  | fa-solid fa-code          | 6         |
| ai_geo                   | AI & GEO                  | fa-solid fa-robot         | 4         |

Total: 74 subchecks.


## FILE 5: blueprints/audit/templates/audit/dashboard.html

```html
{% extends "base.html" %}

{% block title %}Audit Dashboard — Auditmaton for Site Audits{% endblock %}
{% block page_title %}Audit Dashboard{% endblock %}

{% block extra_head %}
<link rel="stylesheet"
      href="{{ url_for('static', filename='css/dashboard.css') }}">
{% endblock %}

{% block content %}
<!-- ===================================================================
         Category Dashboard
         =================================================================== -->
<div class="wrap">

    <!-- ================================================
              Dashboard Summary Bar
             ================================================ -->
    <div class="dashboard-summary">
        <span class="dashboard-summary-count">
            {{ categories | selectattr('status', 'ne', 'locked')
               | selectattr('completed') | list | length }} of
            {{ categories | rejectattr('locked') | list | length }} categories touched
        </span>
    </div>

    <!-- ================================================
              Category Card Grid
             ================================================ -->
    <div class="row">
        {% for cat in categories %}
        <div class="col-lg-4 col-md-6 col-12 mb-4">
            <div class="category-card panel
                        category-card-{{ cat.status }}
                        {% if cat.locked %}category-card-locked{% endif %}"
                 data-category="{{ cat.key }}"
                 {% if cat.locked %}
                 data-toggle="tooltip"
                 data-placement="top"
                 title="{{ cat.locked_reason }}"
                 {% endif %}>

                {# Lock overlay for conditional categories #}
                {% if cat.locked %}
                <div class="category-card-lock">
                    <i class="fa-solid fa-lock"></i>
                </div>
                {% endif %}

                {# Icon and title #}
                <div class="category-card-header">
                    <i class="{{ cat.icon_class }} category-card-icon"></i>
                    <h3 class="category-card-title">{{ cat.display_name }}</h3>
                </div>

                {# Description #}
                <p class="category-card-desc">{{ cat.description }}</p>

                {# Progress bar #}
                <div class="progress-track">
                    <div class="progress-fill
                                progress-fill-{{ cat.status }}"
                         data-progress="{{ cat.percentage }}"
                         style="width: 0%;">
                    </div>
                </div>

                {# Progress text — positive framing #}
                <span class="category-card-progress">
                    {% if cat.locked %}
                        Not available for this site type
                    {% elif cat.status == 'complete' %}
                        <i class="fa-solid fa-check"></i> All {{ cat.total_subchecks }} complete
                    {% elif cat.status == 'not_started' %}
                        0 of {{ cat.total_subchecks }} complete
                    {% else %}
                        {{ cat.completed }} of {{ cat.total_subchecks }} complete
                    {% endif %}
                </span>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
{% endblock %}
```


## FILE 6: static/css/dashboard.css

Page-specific styles that layer on top of styles.css. Do NOT redefine
`:root` variables here; they live in styles.css.

```
/* ========================================================================
   Dashboard — Category Cards
   ======================================================================== */
```

### Card Base

Cards use the `.panel` class from styles.css for the container look, then
add dashboard-specific styling:

```css
.category-card {
    cursor: pointer;
    transition: box-shadow 0.2s ease, transform 0.2s ease, border-left-color 0.2s ease;
    border-left: 3px solid transparent;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.category-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
    transform: translateY(-2px);
}
```

### Card Status Variants

```css
/* Not started — muted */
.category-card-not_started {
    border-left-color: var(--color-light-gray);
}

/* In progress — blue accent */
.category-card-in_progress {
    border-left-color: var(--color-brand-blue);
}

/* Complete — green accent */
.category-card-complete {
    border-left-color: var(--color-brand-green);
}

.category-card-locked {
    opacity: 0.5;
    cursor: not-allowed;
    position: relative;
}

.category-card-locked:hover {
    box-shadow: none;
    transform: none;
}
```

### Card Internal Elements

Style `.category-card-header` (flex row with icon + title),
`.category-card-icon` (font-size 1.5em, color matches card status),
`.category-card-title` (h3 override: smaller size, no margin weirdness),
`.category-card-desc`, `.category-card-progress`, `.category-card-lock`.

The card title h3 should NOT use the global h3 orange color. Override it:
```css
.category-card-title {
    color: var(--color-dark-gray);
    font-size: 1.2em;
    margin: 0;
    font-weight: var(--font-weight-bold);
}
```

Icon colors by status:
```css
.category-card-not_started .category-card-icon { color: var(--color-light-gray); }
.category-card-in_progress .category-card-icon { color: var(--color-brand-blue); }
.category-card-complete .category-card-icon { color: var(--color-brand-green); }
.category-card-locked .category-card-icon { color: var(--color-light-gray); }
```

### Progress Bar

```css
.progress-track {
    height: 6px;
    background-color: var(--color-light-gray);
    border-radius: 3px;
    margin: 40px 0 8px 0;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.8s ease-out;
}

.progress-fill-in_progress { background-color: var(--color-brand-blue); }
.progress-fill-complete { background-color: var(--color-brand-green); }
.progress-fill-not_started { background-color: transparent; }
```

### Progress Text

```css
.category-card-progress {
    font-size: 0.85em;
    color: #666;
    margin-top: auto;
}

.category-card-progress .fa-check {
    color: var(--color-brand-green);
}
```

### Dashboard Summary Bar

```css
.dashboard-summary {
    margin-bottom: 1.5em;
    font-size: 1.1em;
    color: var(--color-dark-gray);
}
```

### Lock Overlay

```css
.category-card-lock {
    position: absolute;
    top: 12px;
    right: 12px;
    color: var(--color-light-gray);
    font-size: 1.2em;
}
```


## Files to Create (Summary)

1. `templates/base.html` — Master layout adapted from AI Timeline
2. `static/css/styles.css` — Full reusable stylesheet (17 sections above)
3. `static/css/dashboard.css` — Dashboard-specific card styles
4. `static/js/dashboard.js` — Progress animation, card clicks, tooltips
5. `blueprints/audit/__init__.py` — Blueprint registration
6. `blueprints/audit/routes.py` — Dashboard route with mock data
7. `blueprints/audit/templates/audit/dashboard.html` — Category card grid


## Quality Checks Before Finishing

- [ ] `:root` variable block is in styles.css only (not repeated in dashboard.css)
- [ ] `--color-brand-blue-light` is correctly `#4E9DD2` (not a duplicate `--color-brand-blue`)
- [ ] `--color-light-gray` is `#DEDEDE` (single hash)
- [ ] ALL colors outside `:root` use CSS custom properties (no hardcoded hex)
- [ ] Banner-style comment headings in all files match CLAUDE.md formats
      exactly (check the character widths for Python, CSS, JS, and HTML)
- [ ] Every Python function has a docstring, even simple ones
- [ ] Comments are generous, start with capital letter, no end punctuation
- [ ] Double quotes throughout (not single quotes)
- [ ] No `<hr>` or `---` anywhere
- [ ] No spaced em dashes in any user-facing text
- [ ] No inline JS or CSS in templates (exception: hamburger toggle in base.html, flagged)
- [ ] Progress framed positively ("5 of 12 complete" not "7 remaining")
- [ ] Template extends base.html and uses correct block names
- [ ] Route uses blueprint pattern (file in `blueprints/audit/`)
- [ ] Template lives in `blueprints/audit/templates/audit/`
- [ ] Mobile-responsive grid via Bootstrap (3 col → 2 col → 1 col)
- [ ] Responsive breakpoints match reference: 1500, 1024, 1023-801, 800, 600, 500
- [ ] Card hover states feel polished (elevation + subtle translateY)
- [ ] Locked category has reduced opacity, lock icon, tooltip, and no click handler
- [ ] `.panel` class generalizes the reference container pattern
- [ ] `.pill` class generalizes the reference pill pattern
- [ ] Spinner pattern ported and generalized
- [ ] Font Awesome icons on all category cards
- [ ] Ek Mukta font family applied via `--font-family-main`
- [ ] Hamburger menu works on mobile (checkbox-hack pattern preserved)
- [ ] Footer uses card-style links at 500px breakpoint (from reference)