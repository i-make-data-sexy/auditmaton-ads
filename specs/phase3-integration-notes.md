# Phase 3 Integration Notes — Inherited from Auditmaton: Tag Management

> **NOTE:** These integration notes were authored for the Tag Management edition's GTM taxonomy. They are carried here as reference only. The Ads edition taxonomy design starts fresh.

Coordinator synthesis of the five cluster taxonomy drafts in `_taxonomy_drafts/`.
Status: awaiting Annie's review. No JSON authored yet.

## Check inventory tally

| Cluster | Categories | Subcategories | Checks |
|---|---|---|---|
| 1 — Container Hygiene & Governance | 4 | 11 | 29 |
| 2 — Tag Firing & Triggers | 4 | 6 | 25 |
| 3 — Variables & dataLayer | 4 | 9 | 31 |
| 4 — Privacy, Consent & Compliance | 4 | 7 | 31 |
| 5 — Server-Side Tagging & Vendor | 4 | 8 | 26 |
| **Total** | **20** | **41** | **142** |

Impact distribution skews correctly: most checks are 2-3 (config/hygiene),
impact-5 reserved for data-corrupting or legally-exposing failures (doubled
purchase events, PII to GA4, pre-consent firing in regulated regions, missing
transport URL).

### Rebalance / scoping flags

- **142 checks is a lot for a v1 manual audit.** Each is a guided manual
  inspection step. Consider tiering into "core" vs. "maintenance/advanced" so the
  default flow isn't 142 mandatory steps. Cluster 3's own note nominates its
  lower-impact checks (8, 9, 13, 15, 26, 31) for a maintenance tier; the same
  logic applies across clusters. **Product decision for Annie.**
- No category exceeds the 25-subcategory ceiling or falls below 3 checks. Two
  Cluster 2 categories (`trigger-configuration`, `conversion-ecommerce-firing`)
  have a single subcategory each; fine, but they could absorb a sibling later.

## Boundary overlaps — resolutions

1. **Universal Analytics / legacy tags.** Owner: **Cluster 1** (`container-bloat`:
   `paused-tags-ua-legacy`, `active-ua-tags`). Clusters 2 and 3 correctly excluded
   UA and handed off. Clean, no duplicate checks. No action.

2. **Consent-init firing order.** Cluster 2 has `consent-initialization-before-
   google-tag`; Cluster 4 owns the entire consent-mode treatment. Resolution:
   **Cluster 4 owns consent depth.** Cluster 2 keeps a slim firing-order symptom
   check that cross-references the Cluster 4 `consent-mode` subcategory. Avoid two
   full checks on the same concern.

3. **PII / sensitive data.** Split by destination. **Cluster 3** owns PII reaching
   GA4/analytics (`data-quality-security`). **Cluster 4** owns PII reaching ad
   platforms (Customer Match / advanced matching) and the consent dimension
   (`data-governance`). Cross-reference. Watch the one true near-duplicate:
   C3 `sensitive-data-ga4-event-params` vs C4 `sensitive-category-restrictions` —
   keep C3 = GA4 event params, C4 = ad-targeting audiences.

4. **Vendor tags.** **Cluster 5** owns vendor governance, sprawl, duplicate
   double-tracking, and retired-vendor inventory (`vendor-sprawl`). **Cluster 1**
   owns the GA4-migration legacy artifacts (UA specifically) plus paused/orphaned
   cleanup. Cross-reference C1 `inactive-vendor-pixels` <-> C5
   `vendor-retired-tags-present` so they don't both fully adjudicate vendor status.

5. **Duplicate hits vs. duplicate tools.** Cluster 2 (`duplicate-tags-same-hit`,
   `ga4-pageview-fires-twice`) = the data-corruption/firing lens. Cluster 5
   (`vendor-duplicate-analytics-pixels`) = the vendor-inventory lens. Different
   lenses, keep both, cross-reference.

6. **Custom HTML, three lenses.** C3 = security/risk (`document.write`, injection,
   third-party script code). C4 = consent gating (`custom-html-consent-gating`).
   C5 = performance + third-party domain inventory. Legitimate separate lenses;
   cross-reference so one inspection pass covers all three. Dedup the inventory:
   **C5 owns the third-party script-domain inventory (Network tab); C3 owns the
   per-tag code-risk review.**

7. **Tag sequencing.** **Cluster 5** owns the dependency-graph checks
   (`tag-sequencing-dependencies-documented`, `...-no-circular-dependencies`).
   **Cluster 2** keeps the "is sequencing configured where a setup tag is needed"
   firing-symptom check (`tag-sequencing-misconfigured`). Cross-reference.

