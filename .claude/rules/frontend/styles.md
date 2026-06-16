# CSS Conventions

## Required Root Variables

Every CSS file must start with the standard `:root` variable block. Use only brand colors:

- `#FFA500` — Brand orange
- `#8BB42D` — Brand green
- `#0273BE` — Brand blue
- `#E90555` — Brand fuscia
- `#333` — Text color (dark gray)
- `#DEDEDE` — Elegant borders around layout containers and charts

Light variants: `#FFC04D` (orange-light), `#A2C359` (green-light), `#4E9DD2` (blue-light)

```css
/* ========================================================================
    Variables
   ======================================================================== */
:root {
    /* ===============================
         Text
        ============================== */

        /* Font Family */
        --font-family-main: "EkMukta-Light", Helvetica, sans-serif;

        /* Paragraph Size */
        --font-size-p: 20px;

        /* Font Weights */
        --font-weight-normal: 200;
        --font-weight-bold: 400;
        --font-weight-bolder: 600;

        /* Heading Sizes: Large */
        --h1-size-lg: 48px;
        --h2-size-lg: 40px;
        --h3-size-lg: 30px;
        --h4-size-lg: 27px;
        --h5-size-lg: 23px;

        /* Heading Sizes: Medium */
        --h1-size-md: 45px;
        --h2-size-md: 37px;
        --h3-size-md: 27px;
        --h4-size-md: 25px;

        /* Heading Sizes: Small */
        --h1-size-sm: 42px;
        --h2-size-sm: 34px;
        --h3-size-sm: 24px;
        --h4-size-sm: 21px;

        /* Heading Sizes: Very Small */
        --h1-size-xs: 39px;
        --h2-size-xs: 31px;
        --h3-size-xs: 21px;

        /* Line Height */
        --line-height-tight: 1.25;
        --line-height-normal: 1.5;
        --line-height-loose: 1.75;


    /* ===============================
         Colors
        ============================== */

        /* Brand Colors */
        --color-brand-orange: #FFA500;
        --color-brand-orange-light: #FFC04D;
        --color-brand-green: #8BB42D;
        --color-brand-green-light: #A2C359;
        --color-brand-blue: #0273BE;
        --color-brand-blue-light: #4E9DD2;
        --color-brand-fuscia: #E90555;
        --color-dark-gray: #333;
        --color-light-gray: #DEDEDE;
        --color-app-bg: #F8F9FA;

        /* Heading Colors */
        --color-h2: #0273BE;
        --color-h3: #FFC04D;
        --color-h4: #8BB42D;
        --link-color: #FFA500;
        --link-hover: #0273BE;
        --link-visited: #4E9DD2;

    }
```
