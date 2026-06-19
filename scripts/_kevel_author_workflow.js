export const meta = {
  name: 'kevel-author',
  description: 'Author the Kevel platform (18 subcategory JSON files) in paced batches of 3',
  phases: [{ title: 'Author', detail: 'one agent per subcategory, batched 3 at a time' }],
}

const slug = 'kevel'
const NAME = 'Kevel'
const REF = 'json/google-ad-manager/monetization/price_floors.json'

// Kevel is a HEADLESS, API-first ad server. The audited user is a publisher,
// retail-media operator, or product team running their OWN ad platform on
// Kevel's Management API + Decision API. Kevel docs are fully PUBLIC at
// dev.kevel.com (/docs/... and /reference/...). NEVER use a learn_more_note
// (docs are public, not gated). NEVER a marketing page.
// The "ecommerce" site_type_overlay = RETAIL MEDIA (a retailer running
// sponsored-product ads via Kevel). The "publishing" overlay = a media site
// or app running a Kevel-powered ad server.

const SUBCATS = [
  { cat:'governance', sub:'api_keys_access', tags:['governance','data-quality'],
    docs:'dev.kevel.com/docs/manage-api-keys ; /reference/getting-started-with-kevel',
    seed:`How Kevel API keys and access are managed. Checks: (1) Management API keys are scoped, rotated, and kept server-side rather than shared or embedded in client code, since a Management key grants full control of the network; (2) Decision API key authentication is enabled where the network requires it (the X-Kevel-ApiKey header), and keys are not exposed in client-side requests.` },
  { cat:'governance', sub:'network_account_structure', tags:['governance','data-quality'],
    docs:'dev.kevel.com/docs/general-set-up-guide ; /docs/channels ; /docs/sites',
    seed:`How the network is organized. Kevel's structure is Advertisers, then Campaigns, then Flights, then Ads, alongside Sites, Zones, and Channels. Checks: (1) the advertiser, campaign, and flight hierarchy is organized so reporting and ownership are clear; (2) test or inactive advertisers, campaigns, and flights are retired rather than left able to serve.` },
  { cat:'governance', sub:'naming_conventions', tags:['governance','data-quality'],
    docs:'dev.kevel.com/docs/general-set-up-guide',
    seed:`Naming hygiene across the network. Checks: (1) advertisers, campaigns, flights, and zones follow a consistent, parseable naming convention so reporting can be sliced reliably; (2) custom targeting keys and zone names are consistent and self-describing rather than ad hoc.` },
  { cat:'inventory', sub:'site_zone_setup', tags:['inventory','data-quality'],
    docs:'dev.kevel.com/docs/sites ; /docs/zones-overview',
    seed:`How inventory is defined as Sites and Zones. A Zone is a placement that can include or exclude specific flights. Checks: (1) Sites and Zones map to real placements with correct include and exclude rules so flights serve where intended; (2) no orphaned or duplicate zones pass inventory under the wrong placement.` },
  { cat:'inventory', sub:'ad_types_templates', tags:['inventory','creative'],
    docs:'dev.kevel.com/docs/creative-templates ; /docs/ads',
    seed:`How ad types and creative templates are defined. Creative templates are predefined formats teams use to build creatives and ads. Checks: (1) ad types and creative templates exist for each format the network serves, with the required fields and macros, rather than each creative being built ad hoc; (2) templates validate and escape their inputs so a malformed creative cannot break rendering or inject unsafe markup.` },
  { cat:'inventory', sub:'ad_sizes_placements', tags:['inventory','ad-experience'],
    docs:'dev.kevel.com/docs/zones-overview ; /docs/creative-templates',
    seed:`How ad sizes and placements line up. Checks: (1) the ad sizes declared on zones and ad types match the placements and the demand trafficked against them, so a flight is not eligible for a placement it cannot fill cleanly; (2) placements are isolated so a creative does not overflow its zone or cause layout and user-experience problems on the page or app.` },
  { cat:'delivery', sub:'priority_flights', tags:['yield','performance'],
    docs:'dev.kevel.com/docs/flights ; /reference/create-flight ; /docs/priorities',
    seed:`How Priorities and flights decide which ad wins. Priorities are the business rules that determine precedence, set through a combination of Priorities or Waterfall tiers and Flights. Checks: (1) priority tiers are deliberate so higher-value flights win where they should and house ads serve only when paid demand is exhausted; (2) flight date ranges, weights, and priorities are set so flights compete as intended rather than starving one another.` },
  { cat:'delivery', sub:'frequency_capping', tags:['ad-experience','data-quality'],
    docs:'dev.kevel.com/docs/ad-frequency-capping ; /docs/frequency-capping-1 ; /docs/ad-capping',
    seed:`How frequency capping limits repetition. Caps can be set per advertiser, campaign, flight, or ad, by minute, hour, or day. Checks: (1) caps are set at the right level and interval for the inventory rather than left uncapped; (2) capping relies on a stable, persistent UserKey so the caps actually hold across requests rather than resetting when the identifier changes.` },
  { cat:'delivery', sub:'pacing', tags:['yield','performance'],
    docs:'dev.kevel.com/docs/ad-pacing-goals',
    seed:`How flights pace toward their goals. Pacing spreads delivery over time, and revenue or impression goals balance how a flight serves toward a target by its end date or per day. Checks: (1) flights with impression or revenue goals use pacing deliberately so they pace evenly rather than front-loading or under-delivering; (2) under-delivery risk is monitored so a flight at risk of missing its goal is caught early.` },
  { cat:'targeting', sub:'custom_targeting', tags:['inventory','data-quality'],
    docs:'dev.kevel.com/docs/custom-targeting ; /docs/passing-custom-targeting ; /docs/reserved-keys',
    seed:`How custom key-value targeting is set and passed. A custom targeting rule matches when the value for a key is passed in the Decision API request. Checks: (1) targeting rules reference keys that are actually passed in the request, so a typo or a missing key does not quietly drop the match; (2) reserved keys are not overloaded, and combined targeting logic (AND, OR, negation) resolves to what the team intends.` },
  { cat:'targeting', sub:'geo_keyword_targeting', tags:['inventory','data-quality'],
    docs:'dev.kevel.com/docs/geo-location ; /docs/keyword-targeting ; /docs/targeting-overview',
    seed:`How geo and keyword targeting are configured. Geo targeting works at the flight level by country, region, or metro. Keyword targeting serves a flight only where the matching keywords are passed in the ad code or Decision request. Checks: (1) geo targeting matches the campaign's intended markets and is not mistakenly including or excluding regions; (2) the keywords a flight targets match the keywords actually passed at request time.` },
  { cat:'targeting', sub:'userdb_audience', tags:['inventory','privacy'],
    docs:'dev.kevel.com/docs/userdb-1',
    seed:`How UserDB is used for audience targeting. UserDB is a first-party, server-side data store keyed to a persistent UserKey, holding interest, behavior, and frequency data. Checks: (1) UserKeys are stable and first-party so audience and frequency data persists correctly rather than fragmenting across identifiers; (2) what is written to UserDB is governed (which interests and segments, and for how long) rather than accumulating unbounded personal data.` },
  { cat:'privacy', sub:'consent_handling', tags:['privacy','compliance'],
    docs:'dev.kevel.com/docs/gdpr-compliance-and-consent-settings ; /reference/gdpr-consent ; /docs/gdpr-kevel',
    seed:`How user consent is captured and honored. GDPR consent is set per UserKey through the consent endpoint and defaults to false unless explicitly set, and Kevel honors it whenever that UserKey is used. Checks: (1) consent is recorded per user and honored on Decision requests, rather than left at the default; (2) requests from a consent region with no recorded consent are handled so personalized targeting and UserDB use are suppressed. GDPR = General Data Protection Regulation.` },
  { cat:'privacy', sub:'data_retention', tags:['privacy','compliance'],
    docs:'dev.kevel.com/docs/kevel-data-processing-agreement ; /docs/privacy-policy-customers',
    seed:`How data retention is governed. Campaign configuration and UserDB first-party data are stored until removed, while transient personal data such as an IP address is retained only briefly during serving. Checks: (1) UserDB retention is bounded so first-party user data is not kept longer than the use requires; (2) what is written to UserDB and to logs is reviewed so personally identifiable information (PII) is minimized. PII = personally identifiable information.` },
  { cat:'privacy', sub:'child_directed', tags:['privacy','compliance'],
    docs:'dev.kevel.com/docs/gdpr-compliance-and-consent-settings ; /docs/privacy-policy-customers ; FTC COPPA rule (ftc.gov)',
    seed:`How inventory directed at children is handled. Because Kevel is a headless platform, COPPA compliance falls to the operator who builds on it. Checks: (1) inventory directed at children suppresses UserDB profiling and personalized targeting so it does not rely on behavioral data, as the Children's Online Privacy Protection Act (COPPA) requires; (2) personal data is not collected through UserDB for users known to be children. COPPA = Children's Online Privacy Protection Act.` },
  { cat:'measurement', sub:'reporting_api', tags:['data-quality','transparency'],
    docs:'dev.kevel.com/docs/request-reporting ; /docs/standard-logs-1',
    seed:`How delivery is reconciled through reporting. The Reporting API and Data Shipping logs (impression, click, custom event, and conversion logs) pull delivery data into the operator's own systems. Checks: (1) reporting or the shipped logs are used to reconcile served impressions, clicks, and revenue rather than trusting the UI total alone; (2) report dimensions and time zones are configured so the numbers are comparable across the operator's systems.` },
  { cat:'measurement', sub:'event_tracking', tags:['data-quality','performance'],
    docs:'dev.kevel.com/docs/conversion-tracking ; /docs/custom-event-tracking ; /docs/tracking-overview',
    seed:`How impressions, clicks, and conversions are tracked. The Decision API returns impression and click URLs, and conversion pixels live at the advertiser level. Checks: (1) impression and click trackers fire correctly, server-side or by pixel, so counts are accurate and an impression is counted once; (2) conversion and custom-event tracking is wired (pixel or server-to-server) so outcomes attribute to the right advertiser and flight.` },
  { cat:'measurement', sub:'decision_logging', tags:['data-quality','transparency'],
    docs:'dev.kevel.com/docs/standard-logs-1 ; /docs/tracking-overview ; /docs/beta-logs',
    seed:`How Decision API activity is logged and watched. Kevel ships standard logs (impression, click, event, conversion) and UserDB logs that record the decisions and user activity. Checks: (1) the logs are shipped and retained so delivery can be audited and debugged after the fact; (2) the logs are monitored for errors such as unfilled decisions or errored requests, rather than collected and ignored.` },
]

