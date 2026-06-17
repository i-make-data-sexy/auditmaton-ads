# SCAFFOLD_REPORT.md — Auditmaton: Ads

Generated: 2026-06-16
Scaffold commit: 9816a7f
Source: Auditmaton: Tag Management (local dir: Auditmaton Tags/)
Target: ~/Dropbox/Annielytics/Code/Python/Auditmaton Ads/

---

## What Was Carried Over

190 files committed from Auditmaton: Tag Management via rsync, excluding:

- `venv/` — not copied (Annie creates with python3.11)
- `__pycache__/` — not copied
- `.git/` — not copied (new repo initialized)
- `.DS_Store`, `Icon` — not copied
- `archive/` — not copied
- `uploads/` contents — not copied (directory present but empty)
- `logs/` contents — not copied (directory present but empty)
- `reports/` contents — not copied (directory present but empty)
- `.env` — NOT copied (secrets never travel between repos)
- `json/*` contents — directory present but empty (taxonomy TBD)
- `migrations/versions/` — not copied (fresh DB migration needed)
- `queue/` data files — not copied
- `_taxonomy_drafts/` — NOT copied (those are GTM taxonomy drafts; Ads taxonomy starts fresh)
- `SCAFFOLD_REPORT.md` — not copied (this file replaces it)

---

## Naming Map Applied

| Concept | Old (Tags) | New (Ads) |
|---|---|---|
| Product name | Auditmaton: Tag Management | Auditmaton: Ads |
| URL segment | /tools/auditmaton/tag-audits | /tools/auditmaton/ads-audits |
| GitHub repo slug | auditmaton_tag_management | auditmaton_ads |
| Server service slug | auditmaton-tag-management | auditmaton-ads |
| Session cookie name | auditmaton_tags_session | auditmaton_ads_session |
| Remember cookie name | auditmaton_tags_remember | auditmaton_ads_remember |
| Dev secret-key fallback | auditmaton-tag-management-dev-secret-key | auditmaton-ads-dev-secret-key |
| Staging/prod ports | 8018 / 8019 | 8022 / 8023 |
| Dev DB default | crawl_canvas (Tags legacy) | auditmaton_ads |

---

## Branding Renames Applied (User-Facing + Identifier Files)

Surgical renames applied to user-facing and identifier files only. Internal
identifiers (canvas.py, /dashboard/ routes, DB table names with "canvas",
task_queue Huey name) left unchanged per playbook conventions.

