# DEPLOY.md — Auditmaton: Ads Deployment & Branch Guide

> Claude Code: Read this entire file before taking any git or deployment action. Never proceed past a ⚠️ CRITICAL step without explicit confirmation.

---

## ⚠️⚠️ CRITICAL RULE #1: MERGE TO MAIN BEFORE CREATING A NEW BRANCH

**Never start a new branch from a stale `main`. Before creating ANY new feature/build/fix branch, the current branch's signed-off work MUST be merged to `main` first.**

This is not optional. On 2026-06-17 a second Claude Code session created `build-linkedin-ads` off a stale `main` (which had neither the Google Ads Phase 2 work nor Meta Ads). Switching to that branch made Google Ads and Meta Ads "disappear" from the working tree (they were safe in commits on `build-meta-ads`, but invisible on the new branch). It read as catastrophic data loss. It was not — but it cost real anxiety and time.

**Why this happens:** committed work lives on the branch it was committed to. If you branch off a `main` that predates that work, the new branch's working tree will not contain it. Switching branches then makes the earlier work vanish from view.

**The rule, every time:**

```bash
# BEFORE creating a new branch:
# 1. Merge the current branch to main (after Annie signs off)
git checkout main
git pull origin main                  # if a remote is configured
git merge <current-branch> --no-edit
git push origin main                  # if a remote is configured

# 2. ONLY NOW create the new branch off up-to-date main
git checkout -b <new-branch>
```

If the current branch has unmerged work Annie has not yet signed off on, **STOP and ask** — do not branch from stale main, and do not start parallel work in another session on a branch that forks before unmerged work.

**Corollary:** Never develop directly on `main`. Always branch. But always merge back promptly so `main` is the single source of truth and no branch drifts far from it. Long-lived stacked branches are how work gets stranded.

---

## App Variables

```
APP_NAME=          auditmaton-ads
APP_DISPLAY_NAME=  Auditmaton: Ads
STAGING_PORT=      8022
PROD_PORT=         8023
APP_PATH_SEGMENT=  tools/auditmaton/ads-audits
BASE_URL_PROD=     https://www.annielytics.com/tools/auditmaton/ads-audits
BASE_URL_STAGING=  https://staging.annielytics.com/tools/auditmaton/ads-audits
HAS_DATABASE=      yes        # confirm DB name before the first server deploy
DB_NAME=           auditmaton_ads   # CONFIRM — may differ from scaffold
```

> Claude Code: confirm the DB name, ports, and path segment with Annie before the first server deploy. Nothing in this repo is deployed to the server yet as of 2026-06-17 — it is local + branch work only.

---

## ⚠️ CRITICAL: Port Registry
> Never assign a port already in use. Show Annie this full list and confirm before writing any config.

| Port | App | Environment |
|------|-----|-------------|
| 8000 | AI Strategy | production |
| 8001 | AI Timeline | production |
| 8002 | AI Strategy | staging |
| 8003 | AI Timeline | staging |
| 8004 | ML Model Picker | production |
| 8005 | ML Model Picker | staging |
| 8006 | Daybell Case | production |
| 8007 | Daybell Case | staging |
| 8008 | STEM Activities | production |
| 8009 | Under Armour Redirect | production |
| 8010 | Under Armour Redirect | staging |
| 8011 | XGBoost Demo | production |
| 8012 | Crawl Canvas (Auditmaton: Site) | staging |
| 8013 | Crawl Canvas (Auditmaton: Site) | production |
| 8014 | Cloud Kingdom | staging |
| 8015 | Cloud Kingdom | production |
| 8016 | Conversion Canvas (Auditmaton: Analytics) | staging |
| 8017 | Conversion Canvas (Auditmaton: Analytics) | production |
| 8018 | Auditmaton: Tag Management | staging |
| 8019 | Auditmaton: Tag Management | production |
| 8022 | **Auditmaton: Ads** | **staging** |
| 8023 | **Auditmaton: Ads** | **production** |

> After deploying, keep this table in sync with the master in Cloud Kingdom's DEPLOY.md.

---

## ⚠️ Protected invariants (do NOT regress these)

These have each broken at least once. Before committing UI or registry changes, confirm they still hold.