function buildPrompt(s) {
  return `You are authoring ONE audit subcategory JSON file for Auditmaton: Ads, the **${NAME}** platform (supply side). ${NAME} is a HEADLESS, API-first ad server. The audited user is a publisher, retail-media operator, or product team that runs their OWN ad platform on Kevel's Management API and Decision API. This is an implementation and configuration audit of that Kevel setup.

## File to write
\`json/${slug}/${s.cat}/${s.sub}.json\`
- category slug: "${s.cat}"; subcategory slug: "${s.sub}"
- theme_tags for every check: choose 2 from ${JSON.stringify(s.tags)} (supply-valid slugs from json/_themes.json)
- check id prefix: "${slug}-${s.sub.replace(/_/g,'-')}-..."

## Domain (verify against the real docs; refine to Kevel specifics)
${s.seed}
Write exactly 2 audit checks (one per intent above). impact_score honest: config/hygiene checks are 2-3; reserve 4-5 only for a catastrophic gap (e.g., a Management API key exposed client-side = 4, or PII collected from children = 4).

## Schema — copy field-for-field from ${REF}
READ ${REF} FIRST and replicate its structure EXACTLY (top-level keys incl. google_guidance; each check: id,title,category,subcategory,impact_score,impact_rationale,has_chart=false,has_code_snippet=false,has_export=false,image_count=0,conditional=null,column_dependencies=[],theme_tags[],educate{base,site_type_overlays{publishing,ecommerce},learn_more[],impactful_updates[]},investigate{intro,tools{free{...},paid{}}},evaluate{logic,column_dependencies=[],export_available=false,fallback_message},visualizations=[],generate{narrative_template}).
- **Leave top-level \`google_guidance\` as empty string ""** (the coordinator sets Overview links later).
- investigate.tools.free: use keys like "kevel_ui" (label "Kevel UI") for the dashboard, and/or "kevel_management_api" (label "Kevel Management API") for GET endpoints, and/or "kevel_decision_api" (label "Kevel Decision API") where the check is verified in a live ad request or the shipped logs. Steps are concrete inspection steps (open Settings, then API Keys; GET the flights/zones via the Management API; inspect a Decision API response; read the Data Shipping logs).
- site_type_overlays: keep keys "publishing" and "ecommerce". Frame "publishing" as a media site or app running a Kevel-powered ad server, and "ecommerce" as RETAIL MEDIA (a retailer running sponsored-product ads on its own site or app through Kevel).
- educate.base: 3-5 paragraphs separated by <br><br>; introduce any list with a COMPLETE standalone sentence ending in a colon, then <ul><li>...</li></ul> (never a fragment like "Signs include:").
- generate.narrative_template uses {{voice_found}}, {{voice_recommend}} + a gerund, and {{site_name}}. Never second-person "you" in narrative_template.

## Citations (STRICT — graded). Kevel docs are PUBLIC at dev.kevel.com, so you MUST cite real public docs. Do NOT use a learn_more_note.
Each educate.learn_more entry MUST be genuine, fetch-verified documentation. Load WebFetch/WebSearch via ToolSearch ("select:WebFetch" / "select:WebSearch") if not already available. Confirm each URL returns the real on-topic article (not a 404, redirect-to-home, or login wall). DROP any you cannot confirm.
GENUINE sources for Kevel (all public):
- dev.kevel.com/docs/...  and  dev.kevel.com/reference/...  (Kevel's own developer documentation) — candidates for THIS subcategory: ${s.docs}
- A controlling public standard ONLY where it is the one-to-one reference for the topic (e.g., the FTC COPPA rule for child-directed treatment, IAB specs where relevant). Use this sparingly and only when it genuinely IS the reference.
NEVER a product, solutions, pricing, or marketing page (e.g., kevel.com/solutions, kevel.com/product). A 200 status is necessary but NOT sufficient — judge what the page IS (developer documentation vs. marketing).
Anchor format inside JSON strings, when you embed a link in prose: <a href='URL' class='tools-link-no-padding' target='_blank'>anchor text</a> (single-quoted attributes).

## Editorial rules (linted — zero tolerance)
Follow ~/.claude/rules/editorial/audit-content-authoring.md. NO em/en-dashes; NO mid-sentence colons before a list/example/question in prose; NO comma before because/since; Oxford comma; "more than" not "over" for quantities; "e.g.,"/"i.e.," with the comma; single quotes for short labels with punctuation OUTSIDE the quote; suggestive phrasing for diagnoses ("you may want to consider", not "you should"). NO editorializing: do not write "is common", "most/many operators|retailers|publishers", "tends to", "quietly/silently" + verb, "notoriously", "often overlooked", "almost never", "in our experience". Spell out each abbreviation once on first use per rendered passage, then bare (API, SDK, UserDB, GDPR, COPPA, PII, PMP).

## Before reporting (MANDATORY)
1. The file is valid JSON (parse it). 2. Lint CLEAN: \`python3 scripts/lint_editorial.py json/${slug}/${s.cat}/${s.sub}.json --severity medium\` (fix and re-run until it prints CLEAN). 3. Confirm top-level google_guidance is "". 4. No duplicate abbreviation expansion on the same rendered page (expand once at first use, bare after).
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
    agent(buildPrompt(s), { label:`kevel:${s.cat}/${s.sub}`, phase:'Author', schema:SCHEMA })))
  results.push(...r)
}
const ok = results.filter(Boolean)
return { platform:slug, files_written:ok.length, lint_clean:ok.filter(r=>r.lint_clean).length, total_checks:ok.reduce((n,r)=>n+(r.checks||0),0) }
