---
name: edu-base-writer
description: Instructions and examples for rewriting educate.base fields in SEO audit JSON checks. Use when rewriting, improving, or generating base education copy for audit checks.
---

# EDU BASE WRITER

## What This Field Is For

The `educate.base` field explains an SEO issue to a practitioner who already
knows what SEO is. 

It should NOT:
- Define basic terms (e.g., don't explain what a breadcrumb is)
- Pad with generic advice
- Reference required or optional data types or properties
- Be a tutorial on how to fix the issue
- Delve into technical details (Ex: "The markup uses the BreadcrumbList type containing an ordered array of ListItem objects. Each ListItem requires a position (integer), a name (text label), and an item (URL), except for the final item in the list, which omits the URL since it represents the current page.")
- Prompt the user to use Google's Rich Results Test to validate their markup or request re-indexing.

It SHOULD:
- Sentence 1: Explain why the fix is important without ever saying explicitly things like "This is important because..." or "This matters because..." 
- Sentence 2+: Provide practical tips with a focus on making Google's best practices digestable using the guidance from the Google Central page or Google Blog for that issue (e.g., tips from the "Author markup best practices" section of https://developers.google.com/search/docs/appearance/structured-data/article)
- Focus on the business case for why a particular fix should be made without delving into the gritty, technical details

## Formatting
- Wrap all references to html in <code> if it's inline and <pre> if it's a code block
- Only use lists if there are at least 3 items
- Only use ordered lists if there's an implicit order (e.g., steps or list items with some kind of hierarchy)
- If a code block is inside a list apply the <pre><code> to the li not the ul (Ex: <ul><li>For multi-part articles, the <code>rel=canonical</code> should point at either each individual page or a 'view-all' page (and not to page 1 of a multi-part series).</li><li>If you offer subscription-based access to your website content, or if users must register for access, consider adding structured data for subscription and paywalled content.</li></ul>)

## Writing rules
- Absolutely no em dashes
- Do not EVER say why something matters (classic AI slop)
- If you are referrring to a word or phrase use single quotes instead of double quotes
- Commas and periods go outside single quotes (e.g., The search result shows 'Example Site > Category > Subcategory', giving searchers immediate context about the page's position in the site.)
- Only use double quotes for a complete quote or a sizable chunk of a quote but keep these to a minimum
- Lists must be preceded by a complete sentence and then a colon (e.g., "Google has some practical guidelines for breadcrumb markup:"). Never use sentence fragments (e.g., "You need to:", "Common culprits include:", "The practical takeaway:"). The word "include" before a colon is almost always a fragment because it's a transitive verb missing its object. If text in a paragraph or list item references an example, you can just write, "Example:" An example of this convention is in the examples.md file.
- If you use a colon in a sentence and an independent clause follows, you must capitalize the first letter after the colon. ("The fix is structural: move every piece of ranking-critical content (headings, body text, prices, structured data) into the server-delivered HTML." becomes The fix is structural: Move every piece... )
- Do not say what something isn't, followed by what it is (e.g., "This isn't just x. It's y."). This is a flag of AI slop. Just say what it is.
	WRONG:
	Readability isn't about dumbing content down; it's about matching the complexity of the writing to the audience and ensuring the content structure supports scanning and comprehension.
	
	CORRECT:
	The goal of making content more readable is matching the complexity of the writing to the audience and ensuring the content structure supports scanning and comprehension.

## Search Google to see if Google has stopped supporting a feature
We don't want SEOs to recommend implementation of markup or code for features 
Google has deprecated or severely restricted. Run a web search for the check's 
feature before rewriting. If it has been deprecated or severely restricted, 
update the existing `worth_it` field to "No" at the subcategory level of the 
JSON file. Also append a row to content/google_updated_guidance.csv with:
- audit_checks.title ('title')
- audit_checks.category ('category')
- what Google deprecated/demoted ('updated_guidance')
- date of change ('update_date')
- citation url ('citation_url')

If worth_it is already "No", still rewrite the base field. Some sites may still qualify for these features.

## Few-Shot Examples

See examples.md for before/after pairs.

## Output Format

Plain string. No JSON. No markdown headers. Use <br> for paragraph breaks.
HTML `<ul>/<li>` is acceptable for lists, matching the existing file style.