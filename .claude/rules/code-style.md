# Coding Preferences

## General Rules

- Never use inline JS or CSS. Use external files for both unless it is absolutely imperative to use inline. If inline is used, flag it explicitly so it can be reviewed.
- Wherever possible, wrap stray code into functions.
- Prefer fixing/improving existing functions over creating new ones. Only create a new function if no current function can be improved to handle the need.
- Use double quotes over single quotes.
- Always put a comment at the top of every file with an overview of its purpose and role in the app.
- Never remove existing comments or docstrings.
- Always add trailing forward slashes to urls

## Docstrings

Every function MUST have a docstring, even if there are no arguments. Follow this format:

```python
def compute_similarity(broken_weights: dict, candidate_weights: dict) -> float:
    """
    Computes the similarity between two sets of weighted keywords using cosine similarity.

    Args:
        broken_weights (dict): Weighted keywords from the broken URL
        candidate_weights (dict): Weighted keywords from a candidate (valid) URL

    Returns:
        float: A similarity score between 0 and 1
    """
```

## Comments

- Be generous with comments
- Start comments with a capital letter, no end punctuation
- Place comments above the line they describe, with a blank line before the comment (unless the comment is the first line in a function)
- Exception: comments for individual parameter settings should be inline, vertically aligned for easy scanning

Example of inline aligned parameter comments:

```python
config = {
    "max_retries": 3,          # Maximum number of retry attempts
    "timeout": 30,             # Request timeout in seconds
    "batch_size": 100,         # Number of URLs per batch
    "delay": 0.5,              # Delay between requests in seconds
}
```

## Code Section Headings

Use these banner-style headings to organize code into logical groups:

**Python:**
```python
# ========================================================================
#   Category
# ========================================================================

# ================================================
#   Subcategory
# ================================================

# ===============================
#   Tertiary Subcategory
# ===============================
```

**CSS / JS:**
```css
/* ========================================================================
   Category
   ======================================================================== */

/* ================================================
     Subcategory
   ================================================ */

/* ===============================
    Tertiary Category
    ============================== */
```

**HTML:**
```html
<!-- ===================================================================
     Category
     =================================================================== -->

<!-- ================================================
     Subcategory
     ================================================ -->

<!-- ==============================
     Tertiary Category
     ============================== -->
```
