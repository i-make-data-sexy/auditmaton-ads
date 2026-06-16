# Directory Structure

Strong preference for tight architecture: more files over long files, organized into directories and subdirectories.

```
Auditmaton Ads/  (local dir for Auditmaton: Ads)
├── app.py                              # App factory entry point
├── wsgi.py                             # Gunicorn entry point
├── config.py                           # Environment-based config
├── extensions.py                       # Flask extension instances (db, login_manager, migrate)
│
├── blueprints/
│   ├── __init__.py
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── routes.py                   # Admin dashboard, user management
│   │   └── templates/
│   │       └── admin/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py                   # Login, register, password reset
│   │   ├── devices.py                  # Device fingerprinting, authorization
│   │   └── templates/
│   │       └── auth/
│   ├── audit/
│   │   ├── __init__.py
│   │   ├── routes.py                   # Audit session management, category/subcat views
│   │   ├── canvas.py                   # The canvas (Santa's workshop) routes
│   │   ├── intake.py                   # Intake form processing (needs Demand/Supply redesign)
│   │   ├── evaluate.py                 # Audit data analysis logic
│   │   └── templates/
│   │       └── audit/
│   ├── billing/
│   │   ├── __init__.py
│   │   ├── routes.py                   # Subscription dashboard, token packs
│   │   ├── payment_webhooks.py         # Authorize.net event handling
│   │   └── templates/
│   │       └── billing/
│   └── ai/
│       ├── __init__.py
│       ├── routes.py                   # Chatbot, contextual queries
│       ├── prompts.py                  # Prompt templates for AI features
│       └── templates/
│           └── ai/
│
├── models/
│   ├── __init__.py                     # Import all models for Alembic
│   ├── user.py                         # User, subscription, token balance
│   ├── device.py                       # Device sessions, fingerprints
│   ├── audit.py                        # Audit sessions, results
│   └── billing.py                      # Subscription plans, token transactions
│
├── services/
│   ├── __init__.py
│   ├── audit_engine.py                 # Core audit logic, schema loading
│   ├── chart_builder.py                # Plotly visualization generation
│   ├── report_generator.py             # PDF export with kaleido
│   └── token_manager.py                # Token usage tracking, allocation
│
├── static/
│   ├── css/
│   ├── js/
│   ├── fonts/
│   └── img/
│
├── templates/
│   ├── base.html                       # Master layout
│   ├── components/                     # Reusable Jinja partials
│   └── errors/                         # 404, 500, etc.
│
├── json/                               # Audit subcheck schemas (empty - taxonomy TBD)
│   ├── demand-side/                    # (planned - Google Ads, Meta, TikTok, Microsoft)
│   │   ├── google-ads/
│   │   ├── meta-ads/
│   │   ├── tiktok-ads/
│   │   └── microsoft-ads/
│   └── supply-side/                    # (planned - Ad Manager, AdSense, SSPs)
│       ├── google-ad-manager/
│       ├── adsense/
│       └── header-bidding/
│
├── content/
│   └── updates/                        # Platform update timeline data (inherited)
│
├── editorial/
│   └── editorial_revisions.json        # Append-only revision log (empty on scaffold)
│
├── migrations/                         # Alembic migration files
│
├── logs/
│   ├── app.log
│   ├── access.log
│   └── error.log
│
├── scripts/                            # Maintenance and ops
│   ├── db_backup.sh
│   ├── create_admin.py
│   ├── validate_db_backup.py
│   ├── lint_editorial.py               # Editorial linter (canonical from Crawl Canvas)
│   └── git-hooks/
│       └── pre-commit                  # Linter gate on staged JSON
│
├── specs/                              # Product planning docs
│   ├── product_spec.md
│   └── tool_inventory.md
│
├── .github/
│   └── workflows/
│       └── lint-editorial.yml          # CI gate (linter on every push/PR)
│
├── archive/                            # Backup graveyard (ignore)
│
├── .env.example
├── .gitignore
├── CLAUDE.md
├── Procfile
├── README.md
└── requirements.txt
```

## Key Structural Decisions

- **Blueprint-scoped templates.** Each blueprint owns its templates. Root `templates/` only holds `base.html`, shared components, and error pages.
- **Services layer.** Business logic separated from routes. Routes stay thin (handle request, call service, return response). Heavy lifting lives in testable service modules.
- **Models split by domain.** Each domain gets its own file. All imported in `models/__init__.py` for Alembic discovery.
- **Scripts directory.** Ops tools (`create_admin.py`, `db_backup.sh`) stay accessible but out of the root.
- **Logs directory.** All logs go here. Never in the root.
- **Only Python files in root:** `app.py`, `wsgi.py`, `config.py`, `extensions.py`.
- **json/ top-level split.** The Demand/Supply fork is reflected in the `json/` tree structure. Taxonomy is TBD and being designed collaboratively with Annie.