| File | Change |
|---|---|
| `config.py` | Docstring, SECRET_KEY dev fallback, SESSION_COOKIE_NAME, REMEMBER_COOKIE_NAME, APPLICATION_ROOT default, dev DATABASE_URL default |
| `app.py` | Module docstring, APPLICATION_ROOT comment, apply_intake_overrides docstring |
| `templates/base.html` | `<title>`, meta description, OG title/description, Twitter title/description |
| `templates/home.html` | Page title, tagline (data-text), hero alt, hero pitch paragraph, card 2 (placeholder) |
| `templates/pricing.html` | `{% block title %}` |
| `templates/architecture.html` | `{% block title %}`, intro paragraph |
| `templates/dashboard.html` | Internal comment (user-visible if read source) |
| `blueprints/auth/templates/auth/reset_password.html` | `{% block title %}` |
| `blueprints/auth/templates/auth/register.html` | `{% block title %}` |
| `blueprints/auth/templates/auth/login.html` | `{% block title %}` |
| `blueprints/admin/templates/admin/hub.html` | `{% block title %}` |
| `blueprints/admin/templates/admin/editorial_revisions.html` | `{% block title %}` |
| `blueprints/admin/templates/admin/site_type_suggestions.html` | `{% block title %}` |
| `blueprints/audit/templates/audit/dashboard.html` | `{% block title %}` |
| `blueprints/audit/templates/audit/category.html` | `{% block title %}`, two code comments |
| `blueprints/audit/templates/audit/intake.html` | `{% block title %}`, modal heading, lede, audit name help text, placeholder, account ID label/help/placeholder |
| `blueprints/audit/templates/audit/canvas.html` | `{% block title %}` |
| `blueprints/editorial/templates/editorial/dashboard.html` | `{% block title %}` |
| `blueprints/auth/routes.py` | Module docstring, Authorize.net subscription description string |
| `blueprints/audit/intake.py` | Module docstring/header comment block |
| `deploy/` | Renamed both service files; updated all paths, slugs, ports (8022/8023), SCRIPT_NAME |
| `.env.example` | DATABASE_URL dev default |
| `static/css/styles.css` | File-header comment |
| `static/css/home.css` | File-header comment |
| `static/css/intake.css` | File-header comment |
| `static/css/category.css` | Depth-filter section comment |
| `static/js/tier-filter.js` | File-header comment |
| `services/sheets_service.py` | SPREADSHEET_NAME constant |
| `services/audit_engine.py` | SCAFFOLD NOTE + Platform Switching comment block, DEFAULT_PLATFORM |
| `services/crawl_processor.py` | SCAFFOLD NOTE |
| `scripts/seed_products.py` | Base plan description string |
| `scripts/lint_editorial.py` | Module docstring, --help text |
| `editorial/editorial_revisions.json` | Reset to empty wrapper (Tags revisions not carried) |
| `.claude/rules/project-overview.md` | Full rewrite for Ads domain + Demand/Supply architecture |
| `.claude/rules/directory-structure.md` | Directory name, json/ structure for Demand/Supply fork |
| `specs/schema_v1.md` | Header note marking it as inherited from Tags |
| `specs/phase3-integration-notes.md` | Header note marking it as inherited from Tags |
| `README.md` | Full rewrite (2 paragraphs) for Ads edition |

---

## SCAFFOLD NOTE — Files Flagged for Review

Three files carry a leading SCAFFOLD NOTE comment block identifying them as
inherited logic that needs review before v1 goes live.

### `services/crawl_processor.py`
Crawl/upload processing logic. NOT needed in v1. Auditmaton: Ads uses
manual/checklist intake only. The intake redesign pass should remove or
replace this with whatever intake parsing the Ads edition requires.

### `services/audit_engine.py`
Core audit schema loader. The `column_dependencies` / crawl-data analysis
patterns do not apply to ad audits. The DEFAULT_PLATFORM has been changed
to `"google-ads"` as a placeholder. The actual platform list, default, and
any Demand/Supply routing logic should be implemented here when the taxonomy
is designed.

### `blueprints/audit/intake.py`
Manual intake form inherited from Tag Management. The Demand/Supply top-level
fork is not yet implemented. The intake redesign pass should add the
demand-side vs. supply-side selector, update the platform list, and adapt
field labels for advertising (e.g., "account ID" instead of "container ID").

---

## Items Left Unchanged (Internal / Deferred)

| Reference | Location | Reason |
|---|---|---|
| `crawl_canvas` Firebase CSP URL | `app.py` (CSP headers) | Firebase project rename deferred |
| `crawl_canvas` Huey queue name | `services/task_queue.py` | Internal queue identifier, not user-visible |
| `blueprints/audit/canvas.py` | File name + class | UI component, not brand-visible |
| `/dashboard/` URL prefix | All route files | Internal routing, not brand-specific |
| `GTM-5FJGP2` tracking ID | `templates/base.html` | Annie's own GTM tag for the app; not a content reference |
| `https://www.googletagmanager.com` CSP entries | `app.py` | CSP infrastructure allowing Google's tracking scripts |
| GTM/tag-management references in `specs/` | All specs files | Internal historical/planning docs, inherited and noted as such |
| `specs/tool_inventory.md` "Tag Management Tools" section | Internal spec | Carries forward Tags taxonomy reference material |
| `specs/product_spec.md` GTM references | Internal spec | Carries forward Tags product planning notes |
| `specs/build_dashboard.md`, `specs/reference_base.html` | Internal specs | Historical reference files, frozen |
| `blueprints/audit/intake.py` SCAFFOLD NOTE mention of Tag Management | Intent comment | Expected by design — it's the SCAFFOLD NOTE itself |
| `services/audit_engine.py` SCAFFOLD NOTE | Intent comment | Expected |
| `services/crawl_processor.py` SCAFFOLD NOTE | Intent comment | Expected |
| `.claude/rules/project-overview.md` mention of "Auditmaton: Tag Management" | Context sentence | Appropriate reference in intake-redesign note |

