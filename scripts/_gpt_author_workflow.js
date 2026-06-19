export const meta = {
  name: 'gpt-author',
  description: 'Author the Google Publisher Tag platform (18 subcategory JSON files) in paced batches of 3',
  phases: [{ title: 'Author', detail: 'one agent per subcategory, batched 3 at a time' }],
}

const slug = 'google-publisher-tag'
const NAME = 'Google Publisher Tag'
const REF = 'json/google-ad-manager/monetization/price_floors.json'

// GPT has fully PUBLIC docs. Two genuine Google doc homes (same vendor):
//   developers.google.com/publisher-tag/  (library guides + /reference + /samples)
//   support.google.com/admanager/        (GAM help center, for conceptual GAM-side topics)
// Plus IAB taxonomy specs / web.dev Core Web Vitals where a standard is the reference.
// NEVER use learn_more_note (docs are public, not gated). NEVER a marketing page.

const SUBCATS = [
  { cat:'governance', sub:'library_loading', tags:['governance','performance'],
    docs:'developers.google.com/publisher-tag/common_implementation_mistakes ; /guides/get-started ; /guides/general-best-practices',
    seed:`How the publisher loads the GPT library on their pages. Checks: (1) GPT is loaded only from the official Google source (securepubads.g.doubleclick.net/tag/js/gpt.js), not a self-hosted or third-party copy that can go stale or be tampered with; (2) the library is loaded asynchronously and all calls go through the googletag.cmd command queue, so render is not blocked and there are no race conditions before the library is ready.` },
  { cat:'governance', sub:'service_config', tags:['governance','data-quality'],
    docs:'developers.google.com/publisher-tag/guides/get-started ; /guides/config-migration ; /common_implementation_mistakes ; /reference',
    seed:`How GPT services and page-level configuration are set up. Checks: (1) page-level settings (targeting, privacy, SRA) are applied before googletag.enableServices() is called, since settings made after enableServices may not take effect; (2) configuration uses the current setConfig config API rather than deprecated per-method setters slated for removal.` },
  { cat:'governance', sub:'csp_integration', tags:['governance','compliance'],
    docs:'developers.google.com/publisher-tag/guides/content-security-policy',
    seed:`How GPT coexists with the page's Content Security Policy (CSP). Checks: (1) the CSP allowlists the Google ad-serving and SafeFrame domains GPT needs, so a tightened policy does not silently block ad requests or rendering; (2) where a strict nonce-based CSP is used, the nonce is propagated so GPT and its creatives are not blocked. CSP = Content Security Policy.` },
  { cat:'inventory', sub:'slot_definition', tags:['inventory','data-quality'],
    docs:'developers.google.com/publisher-tag/guides/get-started ; /reference (defineSlot)',
    seed:`How ad slots are defined with defineSlot(). Checks: (1) the ad unit path passed to defineSlot matches the ad unit hierarchy trafficked in Google Ad Manager (GAM), so requests resolve to the right inventory; (2) the div id passed to defineSlot matches the container div present on the page at display() time, so slots are not left unfilled. GAM = Google Ad Manager.` },
  { cat:'inventory', sub:'ad_sizes', tags:['inventory','creative'],
    docs:'developers.google.com/publisher-tag/guides/ad-sizes',
    seed:`How ad sizes are declared per slot. Checks: (1) responsive inventory uses size mappings (defineSizeMapping) so the right sizes serve per viewport, rather than one fixed size across all screens; (2) the sizes declared in GPT are actually eligible (trafficked) in GAM, so declared sizes are not requesting demand that cannot fill.` },
  { cat:'inventory', sub:'out_of_page_slots', tags:['inventory','ad-experience'],
    docs:'developers.google.com/publisher-tag/guides/get-started ; /reference (defineOutOfPageSlot, OutOfPageFormat)',
    seed:`How out-of-page formats (interstitial, anchor, rewarded) are implemented. Checks: (1) supported out-of-page formats use GPT-managed slots (defineOutOfPageSlot with an OutOfPageFormat) rather than hand-built floating divs, so Google manages placement and frequency; (2) out-of-page units are configured so they do not overlap content or cause layout and user-experience problems.` },
  { cat:'delivery', sub:'single_request_architecture', tags:['inventory','performance'],
    docs:'developers.google.com/publisher-tag/guides/ad-best-practices ; /common_implementation_mistakes',
    seed:`Whether Single Request Architecture (SRA) is used on multi-slot pages. Checks: (1) enableSingleRequest() is on for pages with several slots, so all slots are fetched in one request, which roadblocks and competitive exclusions depend on and which reduces request overhead; (2) slots are batch-defined and displayed together rather than defined and displayed one at a time, which defeats SRA bundling. SRA = Single Request Architecture.` },
  { cat:'delivery', sub:'lazy_loading', tags:['performance','inventory'],
    docs:'developers.google.com/publisher-tag/guides/control-ad-loading ; /guides/ad-best-practices',
    seed:`Whether and how lazy loading is configured. Checks: (1) on long pages, lazy loading (disableInitialLoad plus a fetchMarginPercent set via setConfig) is used so off-screen ads are not all requested up front, which wastes requests and depresses viewability; (2) the fetch and render margins are tuned so ads load shortly before they enter the viewport rather than too late (blank slots) or too early (no benefit).` },
  { cat:'delivery', sub:'ad_refresh', tags:['yield','ad-experience'],
    docs:'developers.google.com/publisher-tag/guides/ad-best-practices ; /guides/control-ad-loading',
    seed:`How ad refresh is implemented with refresh(). Checks: (1) refresh is gated on viewability and a sensible minimum interval and respects Google Ad Manager refresh policy, rather than refreshing on a blind timer; (2) on refresh, targeting and the correlator are handled correctly so the refreshed request is counted and targeted as intended.` },
  { cat:'targeting', sub:'key_value_targeting', tags:['inventory','data-quality'],
    docs:'developers.google.com/publisher-tag/guides/key-value-targeting ; /common_implementation_mistakes',
    seed:`How key-value targeting is passed. Checks: (1) page-level key-values are set with setTargeting before enableServices(), since values set afterward may not reach the request; (2) the keys and values sent by GPT match the custom targeting keys defined in Google Ad Manager, so line items and bidders can actually target them.` },
  { cat:'targeting', sub:'publisher_provided_signals', tags:['inventory','privacy'],
    docs:'support.google.com/admanager (Publisher provided signals / PPS) ; developers.google.com/publisher-tag/reference ; IAB Tech Lab Audience Taxonomy 1.1 / Content Taxonomy 2.2',
    seed:`Whether Publisher Provided Signals (PPS) are sent to improve programmatic value without sharing user identifiers. Checks: (1) PPS are configured so first-party audience and content signals reach bidders; (2) the signals use the supported IAB audience and content taxonomies and Google structured signals correctly, rather than ad hoc values that bidders cannot interpret. PPS = Publisher Provided Signals.` },
  { cat:'targeting', sub:'audience_targeting', tags:['inventory','privacy'],
    docs:'support.google.com/admanager (Publisher provided identifiers / PPID ; Secure signals) ; developers.google.com/publisher-tag/reference (setPublisherProvidedId)',
    seed:`How first-party audience continuity is passed through GPT. Checks: (1) where first-party audience or frequency continuity is needed, a Publisher Provided Identifier (PPID) is set via setPublisherProvidedId; (2) secure signals (first-party data shared with selected bidders) are configured where the publisher intends bidders to receive them, rather than left off by default. PPID = Publisher Provided Identifier.` },
  { cat:'privacy', sub:'privacy_settings', tags:['privacy','compliance'],
    docs:'developers.google.com/publisher-tag/reference (setPrivacySettings) ; support.google.com/admanager (Restricted Data Processing / RDP ; consent)',
    seed:`Whether setPrivacySettings reflects the page's consent state. Checks: (1) setPrivacySettings is wired to the consent management platform so non-personalized ads, restricted data processing, and related flags follow the user's actual consent rather than a hardcoded default; (2) restricted data processing (RDP) is signaled where US state privacy opt-outs require it. RDP = Restricted Data Processing.` },
  { cat:'privacy', sub:'child_directed', tags:['privacy','compliance'],
    docs:'developers.google.com/publisher-tag/reference (tagForChildDirectedTreatment, tagForUnderAgeOfConsent) ; support.google.com/admanager (child-directed / COPPA)',
    seed:`Whether child-directed treatment is tagged where required. Checks: (1) on child-directed content, tagForChildDirectedTreatment is set so personalized ads and certain data uses are suppressed, as the Children's Online Privacy Protection Act (COPPA) requires; (2) where the audience may include users under the age of consent in the EEA, tagForUnderAgeOfConsent is set. COPPA = Children's Online Privacy Protection Act.` },
  { cat:'privacy', sub:'limited_ads', tags:['privacy','compliance'],
    docs:'support.google.com/admanager (limited ads) ; developers.google.com/publisher-tag/reference',
    seed:`Whether limited ads are configured to serve where consent is absent. Checks: (1) limited ads serving is enabled so an ad can still serve with limited data use when a user in a consent region has not consented, rather than serving nothing; (2) the limited ads variant of the GPT library (the limited-ads gpt.js endpoint) is loaded where limited ads are intended, since the standard library does not serve limited ads.` },
  { cat:'measurement', sub:'slot_render_events', tags:['data-quality','performance'],
    docs:'developers.google.com/publisher-tag/reference (events: SlotRenderEndedEvent) ; /samples/ad-event-listeners',
    seed:`Whether GPT slot events are used to monitor delivery. Checks: (1) the slotRenderEnded event is listened to so unfilled (empty) slots are detected and handled, for example collapsing the slot; (2) event listeners are registered before display() is called, since listeners added after a slot renders miss its events.` },
  { cat:'measurement', sub:'performance_monitoring', tags:['performance','data-quality'],
    docs:'developers.google.com/publisher-tag/guides/monitor-performance ; /guides/minimize-layout-shift ; web.dev Core Web Vitals',
    seed:`Whether the performance impact of ads is measured. Checks: (1) a Core Web Vitals baseline exists so the effect of GPT and ad changes on page performance can be measured rather than guessed; (2) layout shift caused by ad slots is measured and the slot space is reserved (min-height or aspect ratio) so ads do not push content and inflate Cumulative Layout Shift (CLS). CLS = Cumulative Layout Shift.` },
  { cat:'measurement', sub:'viewability_events', tags:['data-quality','performance'],
    docs:'developers.google.com/publisher-tag/reference (events: ImpressionViewableEvent) ; support.google.com/admanager (Active View)',
    seed:`Whether viewability is tracked client-side and reconciled. Checks: (1) the impressionViewable event is captured so the publisher can analyze which slots are seen, rather than relying on reporting alone; (2) client-side viewability signals are reconciled with Google Ad Manager Active View so the two measurements are understood rather than assumed identical.` },
]

