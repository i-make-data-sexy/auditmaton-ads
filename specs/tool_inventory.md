# Auditmaton for Site Audits — Tool Inventory

Tools are surfaced in the **Investigate** section of each check, filtered by what the user selects at intake. Each tool tab shows instructions specific to that tool's UI and features.

## Crawl Tools
Primary data source for the audit upload. Also used for many Investigate checks beyond the initial crawl.

**Screaming Frog SEO Spider**
- Primary use: Full site crawl, crawl data export
- Additional features relevant to checks: robots.txt viewer, redirect chains, canonicalization report, hreflang audit, structured data extraction, page speed integration (via API), JavaScript rendering, custom extraction, log file import
- Export format: CSV, Excel, Google Sheets

**Sitebulb**
- Primary use: Full site crawl with visual reporting
- Additional features: Hints system (prioritized issues), crawl path visualization, internal link analysis, Core Web Vitals integration, structured data audit, accessibility checks
- Export format: CSV, Excel

**Ahrefs Site Audit**
- Primary use: Cloud-based crawl + SEO issue detection
- Additional features: Health score, internal link report, content audit, redirect report, hreflang checker, page speed
- Export format: CSV

**Semrush Site Audit**
- Primary use: Cloud-based crawl + issue prioritization
- Additional features: Core Web Vitals, internal linking, HTTPS check, structured data, log file analysis (enterprise), content audit
- Export format: CSV, PDF

**Moz Pro Site Crawl**
- Primary use: Issue detection and site health scoring
- Additional features: Page optimization, internal link explorer, redirect checker
- Export format: CSV

**Screaming Frog Log File Analyser** *(separate product from SEO Spider)*
- Primary use: Server log file analysis — see exactly what Googlebot crawled, how often, and what it ignored
- Relevant checks: Log File Analysis (Crawl section), Crawl Budget
- Conditional: Only surfaced in Investigate when server log access confirmed at intake
- Export format: CSV
- Note: Pairs naturally with Screaming Frog SEO Spider for cross-referencing crawl data against actual bot behavior

**Lumar** *(formerly Deepcrawl)*
- Primary use: Enterprise-scale cloud crawl with deep technical analysis
- Additional features: robots.txt analysis, JavaScript rendering, crawl budget optimization, log file integration, Core Web Vitals monitoring, accessibility auditing, change detection
- Export format: CSV, API
- Note: Designed for large, complex sites — particularly strong at crawl budget and indexability analysis

**Botify**
- Primary use: Enterprise crawl platform combining crawler, log analyzer, and search analytics
- Additional features: robots.txt analysis, JavaScript crawl, crawl budget analysis (via log files), render comparison, content quality analysis, keyword tracking integration
- Export format: CSV, API
- Note: Unique strength in combining crawl data with server log data and search analytics in a single platform

**SEO PowerSuite (WebSite Auditor)**
- Primary use: Desktop-based site crawl and on-page audit
- Additional features: robots.txt editor and tester, content optimization, page speed analysis, schema validation, site structure visualization
- Export format: CSV, PDF
- Note: Desktop tool (not cloud-based). Part of the SEO PowerSuite alongside Rank Tracker, SEO SpyGlass, and LinkAssistant

## SEO Research & Backlink Tools
Used primarily in Investigate sections — not for crawl data upload.

**Ahrefs**
- Relevant checks: Backlink profile, keyword cannibalization, content gap, broken backlinks, anchor text analysis, brand mentions, competitor research
- Unique feature: Content Explorer for brand citation research (relevant to AI/GEO)

**Semrush**
- Relevant checks: Backlink audit / toxic links, keyword cannibalization, content gap, brand monitoring, local listing audit, position tracking
- Unique feature: Semrush .Trends for traffic analysis

**Moz Pro**
- Relevant checks: Backlink profile, spam score, link intersect, brand authority signals
- Unique feature: Domain Authority and Page Authority metrics

**Majestic**
- Relevant checks: Backlink profile, Trust Flow / Citation Flow, topical trust flow
- Niche use: Deep backlink history, link context analysis

**Similarweb**
- Relevant checks: Competitor traffic analysis, traffic source breakdown, audience overlap, industry benchmarking, keyword gap analysis
- Unique feature: Estimated traffic data for any domain without requiring access; industry and category benchmarking
- Note: Not a traditional SEO audit tool but valuable for competitive context and traffic validation. Has an SEO module for keyword and organic research

## Enterprise SEO Platforms
Full-stack SEO platforms with crawl, research, rank tracking, and reporting capabilities. Typically used by large organizations and agencies managing multiple domains at scale.

**Conductor**
- Primary use: Enterprise SEO and content intelligence platform
- Relevant checks: Technical site audit (robots.txt, indexability, page speed), content performance, keyword visibility, competitive intelligence
- Unique feature: Conductor Intelligence integrates organic, paid, and content data for cross-channel insights
- Note: Enterprise pricing; primarily used by large brands and agencies

