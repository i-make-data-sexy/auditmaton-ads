Read specs/site_types_and_taxonomy.md (the artifact Annie exported).
Update CLAUDE.md with the following changes:
 
1. Replace the "Audit Taxonomy" section with the new 12-section structure:
 
   Universal (9 sections):
   1. Crawl
   2. Content
   3. Links
   4. Media
   5. Mobile
   6. E-E-A-T
   7. AI/GEO
   8. Rich Results (subchecks determined by intake schema selection)
   9. JavaScript
 
   Conditional (3 sections):
   10. Shopping (Ecommerce only)
   11. Local (Local Business only)
   12. International (flagged at intake)
 
2. Update the site type list to match the new tiers:
   Tier 1: Ecommerce, Healthcare/Wellness, Recipe, Publishing/News,
           Local Business, Financial/Legal
   Tier 2: Educational, Professional Services
 
3. Add a new "Rich Results" section explaining:
   - Subchecks are dynamic based on intake checkbox selection
   - Content follows Google's structured data gallery exactly (https://developers.google.com/search/docs/appearance/structured-data/search-gallery)
   - No before/after code; instead reference validator tools
   - Overlap handling: Shopping owns Product schema, Local owns
     LocalBusiness schema, these are auto-excluded from Rich Results
 
4. Add a new "JavaScript" section with the 8 subchecks listed in
   the taxonomy doc.
 
5. Update the total subcheck count (it's no longer 74; recalculate
   based on the new sections).
 
6. Add intake form additions:
   - Rich Results schema checkbox list (after site type)
   - JavaScript framework question
   - International yes/no flag
 
Do NOT change any other parts of CLAUDE.md. Only update the sections
described above.
 