---

## `editorial/editorial_revisions.json` Reset

The Tags revision log (598 revisions across 111 files) was NOT carried into this edition.
The file was reset to an empty wrapper:

```json
{"generated_at": null, "baseline_ref": "main", "revision_count": 0, "file_count": 0, "revisions": []}
```

The editorial infrastructure files (`services/revision_log.py`,
`scripts/lint_editorial.py`, `scripts/git-hooks/pre-commit`,
`.github/workflows/lint-editorial.yml`) were carried verbatim and are
fully operational.

---

## `.claude/` Directory Handling

| File / Dir | Action |
|---|---|
| `.claude/CLAUDE.md` | Kept verbatim (structural, not domain-specific) |
| `.claude/rules/project-overview.md` | REWRITTEN for Ads domain + Demand/Supply architecture |
| `.claude/rules/directory-structure.md` | REWRITTEN: dir name, json/ structure for Demand/Supply |
| `.claude/rules/code-style.md` | Kept verbatim (generic Python conventions) |
| `.claude/rules/frontend/styles.md` | Kept verbatim (brand colors, identical across editions) |
| `.claude/settings.json` | Kept verbatim (notification hooks) |
| `.claude/skills/edu-base-writer/` | Kept (domain-neutral editorial helper) |
| `.claude/skills/rewrite-edu-bases/` | Kept (domain-neutral editorial helper) |

No `seo-content-writer.md` agent was present in Tags, so nothing to delete.

---

## Hero Copy and Home Cards — Annie's Sign-Off Required

The home page hero uses placeholder copy:

- Tagline: `for ad audits` (data-text in `templates/home.html`)
- Pitch paragraph: placeholder pointing to the ad audit concept, using
  "auditing an advertising account" as the domain noun
- Card 2: placeholder ("Ad Campaigns" with `fa-chart-line` icon) because the
  Demand/Supply topology affects which check surface to link here

Before committing production-quality hero copy, surface these to Annie:

1. The final tagline phrase ("for ad audits" or different?)
2. The second card's identity, icon, and target URL
3. The pitch paragraph's final domain noun ("auditing an advertising account"?
   "auditing your Google Ads account"? "auditing an ad platform"?)

These are flagged with `{# PLACEHOLDER #}` comments in `templates/home.html`.

---

## Demand vs. Supply Architecture — Key Design Decision

Auditmaton: Ads has a Demand/Supply fork not present in any prior edition.
The `json/` directory structure needs to reflect this:

- Demand-side: Google Ads, Meta Ads, TikTok Ads, Microsoft Ads, LinkedIn Ads
- Supply-side: Google Ad Manager, AdSense, header-bidding (Prebid), SSPs

The intake form needs to capture the practitioner's role (demand or supply)
and their specific platform. `blueprints/audit/intake.py` is flagged for
this redesign.

The `apply_intake_overrides()` function in `app.py` (line ~698) currently
returns categories unchanged. The Demand/Supply gating logic goes there.

**No OAuth, no platform API calls.** Per Annie's no-platform-auth principle,
this edition is guided manual audit only. The intake captures reference IDs
(e.g., Google Ads customer ID) as labels only, never for authentication.

---

## Editorial Gate Status

REGISTERED AND OPERATIONAL.

