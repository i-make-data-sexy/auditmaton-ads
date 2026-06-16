---
name: rewrite-edu-bases
description: Batch rewrites educate.base fields across SEO audit JSON files using the edu-base-writer skill. Use when asked to process or improve a directory of audit JSON files.
context: fork
---

# REWRITE EDU BASES — BATCH PROCESSOR

## Task

Process all JSON files in $ARGUMENTS (or current directory if not specified).
For each file and each audit_check within it, rewrite the `educate.base` field.

## Process Per File

1. Read the JSON file
2. For each object in `audit_checks[]`:
   a. Extract: `id`, `title`, `category`, `subcategory`, `educate.base`
   b. Pass to the seo-content-writer subagent with full context
   c. Replace `educate.base` with the returned string
3. Write the updated JSON back to the file (preserve all other fields exactly)
4. Log: filename + check IDs processed + word count before/after

## Quality Gate

After rewriting, verify:
- New base is 150–400 words
- Does not start with a definition ("X is a...")
- Contains the check's primary risk/enforcement mechanism

If any check fails the quality gate, flag it for manual review instead 
of writing it.

## CSV Aggregation
After all checks are processed, compile all deprecation findings returned
by subagents and write to content/google_updated_guidance.csv with columns:
title, category, updated_guidance, update_date, citation_url

## Output

Print a summary table:
| File | Checks Processed | Flagged for Review |
```
