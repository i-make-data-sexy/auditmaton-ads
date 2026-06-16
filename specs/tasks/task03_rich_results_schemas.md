Read CLAUDE.md for all coding and content conventions.
Read json/ai-geo/ for the reference JSON schema format.
 
Create a new directory json/rich-results/ and build JSON schema files.
 
IMPORTANT: Each schema file's educate content must follow Google's
official guidance at:
https://developers.google.com/search/docs/appearance/structured-data/search-gallery
 
Do NOT include before/after code snippets. Instead, the investigate
section should direct users to these three free validator tools with
step-by-step instructions for each:
 
1. Google Rich Results Test
   https://developers.google.com/search/docs/appearance/structured-data
2. Schema.org Validator
   https://validator.schema.org/
3. Technical SEO Schema Generator
   https://technicalseo.com/tools/schema-markup-generator/
 
Before writing individual schemas, first use web_fetch to read
Google's structured data documentation for each type to ensure
accuracy. The educate section must cover:
- What the schema type does and its SERP visual treatment
- Eligibility requirements
- Required vs recommended properties (per Google, not Schema.org)
- Common implementation mistakes
- Google's official documentation link
 
START with these 10 high-priority schema types (batch 1):
1. article.json — Article
2. faq.json — FAQ
3. event.json — Event
4. breadcrumb.json — Breadcrumb
5. video.json — Video
6. organization.json — Organization
7. course_list.json — Course list
8. review_snippet.json — Review snippet
9. speakable.json — Speakable
10. discussion_forum.json — Discussion forum
 
For event.json, include site_type_overlays for:
- Educational: lecture series, commencement, recurring academic events,
  multi-speaker handling
- Professional Services: webinars, multi-speaker conferences,
  hybrid attendance modes
- Healthcare: support groups, health fairs, clinic events
- Local Business: community workshops, seasonal events
 
Each file follows the standard schema structure with:
- id, title, category ("rich_results"), subcategory
- A "google_doc_url" field linking to the specific Google docs page
- educate, investigate, evaluate, validate, generate blocks
- Use {{domain}} and {{domain_bare}} template variables
 
Do NOT create schemas for types owned by conditional sections:
- Product/Shopping schema → lives in json/shopping/
- LocalBusiness schema → lives in json/local/
- Recipe schema → lives in json/rich-results/ UNLESS the user also
  selected Recipe as a site type, but the schema still lives here
  since Recipe is a SERP decoration, not a conditional section.
 
Wait. Recipe is a Rich Result AND a site type. The Recipe JSON goes in
json/rich-results/recipe.json with heavy site_type_overlays for the
Recipe site type. It is NOT excluded like Product and LocalBusiness.
 
Do NOT use spaced em dashes. Do NOT use horizontal rules.
 