**BrightEdge**
- Primary use: Enterprise SEO and content performance platform
- Relevant checks: Technical SEO audit, page-level recommendations, content optimization, competitive analysis, rank tracking
- Unique feature: Data Cube for large-scale keyword universe analysis; StoryBuilder for automated reporting
- Note: Enterprise pricing; strong in competitive intelligence and automated recommendations

**seoClarity**
- Primary use: Enterprise SEO platform with deep crawl and analytics
- Relevant checks: Technical site audit (Clarity Audits), robots.txt analysis, crawl budget optimization, rank tracking, content optimization, competitive analysis
- Unique feature: Clarity Audits provides enterprise-scale crawl with configurable audit rules; Research Grid for unlimited keyword data
- Note: Enterprise pricing; known for large-scale data access and customizable audit rules

## Google Native Tools
Free. Should always be included as a default option in every Investigate section where applicable.

**Google Search Console**
- Relevant checks: Indexability, coverage report, robots.txt tester, sitemap submission, Core Web Vitals report, mobile usability, rich results status, hreflang errors, manual actions, crawl stats
- Note: Required for most Crawl and Mobile checks

**Google Analytics (GA4)**
- Relevant checks: Content freshness (traffic trends), thin content (engagement signals), content gap (landing page performance), local traffic signals
- Note: Not a crawl tool but provides critical context for many content checks

**Google PageSpeed Insights**
- Relevant checks: Core Web Vitals (LCP, CLS, INP), page speed, mobile performance
- Note: Free, no login required

**Google Rich Results Test**
- Relevant checks: Structured data validation, schema eligibility for rich results
- Note: Free, no login required

**Google Search (Manual)**
- Relevant checks: Knowledge Panel verification, entity establishment, brand mentions, site: operator checks, AI Overview visibility
- Note: Free, no login required

**Bing Webmaster Tools**
- Relevant checks: Sitemap submission, indexability, crawl report, SEO analyzer
- Note: Often overlooked but relevant for International and broader crawl checks

## Local SEO Tools
Relevant only when Local Business site type is selected at intake.

**BrightLocal**
- Relevant checks: NAP consistency audit, citation tracking, GBP audit, local rank tracking, review monitoring
- Unique feature: Citation Tracker covers hundreds of directories

**Whitespark**
- Relevant checks: Local citation finder, GBP audit, reputation management
- Unique feature: Local rank tracker with map pack results

**Yext**
- Relevant checks: NAP consistency at scale, citation management, GBP sync
- Note: More of a management platform than an audit tool — relevant for enterprise local clients

## Tag Management Tools
Relevant across Crawl, Content, Mobile, and AI/GEO sections. Surfaced in Investigate steps where JavaScript-based implementations create crawlability or accuracy risks.

**Google Tag Manager**
- Relevant checks: JavaScript-based redirects, canonicals or hreflang implemented via GTM, schema markup via GTM, page speed / GTM container bloat, GA4 implementation verification
- Note: Industry standard, free, most widely used
- Key risk: Tags that fire client-side only are invisible to crawlers

**Tealium**
- Relevant checks: Same as GTM — tag firing verification, schema via Tealium, page speed impact
- Note: Enterprise standard — common in retail, finance, and healthcare stacks

**Adobe Experience Platform Launch** *(formerly Adobe DTM)*
- Relevant checks: Same as GTM — tag auditing, firing rules, page speed
- Note: Common in large enterprise environments running Adobe stack (AEM, Analytics, Target)

**Ensighten**
- Relevant checks: Tag firing verification, page speed contribution
- Note: Older enterprise tool still in use at some large organizations

**Segment**
- Relevant checks: Data layer verification, event tracking accuracy
- Note: Primarily a CDP but used for tag orchestration by some teams — more relevant to the future Analytics Audit


Used in Investigate sections for Mobile, Crawl, and Media checks.

**Lighthouse** *(built into Chrome DevTools)*
- Relevant checks: Core Web Vitals, page speed, accessibility, mobile usability, best practices
- Note: Free, no login required

**GTmetrix**
- Relevant checks: Page speed, LCP, CLS, waterfall analysis, performance history
- Note: Free tier available

**WebPageTest**
- Relevant checks: Advanced performance testing, filmstrip view, CWV deep dive, mobile simulation
- Note: Free, highly trusted

**Chrome DevTools**
- Relevant checks: Rendering issues (CSS/JS blocking), mobile simulation, network requests, robots.txt header inspection
- Note: Free, built into Chrome

## Schema & Structured Data Tools
Used in Investigate sections for Shopping, AI/GEO, Local, and Media checks.

