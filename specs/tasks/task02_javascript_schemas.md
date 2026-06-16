Read CLAUDE.md for all coding and content conventions.
Read json/ai-geo/ for the reference JSON schema format.
 
Create a new directory json/javascript/ and build JSON schema files
for these 8 subchecks:
 
1. js_rendering.json — JavaScript Rendering (how Googlebot processes
   JS, two-wave indexing, rendering delays)
2. rendering_method.json — Rendering Method Assessment (CSR vs SSR
   vs SSG vs ISR vs dynamic rendering)
3. critical_content_visibility.json — Critical Content Visibility
   (is primary content in initial HTML or only after JS execution)
4. internal_link_discovery.json — Internal Link Discovery (links in
   DOM vs generated via JS event handlers)
5. lazy_loading.json — Lazy Loading & Infinite Scroll (content behind
   JS-triggered lazy loading)
6. js_redirects.json — JavaScript Redirects (client-side vs
   server-side, how Google handles each)
7. url_inspection_rendered.json — URL Inspection: HTML vs Rendered
   (GSC URL Inspection tool, comparing initial vs rendered HTML)
8. resource_blocking.json — Resource Blocking (JS/CSS blocked by
   robots.txt preventing rendering)
 
Each file must follow the established schema with:
- id, title, category ("javascript"), subcategory
- impact_score and impact_rationale
- educate block with base text and site_type_overlays where relevant
- investigate block with tool-specific tabs
- evaluate, validate, generate placeholder blocks
- Use {{domain}} and {{domain_bare}} template variables
- Follow all em dash, colon, and content conventions from CLAUDE.md
 
For investigate tabs, the relevant tools are:
- Google Search Console (URL Inspection, Coverage reports)
- Screaming Frog (JS rendering mode, rendered page comparison)
- Chrome DevTools (View Source vs Inspect comparison)
- Google Rich Results Test (shows rendered HTML)
- web.dev / Lighthouse (JS-related audits)
 
Do NOT use spaced em dashes. Do NOT use horizontal rules.
 