8. **Server-side consent passthrough — same check proposed twice.** C4's proposed
   `server-side-container-consent-passthrough` and C5's proposed
   `consent-signal-forwarded-to-server` are the same check. Resolution: **one
   check, owned by Cluster 4** (consent owns consent correctness), gated on the
   sGTM intake flag, cross-referenced from Cluster 5. **Confirm placement with
   Annie.**

9. **Constant variables / hardcoded IDs — self-overlap inside Cluster 3.**
   `constant-variables-for-ids` (variable-configuration) and `hardcoded-ids-vs-
   variables` (data-quality-security) are the same concern. **Merge into one
   check in variable-configuration, cross-reference from data-quality.**

10. **Ecommerce items array — two ends of one pipe.** C2 `ecommerce-items-array-
    populated` (tag reads a populated items array) and C3 `datalayer-ecommerce-
    items-array` (dataLayer push uses GA4 items structure). Keep both as
    push-side vs. read-side, cross-reference.

11. **Redundant "move Consent Mode to a Privacy cluster" suggestions.** C1 and C3
    both suggested a dedicated consent home. Cluster 4 IS that home. Drop those
    new-check suggestions as already satisfied. Same for C3's "GTM environments"
    suggestion (Cluster 1 already owns `environments.json`).

## Out-of-GTM-UI checks (manual-mode strain)

About 20 of 142 checks need evidence the GTM UI does not surface; each has a
proposed workbook substitute in its draft. Concentration:

- **Cluster 5: 13 of 26 (50%)** — DevTools (Network/Application/Performance),
  Google Cloud Console (region, min instances), DNS/SSL tools. The category intro
  must list access prerequisites up front (DevTools on the live site, GCP Console,
  DNS access).
- Cluster 1: 3 (2FA status, "preview used before publish", vendor-still-active).
- Cluster 4: 3 (IAB TCF vendor-list lookup, Google Signals in GA4 Admin, CMP
  consent log).
- Cluster 3: 1 governance item (third-party vendor approval). Several others use
  DevTools/console, which is standard practitioner tooling.
- Cluster 2: 0 hard blockers (purchase-dedup wants the Network tab, standard).

## Consolidated [VERIFY] TODO for Annie

### A. GTM currency confirmations (UI/feature, as of 2026)
- Workspace cap on free containers (still 3?).
- Tag Assistant canonical name + whether the in-GTM Preview pane still exists as a fallback.
- Permission tier names (Read/Edit/Approve/Publish still current?).
- 1,000-tag soft-ceiling: current Google doc reference.
- Whether the Universal Analytics tag template is still in the GTM picker.
- Enhanced Conversions UI path (Customer data tab vs. separate tag type).
- GA4 "Redact Sensitive Data" exact scope (named params vs. heuristic).
- GA4 default data retention (2026) and whether GTM has any role.
- TikTok Events API GTM template status + dedup parameter name (v1.3+).
- Meta Event Match Quality score scale + availability (2026).
- GA4 "Measurement Accuracy" indicator naming (2026).
- Optional chaining vs. IE11 support assumption.

### B. Legal / privacy framing (your judgment)
- Switzerland (revFADP) in the EEA region list?
- Whether `functionality_storage` / `security_storage` / `personalization_storage`
  belong in the default consent call.
- `url_passthrough` privacy framing.
- Basic vs. Advanced Consent Mode: steer toward Advanced (bump `ga4-consent-built-in`
  to impact 4) or present both as valid?
- US-state handling depth.
- Whether Google's own tags need a TCF string or Consent Mode signals suffice.
- Overall hedging level on the legal-adjacent checks (currently "recommend
  confirming with counsel", no conclusions stated).

### C. Product / structure decisions
- Intake questions to add (see `schema_v1.md`): sGTM, paid-ads/CAPI, SPA,
  ecommerce, GTM free vs. 360.
- Structured vs. freeform `manual_inputs` (recommendation: structured; see
  `schema_v1.md`).
- Sample-based vs. full enumeration for large containers (orphan checks).
- UX for interview/process checks (questionnaire vs. guided UI tour).
- Category naming: "Container Bloat & Deprecation" vs. "Legacy Cleanup & Deprecation".
- Zones subcategory for GTM 360 (defer to v2 unless audience includes 360 users).
- Core vs. maintenance/advanced tiering for the 142-check flow.
- Placement of the single server-side consent-passthrough check (recommend Cluster 4).
- Whether process checks get their own "Governance" subcategory or stay inline.