**Google Rich Results Test**
- Relevant checks: Product schema, FAQ schema, review schema, VideoObject, LocalBusiness, BreadcrumbList
- Note: Free, authoritative

**Schema Markup Validator** *(schema.org)*
- Relevant checks: General schema validation across all types
- Note: Free, broader coverage than Rich Results Test

**Merkle Schema Markup Generator**
- Relevant checks: Code snippet generation for Investigate before/after examples
- Note: Free tool, useful reference for audit recommendations

## Content & AI Visibility Tools
Relevant for AI/GEO section. This category has matured rapidly — over $77M flowed into AI SEO tracking startups in mid-2025 alone. Tools range from manual LLM checks to full enterprise GEO platforms.

### Manual / Free AI Checks
Always available regardless of intake selections.

**Perplexity AI** *(manual check)*
- Relevant checks: Brand mention visibility in AI-generated answers, citation tracking
- Note: Free to use manually

**ChatGPT / Claude / Gemini** *(manual check)*
- Relevant checks: Brand awareness in LLM responses, entity clarity testing
- Note: Manual prompt testing — "What do you know about [brand]?", "What are the best [category] companies?"

**Google AI Overviews / AI Mode** *(manual check)*
- Relevant checks: Whether AI Overviews appear for target queries, whether brand is cited in AI-generated answers
- Note: Free. Check directly in Google Search. AI Mode available via Google Labs.

**HubSpot AEO Grader**
- Relevant checks: Quick diagnostic of brand's AI search performance across GPT-4o, Perplexity, and Gemini
- Note: Free. Entry-level awareness tool — not a full monitoring platform
- URL: https://www.hubspot.com/aeo-grader

**Mangools AI Search Grader**
- Relevant checks: Quick diagnostic of how AI search engines reference your brand
- Note: Free companion to Mangools' paid AI Search Watcher
- URL: https://mangools.com/ai-search-grader

### AI Visibility Features in Existing SEO Platforms
These are AI visibility modules within platforms already listed elsewhere in this inventory. They are surfaced when the user selects the parent platform at intake.

**Semrush AI Visibility Toolkit**
- Relevant checks: Brand visibility, share of voice, citations, and sentiment across ChatGPT, Google AI Overviews, Gemini, Claude, Grok, Perplexity, and DeepSeek
- Note: Part of Semrush One ($199+/month). Integrates AI visibility alongside traditional SEO metrics

**Ahrefs Brand Radar**
- Relevant checks: Brand visibility across 243M+ monthly prompts across ChatGPT, Perplexity, Gemini, Copilot, Google AI Overviews, and Google AI Mode
- Note: Add-on to Ahrefs subscription ($199/month per AI platform index, or $699/month for all 6)

**BrightEdge AI Catalyst**
- Relevant checks: Brand presence across ChatGPT, Perplexity, and Google AI Overviews. Share of voice, content optimization guidance
- Note: Enterprise pricing. Launched April 2025

**Conductor AI**
- Relevant checks: AI citation monitoring, AEO/GEO benchmarking, content optimization for AI visibility
- Note: Enterprise pricing. Published industry's first large-scale AEO/GEO benchmarks report (3.3B sessions, 13K+ domains)

**seoClarity ArcAI**
- Relevant checks: Brand mentions and content triggers across ChatGPT, Gemini, Perplexity, and Google AI Overviews
- Note: Enterprise pricing. Links AI visibility patterns with optimization suggestions

**Surfer SEO AI Tracker**
- Relevant checks: Brand/topic mentions across ChatGPT, Google AI Overviews/AI Mode, Perplexity, Gemini. One prompt tracks across all 5 models simultaneously
- Note: Add-on ($95/month for 25 prompts). Requires Surfer base subscription

### Purpose-Built AI Visibility / GEO Platforms
Dedicated platforms focused entirely on AI search visibility and optimization.

**Profound**
- Relevant checks: Brand mentions, citations, and sentiment across ChatGPT, Perplexity, Google AI Overviews. URL watchlist for tracking specific pages' AI citations over time
- Note: Paid ($99–$399+/month). Well-funded ($58.5M total). SOC 2 Type II compliant. Used by Ramp, US Bank
- URL: https://www.tryprofound.com

**Evertune**
- Relevant checks: AI Brand Score, Visibility Score, Average Position across LLMs. Uses demographically weighted panel of 25M users for statistically significant analytics. Shopping Intelligence for AI-powered product recommendations
- Note: Paid (enterprise-oriented). $19M raised. Founded by early Trade Desk team members
- URL: https://www.evertune.ai

**Peec AI**
- Relevant checks: Distinguishes "used" (content informed the answer) vs. "cited" (URL explicitly mentioned) sources. Covers ChatGPT, Perplexity, Google AI Overviews/AI Mode, Copilot, DeepSeek, Grok
- Note: Paid (EUR 89–499+/month). Berlin-based, EUR 21M Series A
- URL: https://peec.ai

