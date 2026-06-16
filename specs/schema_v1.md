# Schema v1 (manual-mode) — Inherited from Auditmaton: Tag Management

> **NOTE:** This spec was authored for the Tag Management edition. Adapt for the Ads edition taxonomy when the Demand/Supply category design is ready.

Status: **SUPERSEDED (2026-05-30).** The structured `manual_inputs` workbook
("Record Your Findings") was removed per Annie's direction. The auditor records
findings directly in the **Canvas** (free text), seeded by the **Generate**
boilerplate so they never start from a blank canvas; anything the auditor should
observe or note belongs in the **Investigate** steps. `manual_inputs` has been
stripped from all content JSON and is no longer rendered. The `manual_inputs`
shape documented below is retained for historical reference only. The rest of
the schema (the wrapper fields, the `-ate` framework, and the subcategory-level
`tier` that drives the Depth filter) is current.

## Why this exists

Auditmaton: Site keys every check to a crawl-CSV column via `column_dependencies`
(an array of `{canonical_key, display_default, required}`). It reads structured
data from an uploaded file.

Auditmaton: Tag Management has no upload and no API. Every check uses
`manual_inspection`: the practitioner inspects their own container in the Google
Tag Manager (GTM) UI, GTM Preview / Tag Assistant, browser DevTools, or
(rarely) Google Cloud Console, and records what they observed. The schema analog
for `column_dependencies` is `manual_inputs`.

All five cluster agents independently converged on `manual_inputs`. This document
reconciles their five near-identical proposals into one canonical shape.

## Canonical `manual_inputs` shape

```json
"manual_inputs": [
  {
    "input_key": "transport_url_present",
    "label": "Web container Google Tag has a transport_url",
    "input_type": "boolean",
    "required": true,
    "where_to_find": "Web container > Tags > Google Tag > Configuration settings > transport_url"
  },
  {
    "input_key": "initialization_trigger",
    "label": "CMP initialization trigger type",
    "input_type": "select",
    "options": ["Consent Initialization - All Pages", "All Pages", "DOM Ready", "Window Loaded", "Other"],
    "required": true,
    "where_to_find": "Open the CMP tag > Triggering"
  },
  {
    "input_key": "consent_tab_signals",
    "label": "Signals visible in Preview Consent tab",
    "input_type": "multiselect",
    "options": ["ad_storage", "analytics_storage", "ad_user_data", "ad_personalization", "None visible"],
    "required": true,
    "where_to_find": "GTM Preview > Consent tab"
  },
  {
    "input_key": "tag_count",
    "label": "Total tag count",
    "input_type": "integer",
    "required": false,
    "where_to_find": "Tags list pagination footer"
  },
  {
    "input_key": "pre_consent_firing_tags",
    "label": "Tags firing before consent (record names)",
    "input_type": "text_list",
    "required": false,
    "where_to_find": "Preview (cookies cleared, banner untouched) > each event > Tags Fired"
  },
  {
    "input_key": "notes",
    "label": "Practitioner notes",
    "input_type": "text",
    "required": false
  }
]
```

### Field definitions

| Field | Required | Notes |
|---|---|---|
| `input_key` | yes | snake_case, unique within the check. |
| `label` | yes | Human-readable prompt shown in the workbook. (Chosen over `display_label` for brevity; one name across all clusters.) |
| `input_type` | yes | One of the canonical types below. |
| `options` | only for `select` / `multiselect` | The allowed choices. |
| `required` | optional, default `true` | Whether the workbook blocks evaluation until answered. |
| `where_to_find` | optional but recommended | Exact GTM UI / Preview / DevTools / GCP path. Makes the workbook self-documenting and is the manual-mode analog of Auditmaton: Site's column-mapping hint. |
| `description` | optional | Longer guidance when `label` + `where_to_find` aren't enough. |

### Canonical `input_type` vocabulary

`boolean`, `select`, `multiselect`, `integer`, `text`, `text_list`.

Reconciliation of the five proposals:
- C1's `selection` and C2/C3/C4's `select` -> **`select`**.
- C1's `integer` -> kept.
- C4's `multiselect` and `text_list` -> kept (needed for signal sets and tag-name lists).
- C5's `url` -> folded into **`text`** (URL-format validation is a UI concern, not a distinct type).
- A universal optional `notes` (`text`) field is available on every check.

## Structured vs. freeform — recommendation

C4 and C5 both flagged that `text_list` is the least consistent type to implement
and that a freeform textarea might be simpler. The recommendation:

**Use structured types (`boolean` / `select` / `multiselect` / `integer`) for
every observation that has a discrete answer.** They drive deterministic
evaluate logic, render proper workbook controls, and produce clean, machine-
readable canvas output. Reserve `text_list` for genuine list captures (tag-name
inventories, e.g., pre-consent firing tags), and `text` for the universal
per-check `notes` field plus the handful of organizational/interview checks that
have no discrete answer (governance process, data-loss estimate).

This is a recommendation, not a lock. If you'd rather start v1 with a single
freeform textarea per check (faster to build, less structured canvas output),
the schema still supports it: a check whose `manual_inputs` is just one `text`
field works fine. **This is the one schema decision flagged for your call.**

## How `evaluate` changes

`evaluate.logic` no longer runs automated logic against uploaded columns. It reads
the practitioner's `manual_inputs` answers and resolves to pass / flag / fail.
`evaluate.fallback_message` becomes:

> "Complete the inspection steps above and record your findings to see the evaluation."

`generate.narrative_template` pulls the recorded `manual_inputs` values as its
dynamic variables, same mechanism as Auditmaton: Site, just sourced from the
workbook instead of a CSV.

`column_dependencies` is **dropped** from this edition's check schema (not kept as
an empty array, which would imply a mapping screen that doesn't exist).

## Intake gates (conditional content)

Auditmaton: Site gates categories by site type. This edition needs these intake
questions, each gating specific content:

| Intake question | Gates |
|---|---|
| "Do you run a server-side GTM (sGTM) container?" (Yes / No / Planning to) | Cluster 5 Category 1 (Server-Side Tagging) and Category 4 (Measurement Durability). "No" skips them with a summary card; "Planning to" opens them in read-only education mode. |
| "Do you run paid advertising on Meta, Google Ads, or TikTok?" | Cluster 5 `conversions-api.json` subcategory. |
| "Is your site a single-page application (SPA)?" | Cluster 2 `history-change-trigger-absent-on-spa` check. |
| "Does your site have ecommerce?" | Cluster 2/3 ecommerce checks (items array, purchase dedup, ecommerce dataLayer). |
| "Do you use GTM (free) or GTM 360?" | Cluster 1 workspace-cap thresholds; a future Zones subcategory. |

These follow Auditmaton: Site's conditional-category pattern. No new gating
mechanism is needed.
