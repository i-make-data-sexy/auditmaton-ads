Read CLAUDE.md, all JSON schema files, the intake form code, and the
dashboard routes.
 
Audit the entire codebase for overlap and consistency issues:
 
1. SCHEMA OVERLAP: Verify that Product schema content lives ONLY in
   json/shopping/ and NOT in json/rich-results/. Verify LocalBusiness
   schema lives ONLY in json/local/. Verify Recipe schema lives in
   json/rich-results/ (it is a Rich Result, not a conditional section).
 
2. SUBCHECK COUNTS: Recalculate the total subcheck count across all
   12 sections. Update CLAUDE.md and any mock data with accurate
   numbers. Rich Results count should note it's variable (based on
   intake selection) with a max and a typical number.
 
3. INTAKE → DASHBOARD FLOW: Verify that selections made at intake
   correctly determine:
   - Which conditional sections are unlocked (Shopping, Local, Intl)
   - Which Rich Results subchecks appear
   - Whether JavaScript section is active or deprioritized
   - Which site-type overlays load in Educate blocks
 
4. DUPLICATE CONTENT: Check for any educate content that's
   duplicated between AI/GEO and Rich Results. AI/GEO should cover
   LLM-focused markup (Speakable for AI consumption, llms.txt,
   entity optimization for LLMs). Rich Results should cover Google
   SERP-decoration schemas. If Speakable appears in both, determine
   which section owns it (recommendation: Rich Results, since
   Google lists it in their gallery).
 
5. NAMING CONSISTENCY: Ensure all JSON files use consistent keys for
   category names. Check that dashboard route category keys match
   the json/ directory names.
 
6. CONDITIONAL LOGIC: Verify the "Not sure which schemas" default
   auto-selection in intake produces a sensible set per site type.
 
Report all findings as comments in a new file:
specs/audit_overlap_report.md
 
Format: list each finding with severity (CRITICAL, WARNING, INFO),
the file(s) affected, and the recommended fix.
 
Do NOT make any code changes in this task. Only audit and report.
 