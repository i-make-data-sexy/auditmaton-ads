Read CLAUDE.md and the current intake form code.
 
Add these new intake questions:
 
1. After site type selection (step 1), add a Rich Results schema
   checklist. Group the checkboxes by category:
   - Content Types: Article, Discussion forum, Education Q&A, FAQ,
     Fact check, Q&A
   - Business & Organization: Employer aggregate rating, Job posting,
     Organization, Profile page
   - Products & Commerce: Review snippet, Software app
   - Events & Courses: Event, Course list
   - Media & Visual: Carousel, Image metadata, Movie carousel,
     Video, Dataset
   - Food & Travel: Recipe, Vacation rental
   - Navigation & Structure: Breadcrumb, Speakable, Subscription
     and paywalled content
   - Other: Book actions, Math solver
 
   Auto-check logic:
   - If Ecommerce selected → exclude Product (covered in Shopping)
   - If Local Business selected → exclude Local business schema
     (covered in Local section)
   - If Recipe site type selected → auto-check Recipe schema
   - Show a "Not sure which schemas apply? Skip this and we'll
     include the most common ones for your site type." option that
     auto-selects a sensible default set.
 
2. Add International flag (step 1, after site types):
   "Does this site target multiple countries or languages?" (yes/no)
 
3. Add JavaScript framework question (step 4, resources):
   "Is this site built with a JavaScript framework?"
   Options: No / minimal JS, React / Next.js, Vue / Nuxt, Angular,
   Other SPA framework, Not sure
 
4. Store all new selections in the session alongside existing intake
   data.
 
Do NOT change the column mapping logic (step 3).
Do NOT change the review step (step 5) layout, but DO add the new
selections to the review summary.
 