**Goodie AI**
- Relevant checks: Brand visibility across ChatGPT, Gemini, Perplexity, Claude, Copilot, DeepSeek. Sentiment analysis, multi-location/multi-client support
- Note: Paid ($495+/month). Recognized as a leading GEO platform in independent rankings
- URL: https://www.goodie.ai

**Scrunch AI**
- Relevant checks: Agent Experience Platform (AXP) — creates machine-readable content versions for AI agents. Tracks visibility across ChatGPT (including Shopping), Perplexity, Claude, Meta AI, Gemini, Google AI Overviews/AI Mode
- Note: Paid ($300–$500+/month). Distinctive approach focused on making content AI-agent-readable
- URL: https://www.scrunch.ai

**Otterly AI**
- Relevant checks: Automated brand monitoring across Google AI Overviews, ChatGPT, Gemini, and Perplexity
- Note: Paid ($29–$989/month). Simple, accessible entry point for AI visibility tracking
- URL: https://otterly.ai

### Mid-Market AI Visibility Tools

**Mangools AI Search Watcher**
- Relevant checks: Brand mentions across ChatGPT, Gemini, Claude, Mistral, and Llama. Runs prompts multiple times for accurate averages
- Note: Paid ($15.60+/month annual). One of the most affordable options
- URL: https://mangools.com/ai-search-watcher/

**SE Ranking AI Search / SE Visible**
- Relevant checks: ChatGPT visibility tracking (AI Search add-on) and strategic AI visibility insights across Google AI Mode, AI Overviews, Gemini, Perplexity, ChatGPT (SE Visible)
- Note: Paid (~$65+/month for SE Ranking; SE Visible has separate pricing)
- URL: https://seranking.com/ai-visibility-tracker.html

**Nightwatch**
- Relevant checks: LLM monitoring, prompt research, citation-level sentiment analysis alongside traditional rank tracking
- Note: Paid (add-on to existing rank tracking subscription)
- URL: https://nightwatch.io/ai-tracking/

**Authoritas AI Tracker**
- Relevant checks: Deconstructs AI answers to capture full content, differentiating between listings, citations, and carousel items. Direct API integration with Gemini, ChatGPT, Claude, DeepSeek
- Note: Paid (enterprise pricing). Technically deep, granular analysis
- URL: https://www.authoritas.com/ai-search/llm-brand-visibility-tracking

### Enterprise AI / GEO Platforms

**Adobe LLM Optimizer**
- Relevant checks: AI-driven traffic monitoring (AI crawlers, LLM assistants, AI browsers), brand visibility benchmarking across generative platforms, ML-driven optimization recommendations
- Note: Enterprise pricing (part of Adobe Experience Cloud). GA launched October 2025. Adobe saw 1,100% YoY increase in AI traffic to U.S. retail sites
- URL: https://business.adobe.com/products/llm-optimizer.html

### Content Monitoring

**ContentKing**
- Relevant checks: Content freshness monitoring, real-time change detection
- Note: Continuous monitoring platform — relevant for content freshness checks

## Tool Tiers for Intake Form

At intake, present tools grouped by category so users can select all that apply:

**Crawl Tools** — Screaming Frog, Sitebulb, Ahrefs Site Audit, Semrush Site Audit, Moz Pro Site Crawl, Lumar, Botify, SEO PowerSuite (WebSite Auditor), Other

**SEO Research Tools** — Ahrefs, Semrush, Moz Pro, Majestic, Similarweb, Other

**Enterprise Platforms** — Conductor, BrightEdge, seoClarity, Other, None

**AI Visibility Tools** — Profound, Evertune, Peec AI, Goodie AI, Scrunch AI, Otterly AI, Mangools AI Search Watcher, SE Ranking / SE Visible, Nightwatch, Authoritas, Adobe LLM Optimizer, Other, None

**Google Tools** — Google Search Console, Google Analytics, Both, Neither

**Local Tools** *(shown only if Local Business selected)* — BrightLocal, Whitespark, Yext, Other, None

**Tag Manager** — Google Tag Manager, Tealium, Adobe Experience Platform Launch, Ensighten, Segment, Other, None

**Performance Tools** — PageSpeed Insights, GTmetrix, WebPageTest, None

Free tools (Google PageSpeed Insights, Rich Results Test, Schema Validator, Chrome DevTools, Lighthouse, HubSpot AEO Grader, Mangools AI Search Grader) are always included in Investigate instructions regardless of intake selections — they require no login and no cost.

Note: AI visibility features within existing platforms (Semrush AI Visibility, Ahrefs Brand Radar, BrightEdge AI Catalyst, Conductor AI, seoClarity ArcAI, Surfer AI Tracker) are automatically surfaced when the user selects the parent platform at intake — they do not need to be selected separately.