function buildPrompt(s) {
  return `You are authoring ONE audit subcategory JSON file for Auditmaton: Ads, the **${NAME}** platform (supply side). ${NAME} (GPT) is the JavaScript ad request and render library a PUBLISHER runs on their own web pages to request ads from Google Ad Manager (GAM). The audited user is a PUBLISHER (or their developer) who has implemented GPT on their site. This is a developer/implementation audit of the GPT setup, not an account audit.

## File to write
\`json/${slug}/${s.cat}/${s.sub}.json\`
- category slug: "${s.cat}"; subcategory slug: "${s.sub}"
- theme_tags for every check: choose 2 from ${JSON.stringify(s.tags)} (supply-valid slugs from json/_themes.json)
- check id prefix: "${slug}-${s.sub.replace(/_/g,'-')}-..."

## Domain (verify against the real docs; refine to GPT specifics)
${s.seed}
Write exactly 2 audit checks (one per intent above). impact_score honest: config/hygiene checks are 2-3; reserve 4-5 only for a catastrophic gap (e.g., COPPA tagging entirely absent on child-directed inventory = 4).

## Schema — copy field-for-field from ${REF}
READ ${REF} FIRST and replicate its structure EXACTLY (top-level keys incl. google_guidance; each check: id,title,category,subcategory,impact_score,impact_rationale,has_chart=false,has_code_snippet=false,has_export=false,image_count=0,conditional=null,column_dependencies=[],theme_tags[],educate{base,site_type_overlays{publishing,ecommerce},learn_more[],impactful_updates[]},investigate{intro,tools{free{...},paid{}}},evaluate{logic,column_dependencies=[],export_available=false,fallback_message},visualizations=[],generate{narrative_template}).
- **Leave top-level \`google_guidance\` as empty string ""** (the coordinator sets Overview links later).
- investigate.tools.free: use a key like "gpt_console" (label "Google Publisher Console") for the in-page GPT debugging console, and/or "browser_devtools" (label "Browser DevTools"), and/or "gam_ui" (label "Google Ad Manager UI") where the check is verified in GAM. Steps are concrete inspection steps (open the Publisher Console with the googfc bookmarklet or ?googfc, read the network request to securepubads, check defineSlot calls, etc.).
- site_type_overlays: keep keys "publishing" and "ecommerce". Frame "publishing" as a media/content site running GPT, and "ecommerce" as a commerce-content site running GPT (product/category pages).
- educate.base: 3-5 paragraphs separated by <br><br>; introduce any list with a COMPLETE standalone sentence ending in a colon, then <ul><li>...</li></ul> (never a fragment like "Signs include:").
- generate.narrative_template uses {{voice_found}}, {{voice_recommend}} + a gerund, and {{site_name}}. Never second-person "you" in narrative_template.

## Citations (STRICT — graded). GPT docs are PUBLIC, so you MUST cite real public docs. Do NOT use a learn_more_note here.
Each educate.learn_more entry MUST be genuine, fetch-verified documentation. Load WebFetch/WebSearch via ToolSearch ("select:WebFetch" / "select:WebSearch") if not already available. Confirm each URL returns the real on-topic article (not a 404, redirect-to-home, or login wall). DROP any you cannot confirm.
GENUINE sources for GPT (all public, all Google's own or a controlling standard):
- developers.google.com/publisher-tag/  (the guides, the /reference API page, the /samples) — candidates for THIS subcategory: ${s.docs}
- support.google.com/admanager/answer/...  (Google Ad Manager help center, Google's own docs — for GAM-side concepts like PPS, PPID, secure signals, RDP, child-directed, limited ads, Active View). WebSearch within support.google.com/admanager to find the exact answer page, then WebFetch to confirm.
- IAB Tech Lab taxonomy specs (only where the standard IS the reference, e.g., PPS taxonomies) and web.dev / Core Web Vitals (for performance/CLS).
NEVER a product, solutions, or marketing page. A 200 status is necessary but NOT sufficient — judge what the page IS (documentation vs. marketing).
Anchor format inside JSON strings, when you embed a link in prose: <a href='URL' class='tools-link-no-padding' target='_blank'>anchor text</a> (single-quoted attributes).

## Editorial rules (linted — zero tolerance)
Follow ~/.claude/rules/editorial/audit-content-authoring.md. NO em/en-dashes; NO mid-sentence colons before a list/example/question in prose; NO comma before because/since; Oxford comma; "more than" not "over" for quantities; "e.g.,"/"i.e.," with the comma; single quotes for short labels with punctuation OUTSIDE the quote; suggestive phrasing for diagnoses ("you may want to consider", not "you should"). NO editorializing: do not write "is common", "most/many publishers|sites", "tends to", "quietly/silently" + verb, "notoriously", "often overlooked", "almost never", "in our experience". Spell out each abbreviation once on first use per rendered passage, then bare (GPT, GAM, CLS, SRA, RDP, PPS, PPID, COPPA, CSP).

## Before reporting (MANDATORY)
1. The file is valid JSON (parse it). 2. Lint CLEAN: \`python3 scripts/lint_editorial.py json/${slug}/${s.cat}/${s.sub}.json --severity medium\` (fix and re-run until it prints CLEAN). 3. Confirm top-level google_guidance is "".
Return JSON: { file, checks (number), citations_kept (array of the verified URLs), lint_clean (bool) }.`
}

const SCHEMA = {
  type:'object', additionalProperties:false,
  properties:{ file:{type:'string'}, checks:{type:'number'}, citations_kept:{type:'array',items:{type:'string'}}, lint_clean:{type:'boolean'} },
  required:['file','checks','lint_clean'],
}

const results = []
for (let i = 0; i < SUBCATS.length; i += 3) {
  const batch = SUBCATS.slice(i, i + 3)
  log(`${NAME} batch ${i/3 + 1}/${Math.ceil(SUBCATS.length/3)}: ${batch.map(b=>b.cat+'/'+b.sub).join(', ')}`)
  const r = await parallel(batch.map(s => () =>
    agent(buildPrompt(s), { label:`gpt:${s.cat}/${s.sub}`, phase:'Author', schema:SCHEMA })))
  results.push(...r)
}
const ok = results.filter(Boolean)
return { platform:slug, files_written:ok.length, lint_clean:ok.filter(r=>r.lint_clean).length, total_checks:ok.reduce((n,r)=>n+(r.checks||0),0) }
