Read CLAUDE.md for the updated 12-section taxonomy.
 
Update the dashboard to reflect 12 audit categories instead of 10:
 
1. Update the mock data in blueprints/audit/routes.py:
   - Add Rich Results card (icon: fa-solid fa-trophy)
   - Add JavaScript card (icon: fa-solid fa-square-js)
   - Update section count from 10 to 12
   - Rich Results subcheck count is dynamic (based on intake
     selections); for mock data use 6 as a realistic number
   - JavaScript has 8 subchecks
   - Recalculate total subcheck count
 
2. Update the dashboard template if needed for 12 cards.
   Grid should still work: 4 rows of 3 on desktop.
 
3. Conditional logic:
   - Shopping: locked unless Ecommerce site type
   - Local: locked unless Local Business site type
   - International: locked unless flagged at intake
   - Rich Results: show count based on selected schemas
   - JavaScript: always visible but deprioritized (muted style,
     sorted lower) if "No / minimal JS" selected at intake
 
Do NOT change styles.css or dashboard.css unless required for the
new cards. Do NOT touch base.html.
 