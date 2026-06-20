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
APP_PATH_SEGMENT=  tools/auditmaton/ad-audits
BASE_URL_PROD=     https://www.annielytics.com/tools/auditmaton/ad-audits
BASE_URL_STAGING=  https://staging.annielytics.com/tools/auditmaton/ad-audits
HAS_DATABASE=      yes        # confirm DB name before the first server deploy
DB_NAME=           auditmaton_ads   # CONFIRM — may differ from scaffold
```

> Claude Code: confirm the DB name, ports, and path segment with Annie before the first server deploy.
>
> **Status (2026-06-19):** staging is deployed at `https://staging.annielytics.com/tools/auditmaton/ad-audits/` (gunicorn on 8022, Huey worker, Postgres `auditmaton_ads`, initial migration committed). Prod is not yet deployed. The staging `.env` still has Firebase, mail, and Authorize.net values empty, to be filled per **Secrets & Environment Setup** below.

---

## Secrets & Environment Setup

The app reads every secret from a `.env` file in the app root (gitignored, never committed). Two kinds of values live there. A few are **unique per app** and must be generated fresh. The rest are **shared Annielytics infrastructure** that every Auditmaton/Canvas app reuses: one Firebase project (`crawl-canvas`), one Gmail mailbox, and one Authorize.net merchant account. For the shared ones, copy from any already-configured sibling app (Crawl Canvas, Conversion Canvas, Auditmaton Tags, or Ads itself once it's set up).

> The `<SOURCE_APP>` referenced below is any configured sibling, e.g. `crawl-canvas`. Once Ads is fully configured, Ads can be the source for the next edition.

| `.env` key | Copy or generate? | How |
|---|---|---|
| `SECRET_KEY` | 🆕 **Generate** (unique per app) | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | ⚙️ **Mostly generate** | The database name is new per app (`auditmaton_ads`); the password is the shared `anniecushing` Postgres role password, copied from a sibling's `DATABASE_URL`. |
| `APPLICATION_ROOT` | ⚙️ **Per app** | This app: `/tools/auditmaton/ad-audits` |
| `FLASK_ENV` | ⚙️ **Per environment** | `production` on the server, `development` locally |
| `FIREBASE_API_KEY` | ♻️ **Copy** | Identical across all apps (shared `crawl-canvas` project) |
| `FIREBASE_AUTH_DOMAIN` | ♻️ **Copy** | `crawl-canvas.firebaseapp.com` |
| `FIREBASE_PROJECT_ID` | ♻️ **Copy** | `crawl-canvas` |
| `GOOGLE_APPLICATION_CREDENTIALS` | ♻️ **Copy the file** | Same Firebase service account for every app. Copy a sibling's `.secrets/*-firebase.json` to this app's `.secrets/auditmaton-ads-firebase.json` (chmod 600), then point the var at the new path. This is the server-side Admin SDK key that verifies Firebase ID tokens, distinct from the client-side `FIREBASE_*` config above. |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | ♻️ **Copy** | Reuse a mailbox and its Gmail app password. `support@annielytics.com` aligns with the Reply-To pattern; `annie@annielytics.com` is also in use. |
| `MAIL_DEFAULT_SENDER` | ♻️ **Copy** | Match the chosen mailbox |
| `AUTHORIZE_NET_API_LOGIN_ID` | ♻️ **Copy** | One merchant account, shared across all apps |
| `AUTHORIZE_NET_TRANSACTION_KEY` | ♻️ **Copy** | Same merchant account |
| `AUTHORIZE_NET_PUBLIC_CLIENT_KEY` | ♻️ **Copy** | Same merchant account |
| `AUTHORIZE_NET_SANDBOX` | ⚙️ **Per environment** | `true` on staging, `false` on prod (live charges) |

> **Net for a new edition: only `SECRET_KEY` and the database are truly new. Everything else copies from a sibling.**

### Walkthrough (staging)

Run on the server, from the app dir. Replace `<SOURCE_APP>` with a configured sibling (e.g. `crawl-canvas`).

```bash
cd ~/apps/staging/auditmaton-ads
SOURCE=~/apps/staging/<SOURCE_APP>

# 1) Firebase service-account JSON (same project for every app, so copy the file)
mkdir -p .secrets && chmod 700 .secrets
cp "$SOURCE"/.secrets/*firebase*.json .secrets/auditmaton-ads-firebase.json
chmod 600 .secrets/auditmaton-ads-firebase.json

# 2) Copy the shared values from the sibling .env into this .env
#    (Firebase client config, mail, Authorize.net)
for k in FIREBASE_API_KEY FIREBASE_AUTH_DOMAIN FIREBASE_PROJECT_ID \
         MAIL_USERNAME MAIL_PASSWORD MAIL_DEFAULT_SENDER \
         AUTHORIZE_NET_API_LOGIN_ID AUTHORIZE_NET_TRANSACTION_KEY \
         AUTHORIZE_NET_PUBLIC_CLIENT_KEY; do
  val=$(grep -E "^$k=" "$SOURCE/.env" | cut -d= -f2-)
  python3 - "$k" "$val" <<'PY'
import sys, re, pathlib
k, v = sys.argv[1], sys.argv[2]
p = pathlib.Path(".env"); t = p.read_text()
t = re.sub(rf"^{k}=.*$", f"{k}={v}", t, flags=re.M)
p.write_text(t)
PY
done

# 3) Point the credentials path at THIS app's copy of the JSON
sed -i "s#^GOOGLE_APPLICATION_CREDENTIALS=.*#GOOGLE_APPLICATION_CREDENTIALS=$PWD/.secrets/auditmaton-ads-firebase.json#" .env

# 4) Restart so gunicorn and the Huey worker pick up the new values
sudo systemctl restart auditmaton-ads-staging auditmaton-ads-huey-staging
```

Already set when staging was first provisioned, so do NOT overwrite these: `SECRET_KEY` (freshly generated), `DATABASE_URL` (database `auditmaton_ads` with the shared role password), `APPLICATION_ROOT`, and `FLASK_ENV`.

**Firebase note:** sign-in needs no console change. Firebase authorizes by domain, and `staging.annielytics.com` and `www.annielytics.com` are already authorized for the sibling apps. Reusing the `crawl-canvas` project also means a shared user pool across all Auditmaton apps (one Annielytics identity), which matches the long-term one-account goal.

**Mail note:** `MAIL_PASSWORD` is a Gmail **app password** (not the account login password), tied to the chosen mailbox. Reusing a sibling's app password works, since any app password authenticates SMTP for that account. To mint a dedicated one for Ads instead (recommended, so it can be revoked independently), generate it at <https://myaccount.google.com/apppasswords> while signed in as the mailbox owner, then paste the 16-character value into `MAIL_PASSWORD`.

### Prod differences

When deploying prod, repeat the walkthrough under `~/apps/auditmaton-ads/` with these changes: generate a fresh `SECRET_KEY` distinct from staging, set `AUTHORIZE_NET_SANDBOX=false` (live charges), and put the credentials JSON under the prod dir's `.secrets/` with the matching `GOOGLE_APPLICATION_CREDENTIALS` path. Confirm `www.annielytics.com` is in the Firebase authorized domains (it already is, for the sibling apps).

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
| 8020 | Vinspire| staging |
| 8021 | Vinspire | production |
| 8022 | **Auditmaton: Ads** | **staging** |
| 8023 | **Auditmaton: Ads** | **production** |


> After deploying, keep this table in sync with the master in Cloud Kingdom's DEPLOY.md.

---

## ⚠️ Protected invariants (do NOT regress these)

These have each broken at least once. Before committing UI or registry changes, confirm they still hold.

1. **Platform dropdown must render above the swimlane.** The platform filter lives in a `.wrap` that is `overflow: hidden`, which clips the absolutely-positioned dropdown menu. The fix is the `.platform-filter-wrap` modifier in `static/css/dashboard.css` (`overflow: visible; position: relative; z-index: 100;`) applied to the filter's wrap in `templates/dashboard.html`. If the dropdown is ever behind the cards again, this class is missing. Do not "fix" it with z-index alone — a z-index cannot escape an `overflow: hidden` clip.
2. **Platform dropdown lists platforms only** — no type-group headers (the `platform-filter-type-label` was removed deliberately).
3. **Editorial gate must pass.** `python3 scripts/lint_editorial.py json/ --severity medium` must print CLEAN before any commit of audit content. The pre-commit hook enforces it. Also scrub the patterns the linter cannot see (`tends to`, `quietly`/`silently` + verb, `is common`, `most/many accounts`) — see `~/.claude/rules/editorial/audit-content-authoring.md`.
4. **Every citation is a verified, genuine doc — never a sales page.** Authoring agents WebFetch-verify and drop dead URLs. Re-check with `python3 scripts/verify_citation_urls.py json/<platform>` from a normal network (sandbox IPs get 429-throttled by Google/Meta help — a 429 is not a broken link; a 404/410/5xx is). The verifier also reports a `blocked` bucket for anti-bot/auth refusals of the script (facebook.com returns 400, Nielsen's portal returns 403) — these are live pages, NOT dead links, so they do not fail the run; spot-check any you doubt with WebFetch. Only `broken` (404/410/5xx) is a real fault. A 200 is necessary but NOT sufficient: a citation must be real documentation (help center, product guide, ad spec, API/developer docs, or an IAB/MRC standard), not a product/solutions/marketing page that reads as AI slop. The check: `grep -rnE '/solutions/products/|\.com/products/|/lp/|/our-platform|/our-demand-side-platform/' json/<platform>` must return nothing. Where a topic's only docs are gated behind a partner login (e.g., The Trade Desk), use the gated-docs `educate.learn_more_note` (rendered by the canvas Learn More `elif`) instead of a marketing page. Platforms with deep public help centers (Google, Meta, LinkedIn, DV360 via Google help) pass naturally; Amazon DSP and The Trade Desk did not until fixed.
5. **theme_tags are side-appropriate.** Every check carries valid slugs from `json/_themes.json` whose `sides` include the platform's side. The linter enforces this.
6. **New platforms** follow `~/.claude/rules/coding/auditmaton-ads-new-platform-prompt.md`. The platform must exist in `json/_platforms.json`; add a `CATEGORY_METADATA` block per category in `services/audit_engine.py`; update `specs/platform_tracker.csv`.
7. **Category names + icons are canonical across platforms, and an icon is NEVER reused for a different concept.** A category `display_name` that appears on more than one platform MUST use the same `icon_class` everywhere (same concept, same icon), and conversely each icon maps to exactly one concept, so a new category always gets its own unique icon, never one already in the table. Reuse the established name wherever the concept matches (don't coin synonyms). The canonical registry lives in the new-platform rule (`~/.claude/rules/coding/auditmaton-ads-new-platform-prompt.md`, "Canonical category names + icons"). Current set: Conversion Tracking `fa-bullseye`, Attribution `fa-route`, Campaigns `fa-rectangle-list`, Bidding `fa-hand-holding-dollar`, Targeting `fa-crosshairs`, Creative `fa-palette`, Measurement `fa-chart-line`, Governance `fa-scale-balanced`, Privacy `fa-user-shield`, Inventory `fa-boxes-stacked`, Brand Safety `fa-shield-halved`, Identity `fa-fingerprint`, Retail `fa-bag-shopping`, Coverage `fa-satellite-dish`, Fraud `fa-user-secret`, Viewability `fa-eye`, Audience `fa-users`, Monetization `fa-sack-dollar`, Buyers `fa-handshake`, Supply Chain `fa-link`, Delivery `fa-truck-fast`. A quick audit: `python3 -c "import services.audit_engine as e;from collections import defaultdict;d=defaultdict(set);[d[m['display_name']].add(m['icon_class']) for p in e.CATEGORY_METADATA.values() for m in p.values()];[print('CONFLICT',k,v) for k,v in d.items() if len(v)>1]"` prints nothing when consistent.
8. **Acronyms render with correct casing.** Subcategory display names are title-cased from the slug by `_format_display_name` in `services/audit_engine.py`, which lowercases acronyms ("creative_qa" -> "Creative Qa"). Every acronym a slug uses must be in the `DISPLAY_ACRONYMS` map there (QA, STV, ID, IO, PMP, AMC, ASIN, OpenPath, UID2, DSP, CM360, …); a standalone slug that means something special (e.g., `qa` as Q&A) goes in the `overrides` dict, checked first. When adding a platform, add its new acronyms and eyeball `/dashboard/<platform>/<category>/` — every subcategory label should read with correct casing.
9. **Every subcategory Overview has a Learn More link OR is genuinely gated.** The Overview panel (`category.html`) renders its "Learn more" link from the subcategory-level `google_guidance` field. An empty `google_guidance` drops the link. That is permitted ONLY when the topic's real docs are genuinely paywalled — evidenced by the subcategory's checks carrying the partner-portal `learn_more_note` (the established gated-docs messaging, as The Trade Desk uses platform-wide and Magnite uses for governance/ClearLine). When a public, readable, on-topic doc exists, `google_guidance` MUST be set to it. The link must be REAL, FETCH-VERIFIED documentation on the subcategory's topic: a vendor product-overview / "Welcome to X" / "/help/<product>" landing page is marketing, not docs, and is forbidden even at 200; a vendor help center that is a JS single-page app whose content WebFetch cannot read is unverifiable and must not be used. The approved bar (Google Ad Manager, Google Ads, Meta, LinkedIn, DV360) is the VENDOR'S OWN help center deep-linked to the exact topic (e.g., GAM -> `support.google.com/admanager/answer/<id>`). **Do NOT substitute third-party docs (Prebid, IAB, OWASP, MRC) for a missing vendor doc** — a generically-related third-party page reads as AI slop and users will flag it. When the platform's own help center is gated / login-required (Magnite, The Trade Desk), you cannot find or verify per-topic articles, so leave `google_guidance` EMPTY — except where a canonical public standard is the unambiguous, one-to-one reference for that exact subcategory (the only Magnite examples: `ads_txt` -> IAB ads.txt and `sellers_json` -> IAB sellers.json, because the audited file IS that spec). Everything else stays empty; the per-check `learn_more` citations still serve as the Educate-page references. Magnite final state: 2 Overview links (ads.txt, sellers.json), 25 empty.

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
3. **Nginx block** for `/tools/auditmaton/ad-audits/` → `127.0.0.1:8022` (staging) with `X-Forwarded-Prefix` + `X-Script-Name` set to the path segment; `sudo nginx -t && sudo systemctl reload nginx`.
4. **systemd `SCRIPT_NAME`** must match the path segment, or gunicorn 500s with a SCRIPT_NAME-mismatch error. `daemon-reload` after editing the unit.
5. **✅ Wait for Annie's sign-off on staging before prod.** Never deploy prod unprompted.
6. **Prod:** repeat on `~/apps/auditmaton-ads/` with port 8023 and the prod nginx/systemd files.

> The full step-by-step (venv, nginx block, systemd unit templates, troubleshooting) is identical to Cloud Kingdom's DEPLOY.md Parts 1–2 — follow that for the mechanics; this file owns the Auditmaton-specific variables, invariants, and the branch rule.

---

## Server security (all apps)

Per `~/.claude/rules/security/server-security.md`: never open ports without approval, web traffic only from Cloudflare ranges, gunicorn + DB bind to 127.0.0.1 only, no credentials in code (env vars only), HTTPS only. Confirm no change violates these before any server edit.