All three enforcement-chain files confirmed present:
- `scripts/lint_editorial.py` — the linter (canonical from Crawl Canvas)
- `scripts/git-hooks/pre-commit` — thin wrapper, calls linter on staged JSON
- `.github/workflows/lint-editorial.yml` — CI gate on every push and PR

Hooks path registered (not committed to git):
```
git config core.hooksPath scripts/git-hooks
# returns: scripts/git-hooks (verified)
```

Linter smoke-test against empty `json/`:
```
python3 scripts/lint_editorial.py json/ --severity high
# "No JSON files found" — expected result for empty json/, CLEAN
```

---

## Next Steps for Human

### 1. Environment setup
1. `python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in all values (new SECRET_KEY, new DB URL,
   Firebase, Authorize.net, Mail credentials).
3. `createdb auditmaton_ads`
4. `flask db upgrade` to initialize the schema from Alembic migrations.

### 2. Annie's sign-off on hero copy and home cards
Before any user-facing deploy, resolve the PLACEHOLDER items in `templates/home.html`:
- Tagline phrase
- Card 2 identity, icon, and target URL
- Pitch paragraph domain noun

### 3. Intake redesign — Demand/Supply fork
The inherited intake form is for a single-platform manual audit (Tag Management).
Adapt it for the Demand/Supply fork:
- Add role selector (demand-side vs. supply-side)
- Update platform list to advertising platforms
- Update field labels (e.g., "Container or property ID" to "Account or property ID")

Key files: `blueprints/audit/intake.py`, `blueprints/audit/templates/audit/intake.html`

### 4. Taxonomy authorship
`json/` is empty. The Demand/Supply topology should be designed before fan-out.
Proposed structure:

```
json/
  demand-side/
    google-ads/
    meta-ads/
    tiktok-ads/
    microsoft-ads/
  supply-side/
    google-ad-manager/
    adsense/
    header-bidding/
```

Run the cluster agent fan-out per `~/.claude/rules/coding/replicate-auditmaton-as-new-app.md`.
The editorial gate will enforce writing rules as JSON files land.

### 5. Image asset replacement
`static/img/seo-auditor-home-screen.png` shows an SEO/GTM detective figure.
Replace with an ad-audit appropriate illustration.

Category dashboard images in `static/img/subcat/main/` reference SEO categories.
Replace as the Ads taxonomy is built.

### 6. DB schema review
The Alembic migrations were built for Auditmaton: Site and Tag Management. After
reviewing `models/audit.py` for crawl/GTM-specific fields, run a fresh migration
if the schema needs adjusting for ad audits.

### 7. Firebase project decision
`app.py` CSP and `static/js/auth.js` reference the Auditmaton: Site Firebase project
(`crawl-canvas.firebaseapp.com`). Decide whether to reuse or create a new Firebase
project for this edition.

### 8. GitHub remote
No remote has been set up. When ready:
```
git remote add origin git@github.com:anniecushing/auditmaton_ads.git
git push -u origin main
```

### 9. Server staging setup
- Port pair: **8022 staging / 8023 production**
- Server slug: `auditmaton-ads`
- Staging app dir: `~/apps/staging/auditmaton-ads/`
- Service files: `deploy/auditmaton-ads-huey-staging.service` and
  `deploy/auditmaton-ads-huey.service`

Verify ports 8022/8023 are free on the live server before provisioning:
```
ssh -i ~/.ssh/id_ed25519_imds anniecushing@208.109.215.51 \
  "sudo grep -rh '127.0.0.1:' /etc/systemd/system/*.service | sort -u"
```

Install the updated service files from `deploy/` once the staging directory is ready.
Follow the same nginx + systemd pattern as Auditmaton: Site and Tag Management.

---

## Auto-Push-to-Staging Reminder

Annie's convention (auto-memory `auto-push-to-staging`): commits on feature branches
push to staging automatically. This kicks in once:
1. The GitHub remote is set up (step 8 above).
2. The staging server directory is provisioned (step 9 above).

Until then, all commits are local only.
