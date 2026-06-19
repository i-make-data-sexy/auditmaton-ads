export const meta = {
  name: 'videoserver-author',
  description: 'Author one video/CTV ad-server platform (27 subcategory JSON files) in paced batches of 3',
  phases: [{ title: 'Author', detail: 'one agent per subcategory, batched 3 at a time' }],
}

const PLATFORMS = {
  'freewheel': {
    name: 'FreeWheel',
    notes: 'FreeWheel (a Comcast company) is a premium video and Connected TV (CTV) ad server and monetization platform used by broadcasters and large publishers to manage ad serving, ad pods, and both direct-sold and programmatic demand. Its console/operational docs are gated behind a partner login. IAB Tech Lab VAST/VMAP/ads.txt/sellers.json and OpenRTB specs are the public references for its standards-based mechanics.',
  },
}

const slug = (typeof args === 'string' ? args : (args && args.slug)) || 'freewheel'
const P = PLATFORMS[slug]
if (!P) throw new Error('unknown platform slug: ' + slug)

const SUBCATS = [
  { cat:'governance', sub:'account_structure', tags:['governance','compliance'],
    seed:`The publisher's ${P.name} account and entity structure (networks, supply partners, child accounts). Checks: (1) the account/entity hierarchy is organized cleanly so reporting and ownership are clear; (2) inactive or duplicate entities are identified and retired.` },
  { cat:'governance', sub:'roles_permissions', tags:['governance','compliance'],
    seed:`User access in the ${P.name} console. Checks: (1) user roles follow least privilege (admin access limited, departed staff removed); (2) API credentials / access tokens are scoped and rotated, not shared.` },
  { cat:'governance', sub:'naming_conventions', tags:['governance','data-quality'],
    seed:`Naming hygiene for ${P.name} supply tags, demand tags, and line items. Checks: (1) names follow a consistent, parseable convention so reporting can be sliced; (2) deal and campaign names are consistent and identifiable.` },
  { cat:'inventory', sub:'supply_tag_setup', tags:['inventory','data-quality'],
    seed:`How the publisher's video/CTV inventory is defined as supply tags/placements in ${P.name}. Checks: (1) supply tags declare the right ad sizes/durations/formats and map to the correct inventory; (2) no orphaned or mislabeled supply tags passing inventory under the wrong placement.` },
  { cat:'inventory', sub:'ad_pod_config', tags:['inventory','ad-experience'],
    seed:`CTV/OTT ad pod configuration in ${P.name}. Checks: (1) ad pod settings (pod duration, max ads per pod, slot structure, midroll cue points) are deliberate, not defaults; (2) competitive separation and frequency within pods are configured to protect the viewer experience. CTV = Connected TV.` },
  { cat:'inventory', sub:'vast_vmap_integration', tags:['inventory','creative'],
    seed:`VAST/VMAP and player integration with ${P.name}. Checks: (1) the VAST version and VMAP ad-break declarations are correct and the player passes required parameters (player size, content metadata); (2) macros and tracking are wired so impressions and quartiles fire. VAST = Video Ad Serving Template, VMAP = Video Multiple Ad Playlist.` },
  { cat:'delivery', sub:'demand_routing_priority', tags:['yield','performance'],
    seed:`How ${P.name} prioritizes and routes demand into each ad slot (direct-sold, programmatic, and house). Checks: (1) the priority/waterfall or unified-auction routing is deliberate so higher-value demand wins where it should; (2) routing does not starve programmatic or let house ads displace paid demand.` },
  { cat:'delivery', sub:'competitive_separation', tags:['ad-experience','brand-safety'],
    seed:`Competitive separation and creative dedup in ${P.name} ad pods and sessions. Checks: (1) advertiser/category competitive-separation rules prevent rival ads in the same pod; (2) session-level frequency and dedup prevent the same creative repeating across a viewing session.` },
  { cat:'delivery', sub:'pacing_under_delivery', tags:['yield','performance'],
    seed:`Pacing and delivery of guaranteed/direct-sold campaigns in ${P.name}. Checks: (1) line items pace smoothly toward their goals rather than front-loading or under-delivering; (2) under-delivery risk is monitored so make-goods and missed guarantees are caught early.` },
  { cat:'monetization', sub:'price_floors', tags:['yield','inventory'],
    seed:`Floor pricing in ${P.name}. Checks: (1) floors are set deliberately and segmented by inventory/format/geo/device rather than one flat number; (2) dynamic floors are evaluated against a fixed-floor baseline rather than accepted by default.` },
  { cat:'monetization', sub:'programmatic_demand', tags:['yield','performance'],
    seed:`Programmatic demand connections in ${P.name} (RTB/exchange and SSP connections feeding the video/CTV inventory). Checks: (1) the connected programmatic demand sources are justified and active, with timeouts tuned for the streaming environment; (2) duplicate or dormant connections are pruned.` },
  { cat:'monetization', sub:'yield_optimization', tags:['yield','performance'],
    seed:`Yield settings in ${P.name}. Checks: (1) auction dynamics and any demand throttling are reviewed so the publisher is not losing value; (2) the balance between direct-sold protection and programmatic yield is set deliberately.` },
  { cat:'buyers', sub:'programmatic_deals', tags:['yield','transparency'],
    seed:`PMP/PG deals running through ${P.name}. Checks: (1) deal health is monitored (deal IDs active, spending, not stalled); (2) deal floors and priorities are aligned so deals do not undercut or get undercut by other demand. PMP = Private Marketplace, PG = Programmatic Guaranteed.` },
  { cat:'buyers', sub:'direct_demand_partners', tags:['yield','transparency'],
    seed:`Direct-sold and demand-partner tags in ${P.name}. Checks: (1) direct demand tags and third-party demand partners are configured with correct priorities and budgets; (2) stale or non-performing demand tags are removed.` },
  { cat:'buyers', sub:'demand_tag_controls', tags:['yield','brand-safety'],
    seed:`Buyer/demand controls in ${P.name}. Checks: (1) advertiser/buyer allowlists and blocklists are maintained intentionally; (2) blocks are not so broad that they suppress legitimate demand and fill.` },
  { cat:'supply-chain', sub:'ads_txt', tags:['transparency','compliance'],
    seed:`ads.txt / app-ads.txt entries authorizing ${P.name} for the publisher's sites and CTV apps. Checks: (1) ads.txt/app-ads.txt lists the correct ${P.name} seller account ID with the right DIRECT or RESELLER designation; (2) no stale, duplicate, or unauthorized lines remain. Reference the IAB Tech Lab ads.txt/app-ads.txt spec.` },
  { cat:'supply-chain', sub:'sellers_json', tags:['transparency','compliance'],
    seed:`sellers.json + SupplyChain object (schain) for ${P.name}. Checks: (1) ${P.name}'s sellers.json entry matches the publisher's seller ID and relationship; (2) the SupplyChain object is complete and passed end to end. Reference IAB Tech Lab sellers.json and SupplyChain Object specs.` },
  { cat:'supply-chain', sub:'spo_reseller_hygiene', tags:['transparency','fraud'],
    seed:`Supply Path Optimization (SPO) and reseller/MFA hygiene for ${P.name} supply. Checks: (1) redundant or low-value reseller paths to the same inventory are minimized; (2) made-for-advertising (MFA) and unauthorized reseller risk is monitored and reduced. SPO = Supply Path Optimization, MFA = Made For Advertising.` },
  { cat:'brand-safety', sub:'ad_quality_scanning', tags:['brand-safety','ad-experience'],
    seed:`Creative quality and viewer-experience protection in ${P.name}. Checks: (1) creative scanning for malformed VAST, broken media files, slate/black-frame, and audio-loudness (CALM Act) issues is in place; (2) flagged creatives are blocked rather than left to run.` },
  { cat:'brand-safety', sub:'creative_blocking', tags:['brand-safety','creative'],
    seed:`Advertiser/category blocking controls in ${P.name}. Checks: (1) advertiser-domain and category block lists match the publisher's standards and any content-owner requirements; (2) blocks are not over-broad in a way that needlessly suppresses revenue.` },
  { cat:'brand-safety', sub:'content_classification', tags:['brand-safety','data-quality'],
    seed:`Content metadata and classification passed to demand in ${P.name}. Checks: (1) content genre, rating, and IAB content category signals are accurate so buyers target and apply safety correctly; (2) sensitive or mismatched content is flagged rather than mislabeled. Reference IAB Tech Lab Content Taxonomy.` },
  { cat:'privacy', sub:'consent_signals', tags:['privacy','compliance'],
    seed:`TCF / GPP consent and CTV privacy signals passing through ${P.name}. Checks: (1) the TCF or GPP consent string (web) and CTV privacy signals are captured and forwarded to demand; (2) bid/ad requests are limited where consent is absent and a legal basis is required. TCF = Transparency and Consent Framework, GPP = Global Privacy Platform.` },
  { cat:'privacy', sub:'us_state_privacy', tags:['privacy','compliance'],
    seed:`US state privacy signals via GPP through ${P.name}. Checks: (1) US national and state GPP sections are passed so opt-outs reach demand; (2) opt-out of sale/share is honored in the signal sent downstream. CCPA = California Consumer Privacy Act, CPRA = California Privacy Rights Act.` },
  { cat:'privacy', sub:'child_directed', tags:['privacy','compliance'],
    seed:`Child-directed / COPPA treatment on relevant ${P.name} inventory (kids programming on CTV). Checks: (1) child-directed inventory is flagged so personalized ads and certain data uses are suppressed; (2) restricted data processing applies to inventory likely to reach minors. COPPA = Children's Online Privacy Protection Act.` },
  { cat:'measurement', sub:'discrepancy_reconciliation', tags:['data-quality','performance'],
    seed:`Impression discrepancy between ${P.name} and downstream or upstream counts. Checks: (1) the ad-server-vs-demand or ad-server-vs-player impression discrepancy is measured and within an accepted tolerance; (2) discrepancy sources (timeouts, errored media, counting method) are investigated when out of range.` },
  { cat:'measurement', sub:'completion_viewability', tags:['data-quality','performance'],
    seed:`Video completion and viewability metric integrity in ${P.name}. Checks: (1) quartile and completion events are tracked and reconcile across player and ad server; (2) viewability measurement is integrated so buyers can value the impression. VTR = Video Through Rate.` },
  { cat:'measurement', sub:'reporting_accuracy', tags:['data-quality','transparency'],
    seed:`Revenue/fill reporting accuracy in ${P.name}. Checks: (1) reported revenue and fill reconcile against actual payments/remittances; (2) report dimensions and timezones are configured so the numbers are comparable across systems.` },
]