1. **Platform dropdown must render above the swimlane.** The platform filter lives in a `.wrap` that is `overflow: hidden`, which clips the absolutely-positioned dropdown menu. The fix is the `.platform-filter-wrap` modifier in `static/css/dashboard.css` (`overflow: visible; position: relative; z-index: 100;`) applied to the filter's wrap in `templates/dashboard.html`. If the dropdown is ever behind the cards again, this class is missing. Do not "fix" it with z-index alone — a z-index cannot escape an `overflow: hidden` clip.
2. **Platform dropdown lists platforms only** — no type-group headers (the `platform-filter-type-label` was removed deliberately).
3. **Editorial gate must pass.** `python3 scripts/lint_editorial.py json/ --severity medium` must print CLEAN before any commit of audit content. The pre-commit hook enforces it. Also scrub the patterns the linter cannot see (`tends to`, `quietly`/`silently` + verb, `is common`, `most/many accounts`) — see `~/.claude/rules/editorial/audit-content-authoring.md`.
4. **Every citation is a verified, genuine doc — never a sales page.** Authoring agents WebFetch-verify and drop dead URLs. Re-check with `python3 scripts/verify_citation_urls.py json/<platform>` from a normal network (sandbox IPs get 429-throttled by Google/Meta help — a 429 is not a broken link; a 404/410/5xx is). A 200 is necessary but NOT sufficient: a citation must be real documentation (help center, product guide, ad spec, API/developer docs, or an IAB/MRC standard), not a product/solutions/marketing page that reads as AI slop. The check: `grep -rnE '/solutions/products/|\.com/products/|/lp/|/our-platform|/our-demand-side-platform/' json/<platform>` must return nothing. Where a topic's only docs are gated behind a partner login (e.g., The Trade Desk), use the gated-docs `educate.learn_more_note` (rendered by the canvas Learn More `elif`) instead of a marketing page. Platforms with deep public help centers (Google, Meta, LinkedIn, DV360 via Google help) pass naturally; Amazon DSP and The Trade Desk did not until fixed.
5. **theme_tags are side-appropriate.** Every check carries valid slugs from `json/_themes.json` whose `sides` include the platform's side. The linter enforces this.
6. **New platforms** follow `~/.claude/rules/coding/auditmaton-ads-new-platform-prompt.md`. The platform must exist in `json/_platforms.json`; add a `CATEGORY_METADATA` block per category in `services/audit_engine.py`; update `specs/platform_tracker.csv`.
7. **Category names + icons are canonical across platforms.** A category `display_name` that appears on more than one platform MUST use the same `icon_class` everywhere, and you reuse the established name wherever the concept matches (don't coin synonyms). The canonical registry lives in the new-platform rule (`~/.claude/rules/coding/auditmaton-ads-new-platform-prompt.md`, "Canonical category names + icons"). Current set: Conversion Tracking `fa-bullseye`, Attribution `fa-route`, Campaigns `fa-rectangle-list`, Bidding `fa-hand-holding-dollar`, Targeting `fa-crosshairs`, Creative `fa-palette`, Measurement `fa-chart-line`, Governance `fa-scale-balanced`, Privacy `fa-user-shield`, Inventory `fa-boxes-stacked`, Brand Safety `fa-shield-halved`, Identity `fa-fingerprint`, Retail `fa-bag-shopping`, Coverage `fa-satellite-dish`, Fraud `fa-user-secret`, Viewability `fa-eye`, Audience `fa-users`. A quick audit: `python3 -c "import services.audit_engine as e;from collections import defaultdict;d=defaultdict(set);[d[m['display_name']].add(m['icon_class']) for p in e.CATEGORY_METADATA.values() for m in p.values()];[print('CONFLICT',k,v) for k,v in d.items() if len(v)>1]"` prints nothing when consistent.
8. **Acronyms render with correct casing.** Subcategory display names are title-cased from the slug by `_format_display_name` in `services/audit_engine.py`, which lowercases acronyms ("creative_qa" -> "Creative Qa"). Every acronym a slug uses must be in the `DISPLAY_ACRONYMS` map there (QA, STV, ID, IO, PMP, AMC, ASIN, OpenPath, UID2, DSP, CM360, …); a standalone slug that means something special (e.g., `qa` as Q&A) goes in the `overrides` dict, checked first. When adding a platform, add its new acronyms and eyeball `/dashboard/<platform>/<category>/` — every subcategory label should read with correct casing.

---

## Git Workflow

```bash
# Normal flow: branch, work, merge back PROMPTLY
git checkout -b build-<platform-or-feature>   # off up-to-date main (see Rule #1)
# ... commit work on the branch ...
# When Annie signs off, merge to main right away (Rule #1), do not let it linger.
git checkout main && git merge build-<...> --no-edit && git push origin main
```

- **Branch naming:** `build-<platform>` for a new platform (e.g., `build-meta-ads`), `<area>-<fix>` for fixes.
- **Never stack a new branch on an unmerged branch.** Merge to main first (Rule #1).
- **One source of truth:** after sign-off, `main` should contain all shipped work. A branch that lives more than a session or two is a smell — merge it.
- **Backups before risky git ops:** `git tag -f backup/<name> <branch>` for every branch tip before any merge/reset/rebase. Tags are free and make any state recoverable.

### Branch state snapshot (2026-06-17, pre-consolidation)
- `main` — conversion-tracking + intake fixes only.
- `build-meta-ads` — Google Ads (7 categories) + Meta Ads (7 categories) + the dropdown fix + verify script + tracker CSV.
- `build-linkedin-ads` — LinkedIn Ads (7 categories), forked off stale main (lacks Google Phase 2 / Meta / dropdown fix).
- `phase2-google-ads-categories`, `build-calibration-google-ads` — older, superseded by `build-meta-ads`.
- Backup tags `backup/*` exist for every tip.

The consolidation merges everything into `main` so this fragmentation ends.

---

## Pre-Flight Checklist (Local, before first server deploy)

- [ ] `requirements.txt` generated from the active venv: `pip freeze > requirements.txt`
- [ ] `.gitignore` includes `__pycache__/`, `venv/`, `archive/`, `.env`, `logs/`
- [ ] `wsgi.py` exists in project root with `ProxyFix` + `DispatcherMiddleware` for the URL prefix
- [ ] Editorial gate CLEAN: `python3 scripts/lint_editorial.py json/ --severity medium`
- [ ] URL health (from a normal network): `python3 scripts/verify_citation_urls.py json/`
- [ ] `git status` is clean and the working branch is merged to `main`

---

## Server Deploy (staging → prod)

Same pattern as every Annielytics app (mirrors Cloud Kingdom's DEPLOY.md). Summary:

```
Staging dir:  /home/anniecushing/apps/staging/auditmaton-ads/
Prod dir:     /home/anniecushing/apps/auditmaton-ads/
Python:       /usr/bin/python3.11   (NEVER plain python3 — server default is 3.10)
Nginx:        staging.annielytics.conf  /  annielytics.conf
systemd:      auditmaton-ads-staging.service  /  auditmaton-ads.service
```

1. **Branch + merge:** ensure work is merged to `main` (Rule #1), push.
2. **Staging:** `git pull` on `~/apps/staging/auditmaton-ads/`, `pip install -r requirements.txt` in the 3.11 venv, restart `auditmaton-ads-staging`.
3. **Nginx block** for `/tools/auditmaton/ads-audits/` → `127.0.0.1:8022` (staging) with `X-Forwarded-Prefix` + `X-Script-Name` set to the path segment; `sudo nginx -t && sudo systemctl reload nginx`.
4. **systemd `SCRIPT_NAME`** must match the path segment, or gunicorn 500s with a SCRIPT_NAME-mismatch error. `daemon-reload` after editing the unit.
5. **✅ Wait for Annie's sign-off on staging before prod.** Never deploy prod unprompted.
6. **Prod:** repeat on `~/apps/auditmaton-ads/` with port 8023 and the prod nginx/systemd files.

> The full step-by-step (venv, nginx block, systemd unit templates, troubleshooting) is identical to Cloud Kingdom's DEPLOY.md Parts 1–2 — follow that for the mechanics; this file owns the Auditmaton-specific variables, invariants, and the branch rule.

---

## Server security (all apps)

Per `~/.claude/rules/security/server-security.md`: never open ports without approval, web traffic only from Cloudflare ranges, gunicorn + DB bind to 127.0.0.1 only, no credentials in code (env vars only), HTTPS only. Confirm no change violates these before any server edit.