const REF = 'json/google-ad-manager/monetization/price_floors.json'

function buildPrompt(s) {
  return `You are authoring ONE audit subcategory JSON file for Auditmaton: Ads, the **${P.name}** platform (supply side). ${P.name} is a VIDEO/CTV AD SERVER. The audited user is a PUBLISHER or channel owner using ${P.name} to serve and monetize video/CTV ads.
Platform context: ${P.notes}

## File to write
\`json/${slug}/${s.cat}/${s.sub}.json\`
- category slug: "${s.cat}"; subcategory slug: "${s.sub}"
- theme_tags for every check: choose 2 from ${JSON.stringify(s.tags)} (supply-valid slugs from json/_themes.json)
- check id prefix: "${slug}-${s.sub.replace(/_/g,'-')}-..."

## Domain seed (verify against real docs; refine to ${P.name} specifics)
${s.seed}
Write 2-3 audit checks. impact_score honest: most config/hygiene checks 2-3; reserve 4-5 for catastrophic gaps.

## Schema — copy field-for-field from ${REF}
READ it first and replicate EXACTLY (top-level keys incl. google_guidance; each check: id,title,category,subcategory,impact_score,impact_rationale,has_chart=false,has_code_snippet=false,has_export=false,image_count=0,conditional=null,column_dependencies=[],theme_tags[],educate{base,site_type_overlays{publishing,ecommerce},learn_more[],impactful_updates[]},investigate{intro,tools{free{...},paid{}}},evaluate{logic,column_dependencies=[],export_available=false,fallback_message},visualizations=[],generate{narrative_template}).
- **Leave top-level \`google_guidance\` as empty string ""**.
- site_type_overlays: keep keys "publishing" and "ecommerce"; for a video/CTV ad server, frame "publishing" as a streaming/broadcaster context and "ecommerce" as a commerce-content video context.
- educate.base: 3-5 paragraphs separated by <br><br>; introduce any list with a complete standalone sentence + colon then <ul><li>...</li></ul>.
- generate.narrative_template uses {{voice_found}}, {{voice_recommend}} + gerund, {{site_name}}. Never second-person "you" in narrative_template.

## Citations (STRICT — graded)
Every educate.learn_more entry MUST be genuine, fetch-verified documentation. WebSearch then WebFetch to confirm the real on-topic article (not 404/redirect/login wall). DROP any you cannot confirm.
GENUINE sources: IAB Tech Lab specs (VAST, VMAP, ads.txt, app-ads.txt, sellers.json, SupplyChain Object, Content Taxonomy, GPP, Open Measurement), OpenRTB, IAB Europe (TCF), MRC/IAB measurement & viewability guidelines, FTC (COPPA), and ${P.name}'s own PUBLIC documentation if genuinely public.
NEVER a product/solutions/marketing page or homepage. 200 is NOT enough; judge what the page IS.
${P.name}'s own console/operational docs are largely GATED. When the only ${P.name}-specific source is gated, set educate.learn_more_note (string) like "${P.name}'s detailed configuration documentation for this is in the partner portal (login required)." and keep learn_more to genuinely-public standards entries only.

## Editorial rules (linted)
Follow ~/.claude/rules/editorial/audit-content-authoring.md. NO em/en-dashes, NO mid-sentence colons before a list in prose, NO comma before because/since, Oxford comma, "more than" not "over", "e.g.,"/"i.e.," with commas, single quotes for short labels with punctuation OUTSIDE, suggestive phrasing for diagnoses. NO editorializing ("is common","most/many publishers|broadcasters","tends to","quietly/silently","notoriously","often overlooked","almost never","in our experience"). Single-quoted HTML attrs inside JSON (class='tools-link-no-padding' on anchors).

## Before reporting (MANDATORY)
1. JSON parses. 2. Lint CLEAN: python3 scripts/lint_editorial.py json/${slug}/${s.cat}/${s.sub}.json --severity medium (fix until CLEAN). 3. google_guidance is "".
Return JSON: file, checks (number), citations_kept (array), used_learn_more_note (bool), lint_clean (bool).`
}

const SCHEMA = {
  type:'object', additionalProperties:false,
  properties:{ file:{type:'string'}, checks:{type:'number'}, citations_kept:{type:'array',items:{type:'string'}}, used_learn_more_note:{type:'boolean'}, lint_clean:{type:'boolean'} },
  required:['file','checks','lint_clean'],
}

const results = []
for (let i = 0; i < SUBCATS.length; i += 3) {
  const batch = SUBCATS.slice(i, i + 3)
  log(`${P.name} batch ${i/3 + 1}/${Math.ceil(SUBCATS.length/3)}: ${batch.map(b=>b.cat+'/'+b.sub).join(', ')}`)
  const r = await parallel(batch.map(s => () =>
    agent(buildPrompt(s), { label:`${slug}:${s.cat}/${s.sub}`, phase:'Author', schema:SCHEMA })))
  results.push(...r)
}
const ok = results.filter(Boolean)
return { platform:slug, files_written:ok.length, lint_clean:ok.filter(r=>r.lint_clean).length, total_checks:ok.reduce((n,r)=>n+(r.checks||0),0), note_used:ok.filter(r=>r.used_learn_more_note).length }
