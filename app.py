# app.py
# Application factory for Auditmaton: Ads, a professional ad-audit tool for
# digital analytics practitioners. Creates and configures the Flask app, initializes extensions,
# registers blueprints, and defines top-level routes.

# ========================================================================
#   Imports
# ========================================================================

from flask import Flask, render_template, request, make_response, session, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFError
from markupsafe import Markup
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import logging
import os
import re

# Load environment variables from .env file (if present).
# override=True ensures .env values always win over shell exports,
# so the .env file is the single source of truth for credentials.
load_dotenv(override=True)

from config import DevelopmentConfig, ProductionConfig
from flask_login import logout_user as _logout_user
from extensions import db, migrate, login_manager, csrf, limiter, mail


# ========================================================================
#   Configure Logging
# ========================================================================

# Configure logging to display timestamps, log level, and messages.
# In production (Gunicorn), also write to logs/app.log so application
# messages are captured alongside Gunicorn's own error log.
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "app.log")),
    ],
)


# ========================================================================
#   Jinja Filters
# ========================================================================

def render_content(text):
    """
    Converts raw text from JSON content fields into properly structured HTML.

    Splits on double newlines to separate blocks, then detects whether each
    block contains HTML block-level elements (passed through as-is), a
    numbered list (lines starting with '1. ', '2. ', etc.), a bullet list
    (lines starting with '- ' or '* '), or a plain paragraph.

    Inline HTML elements like <em>, <strong>, and <a> within paragraphs
    are preserved and rendered correctly.

    Args:
        text (str): Raw text from a JSON content field.

    Returns:
        Markup: Safe HTML string with <p>, <ol>, <ul>, and any passed-through
                HTML block elements.
    """
    if not text:
        return Markup("")

    blocks = text.split("\n\n")
    html_parts = []

    # Pattern for numbered list items: digit(s) followed by a period and space
    numbered_pattern = re.compile(r"^\d+\.\s")

    # Pattern for bullet list items: dash or asterisk followed by a space
    bullet_pattern = re.compile(r"^[-*]\s")

    # Pattern for HTML block-level elements that should pass through without wrapping
    html_block_pattern = re.compile(
        r"^<(ul|ol|li|div|table|blockquote|h[1-6]|p|section|article"
        r"|figure|figcaption|dl|dt|dd|img)\b",
        re.IGNORECASE
    )

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # If block starts with an HTML block-level element, pass through as-is
        if html_block_pattern.match(block):
            html_parts.append(block)
            continue

        lines = block.split("\n")

        # Check if the block is a numbered list
        if all(numbered_pattern.match(line.strip()) for line in lines if line.strip()):
            items = []
            for line in lines:
                line = line.strip()
                if line:

                    # Strip the leading number and period
                    item_text = numbered_pattern.sub("", line, count=1)
                    items.append(f"<li>{item_text}</li>")
            html_parts.append("<ol>" + "".join(items) + "</ol>")

        # Check if the block is a bullet list
        elif all(bullet_pattern.match(line.strip()) for line in lines if line.strip()):
            items = []
            for line in lines:
                line = line.strip()
                if line:

                    # Strip the leading dash/asterisk
                    item_text = bullet_pattern.sub("", line, count=1)
                    items.append(f"<li>{item_text}</li>")
            html_parts.append("<ul>" + "".join(items) + "</ul>")

        # Plain paragraph
        else:
            html_parts.append(f"<p>{block}</p>")

    return Markup("".join(html_parts))


# ========================================================================
#   App Factory
# ========================================================================

def create_app(config_class=None):
    """
    Creates and configures the Flask application.

    Initializes all extensions, registers blueprints, sets up
    Jinja filters, and defines top-level routes. Uses the provided
    config class or auto-selects based on the FLASK_ENV variable.

    Args:
        config_class: Configuration class to use (DevelopmentConfig or
                      ProductionConfig). If None, auto-selects based
                      on the FLASK_ENV environment variable.

    Returns:
        Flask: The configured Flask application instance.
    """

    # Auto-select config based on environment if not provided
    if config_class is None:
        env = os.environ.get("FLASK_ENV", "development")
        config_class = ProductionConfig if env == "production" else DevelopmentConfig

    # Initialize Flask app with static file configuration
    app = Flask(__name__,
                static_url_path="/static",
                static_folder="static")

    # Load configuration from the selected config class
    app.config.from_object(config_class)

    # ================================================
    #   Initialize Extensions
    # ================================================

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)

    # Import models so Alembic can discover them for migration generation
    import models  # noqa: F401
    from models.user import User
    from models.billing import Product

    # ================================================
    #   User Loader (Flask-Login)
    # ================================================

    @login_manager.user_loader
    def load_user(user_id):
        """
        Loads a user from the database by their primary key.

        Called automatically by Flask-Login on every request to
        populate current_user from the session cookie.

        Args:
            user_id (str): The user's UUID primary key stored in the session.

        Returns:
            User or None: The User object if found, otherwise None.
        """
        return db.session.get(User, user_id)

    # ================================================
    #   Register Jinja Filters
    # ================================================

    app.jinja_env.filters["render_content"] = render_content

    # ================================================
    #   Template Context Processor
    # ================================================

    @app.context_processor
    def inject_app_root():
        """
        Injects the APPLICATION_ROOT prefix into all templates.

        Templates use {{ app_root }} to prefix hardcoded URLs so links
        work correctly when the app is mounted behind a reverse proxy
        at /tools/auditmaton/ads-audits/.

        Strip any trailing slash so templates that write `{{ app_root }}/x`
        never produce a double slash. In particular, a local APPLICATION_ROOT
        of "/" normalizes to "" so links render as `/x`, not `//x` (the
        browser would treat `//x` as a protocol-relative host).
        """
        return {"app_root": app.config.get("APPLICATION_ROOT", "").rstrip("/")}

    @app.context_processor
    def inject_active_platform():
        """
        Injects the active platform into all templates as {{ active_platform }}
        (slug) and {{ active_platform_label }} (display name). Templates use the
        slug to build platform-scoped /dashboard/<platform>/ links and to mark
        the active chip in the platform strip.
        """
        from services.audit_engine import get_active_platform, AVAILABLE_PLATFORMS
        slug = get_active_platform()
        label = dict(AVAILABLE_PLATFORMS).get(slug, slug)
        return {"active_platform": slug, "active_platform_label": label}

    @app.context_processor
    def inject_user_role():
        """
        Injects the current user's editorial role into all templates.

        Templates use {{ user_role }} to conditionally show/hide
        editorial UI elements (propose edit, comment buttons) based
        on the user's role. During an admin 'unauth' Test as tier preview,
        reports None so role-gated UI renders the logged-out experience.
        """
        from services.tier import viewer_authenticated
        if current_user.is_authenticated and viewer_authenticated():
            return {"user_role": current_user.role}
        return {"user_role": None}

    @app.context_processor
    def inject_effective_tier():
        """
        Injects the Test as tier state into all templates.

        Provides {{ effective_tier }} (the tier the viewer is treated as),
        {{ is_real_admin }} (gates switcher visibility independently of any
        preview, so a real admin is never trapped in a downgraded view),
        {{ viewer_authenticated }} (False during an 'unauth' preview so the
        nav renders logged-out), and {{ tier_switcher_options }} for the
        switcher's <select>.
        """
        from services.tier import (
            resolve_effective_tier,
            is_real_admin,
            viewer_authenticated,
            SWITCHER_OPTIONS,
        )
        return {
            "effective_tier": resolve_effective_tier(),
            "is_real_admin": is_real_admin(),
            "viewer_authenticated": viewer_authenticated(),
            "tier_switcher_options": SWITCHER_OPTIONS,
        }

    @app.url_defaults
    def add_static_cache_buster(endpoint, values):
        """
        Appends a `v=<mtime>` query string to every url_for('static', ...)
        call so browsers re-fetch CSS, JS, and image assets after a deploy
        instead of serving the cached previous version.

        The version is the file's modification time (epoch seconds), so
        unchanged assets keep the same URL and stay cached, while edited
        ones bump the version automatically.
        """

        if endpoint != "static":
            return

        filename = values.get("filename")
        if not filename or "v" in values:
            return

        try:
            file_path = os.path.join(app.static_folder, filename)
            values["v"] = int(os.stat(file_path).st_mtime)
        except OSError:

            # File doesn't exist on disk — let Flask 404 normally
            pass

    # ================================================
    #   Ensure Upload Directory Exists
    # ================================================

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ================================================
    #   Register Blueprints
    # ================================================

    from blueprints.admin import admin_bp
    from blueprints.audit.routes import audit_bp
    from blueprints.audit.intake import intake_bp
    from blueprints.audit.canvas import canvas_bp
    from blueprints.auth import auth_bp
    from blueprints.editorial import editorial_bp
    from blueprints.preferences import preferences_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(intake_bp)
    app.register_blueprint(canvas_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(editorial_bp)
    app.register_blueprint(preferences_bp)

    # ================================================
    #   Request Hooks
    # ================================================

    # Local dev convenience: turn off auth gates entirely when running
    # locally. Flask-Login honors LOGIN_DISABLED natively, so
    # @login_required becomes a no-op, and the role_required decorator
    # checks this same flag so admin routes open up too. Gated on the
    # config's DEBUG value (True only in DevelopmentConfig), not on
    # FLASK_ENV, so a missing env var on prod cannot accidentally open
    # auth.
    if app.config.get("DEBUG") is True:
        app.config["LOGIN_DISABLED"] = True

    @app.before_request
    def log_request_info():
        """Logs request headers and body for debugging."""
        app.logger.debug("Headers: %s", request.headers)
        app.logger.debug("Body: %s", request.get_data())

        # Mark session as permanent so it persists across browser closures
        session.permanent = True

    # Routes that do not require an active subscription
    SUBSCRIPTION_EXEMPT_PREFIXES = ("/static/", "/timeline/")
    SUBSCRIPTION_EXEMPT_ENDPOINTS = ("home", "pricing", "static")

    @app.before_request
    def check_subscription():
        """
        Enforces active subscription for authenticated users.

        Redirects to the subscription-required page if the user is logged in
        but has no active subscription. Auth routes, static files, the home
        page, and the timeline are exempt.
        """
        if not current_user.is_authenticated:
            return

        # Admins always have access regardless of subscription state.
        # Without this bypass, the app owner gets kicked to login the
        # moment their personal subscription record expires (or doesn't
        # exist yet on a fresh Canvas-app deploy where the subscription
        # record hasn't been seeded).
        if current_user.is_admin:
            return

        # Skip check for exempt routes
        if request.endpoint in SUBSCRIPTION_EXEMPT_ENDPOINTS:
            return

        # Skip all auth blueprint routes (login, register, logout, reset)
        if request.endpoint and request.endpoint.startswith("auth."):
            return

        for prefix in SUBSCRIPTION_EXEMPT_PREFIXES:
            if request.path.startswith(prefix):
                return

        # Check for active subscription
        if not current_user.has_active_subscription:
            _logout_user()
            flash("Your subscription has expired. Please renew to continue.")
            return redirect(url_for("auth.login"))

    # ================================================
    #   Error Handlers
    # ================================================

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """
        Returns a descriptive JSON response when CSRF validation fails
        on an AJAX request. For non-AJAX requests, renders a 400 error page.
        """
        app.logger.warning("CSRF validation failed: %s (endpoint: %s)", e.description, request.endpoint)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "CSRF token missing or invalid. Please refresh the page and try again."}), 400

        flash("Your session has expired. Please try again.")
        return redirect(url_for("home"))

    @app.errorhandler(404)
    def page_not_found(e):
        """
        Renders the custom 404 page (missing URL rendered as an audit
        finding card) for any missing route. JSON endpoints under /api/
        still get a JSON 404 so AJAX clients aren't handed an HTML body.
        """
        if request.path.startswith("/api/") or \
           request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "Not found"}), 404

        return render_template(
            "errors/404.html",
            requested_path=request.path,
            detected_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        ), 404

    # ================================================
    #   Security Headers
    # ================================================

    @app.after_request
    def set_security_headers(response):
        """
        Adds security headers to every response.

        Protects against clickjacking, MIME sniffing, XSS, and enforces
        HTTPS via HSTS in production. Content-Security-Policy whitelists
        only the CDN domains used by the app.
        """
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # Content-Security-Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' "
                "https://stackpath.bootstrapcdn.com "
                "https://cdnjs.cloudflare.com "
                "https://cdn.jsdelivr.net "                      # Quill rich text editor (via jsDelivr)
                "https://www.gstatic.com "                       # Firebase JS SDK
                "https://www.googletagmanager.com "              # GTM
                "https://connect.facebook.net "                  # Facebook pixel (via GTM)
                "https://apis.google.com "                       # Google Sign-In
                "https://jstest.authorize.net "                  # Authorize.net Accept.js (sandbox)
                "https://js.authorize.net "                      # Authorize.net Accept.js (production)
                "'unsafe-inline'",                               # GTM and Firebase init require inline scripts
            "style-src 'self' "
                "https://stackpath.bootstrapcdn.com "            # Bootstrap CSS
                "https://cdnjs.cloudflare.com "                  # Font Awesome CSS
                "https://cdn.jsdelivr.net "                      # Quill editor styles (via jsDelivr)
                "https://fonts.googleapis.com "                  # Google Fonts CSS (Gugi on home page)
                "'unsafe-inline'",                               # Bootstrap and FA use inline styles
            "font-src 'self' "
                "https://cdnjs.cloudflare.com "                  # Font Awesome webfonts
                "https://fonts.gstatic.com "                     # Google Fonts webfont files
                "data:",                                         # Accept.js inline font
            "img-src 'self' "
                "https://www.gstatic.com "                       # Google icon on sign-in button
                "https://www.googletagmanager.com "              # GTM pixel
                "https://www.facebook.com "                      # Facebook pixel (via GTM)
                "https://*.facebook.com "                        # Facebook tracking subdomains
                "data:",                                         # Inline images (canvas fingerprint, etc.)
            "connect-src 'self' "
                "https://stackpath.bootstrapcdn.com "            # Bootstrap CSS source map
                "https://cdn.jsdelivr.net "                      # Quill source map (jsDelivr)
                "https://www.googleapis.com "                    # Firebase Auth REST API
                "https://securetoken.googleapis.com "            # Firebase token refresh
                "https://identitytoolkit.googleapis.com "        # Firebase Auth
                "https://www.googletagmanager.com "
                "https://www.google-analytics.com "
                "https://analytics.google.com "                  # GA4 measurement endpoint
                "https://jstest.authorize.net "                  # Accept.js loads AcceptCore.js (sandbox)
                "https://js.authorize.net "                      # Accept.js loads AcceptCore.js (production)
                "https://apitest.authorize.net "                 # Authorize.net API (sandbox)
                "https://api.authorize.net",                     # Authorize.net API (production)
            "frame-src "
                "https://accounts.google.com "                   # Google Sign-In popup
                "https://www.googletagmanager.com "
                "https://crawl-canvas.firebaseapp.com "          # Firebase Auth handler
                "https://jstest.authorize.net "                  # Authorize.net iframe (sandbox)
                "https://js.authorize.net "                      # Authorize.net iframe (production)
                "https://www.facebook.com",                      # Facebook pixel iframe (via GTM)
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self' "
                "https://www.facebook.com",                      # Facebook pixel form post (via GTM)
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # HSTS only in production (requires HTTPS)
        if not app.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

    # ================================================
    #   Routes
    # ================================================

    # Home route
    @app.route("/")
    def home():
        """
        Renders the home screen.

        Returns:
            Rendered home.html template.
        """
        return render_template("home.html")

    # Dashboard routes. /dashboard/<platform>/ is the kanban for a platform and
    # doubles as the platform switcher (chip clicks navigate here). The bare
    # /dashboard/ redirects to the active (or default) platform.
    @app.route("/dashboard/")
    @login_required
    def dashboard_home():
        """Redirect the bare dashboard URL to the active platform's dashboard."""
        from services.audit_engine import get_active_platform
        return redirect(url_for("dashboard", platform=get_active_platform()))

    @app.route("/dashboard/<platform>/")
    @login_required
    def dashboard(platform):
        """
        Renders the Category Dashboard (Level 1 navigation) for a platform.

        Args:
            platform (str): Platform slug. Must match AVAILABLE_PLATFORMS, else 404.

        Returns:
            Rendered dashboard.html with the platform cookie set so the choice
            persists across browser sessions.
        """
        from services.audit_engine import (
            AVAILABLE_PLATFORMS,
            set_active_platform,
            get_active_side,
            platforms_grouped_by_type,
        )

        valid_slugs = {s for s, _ in AVAILABLE_PLATFORMS}
        if platform not in valid_slugs:
            abort(404)

        # Set the session before building categories so platform-scoped
        # content resolves correctly.
        session["active_platform"] = platform

        categories = get_dashboard_categories(platform)

        # Audit finding #7: Apply intake session data to lock/unlock sections
        categories = apply_intake_overrides(categories)

        # Build the grouped picker for the dashboard chip strip. Use the
        # side from the intake session if present; fall back to the side of
        # the active platform, then to demand. Restrict to the platforms the
        # practitioner selected at intake when a non-empty selection exists.
        active_side = session.get("intake_side") or get_active_side() or "demand"
        selected = set(session.get("intake_platforms") or [])
        picker_groups = platforms_grouped_by_type(
            active_side,
            slugs=(selected if selected else None),
        )

        rendered = render_template(
            "dashboard.html",
            categories=categories,
            active_platform=platform,
            available_platforms=AVAILABLE_PLATFORMS,
            picker_groups=picker_groups,
            active_side=active_side,
        )

        # Cache-control headers (dashboard reflects in-progress audit state)
        response = make_response(rendered)
        set_active_platform(response, platform)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response

    # App Architecture route — treemap of the full audit taxonomy
    @app.route("/architecture/")
    @login_required
    def architecture():
        """
        Renders the App Architecture page: a clickable Plotly treemap of the
        live category/subcategory taxonomy, sized by check count.

        Returns:
            Rendered architecture.html template.
        """
        from services.chart_builder import build_architecture_treemap

        return render_template(
            "architecture.html",
            treemap=build_architecture_treemap(),
        )

    # Pricing route
    @app.route("/pricing/")
    def pricing():
        """
        Renders the pricing page with base product and add-on cards.

        Loads active products from the database and passes them to the
        template for the hero base card, add-on grid, and lightbox modals.

        Returns:
            Rendered pricing.html template.
        """
        products = Product.query.filter_by(is_active=True).order_by(Product.sort_order).all()
        return render_template("pricing.html", products=products)

    # Google Algorithm Timeline route
    @app.route("/timeline/")
    def timeline():
        """
        Renders the Google Algorithm Timeline page.

        Displays a chronological timeline of confirmed and unconfirmed Google
        algorithm updates with insights, recovery times, and representative quotes.

        Returns:
            Rendered timeline.html template.
        """
        return render_template("timeline.html")

    return app


# ========================================================================
#   Mock Data
# ========================================================================

def get_mock_active_audit():
    """
    Returns mock data for the active audit session context bar.

    Simulates a SaaS site audit on the AI tier with token tracking.

    Returns:
        dict: Active audit session data with domain, tier, and token info.
    """
    return {
        "domain": "https://example-saas.com",
        "tier": "ai",
        "tier_display": "AI Tier",
        "tokens_remaining": 8420,
    }


def get_dashboard_categories(platform=None):
    """
    Builds the dashboard category cards for the Tag edition from the
    real authored content. Categories (and their order) come from
    CATEGORY_METADATA; each category that has audit JSON becomes a card, with
    not_started status: a fresh audit has no progress, so the kanban dashboard
    shows every category under Not Started. Deriving from CATEGORY_METADATA +
    the live json/ dirs keeps this tethered to the actual taxonomy.
    """
    from services.audit_engine import CATEGORY_METADATA, get_subcategories, get_active_platform

    plat = platform or get_active_platform()
    categories = []
    for key, meta in CATEGORY_METADATA.get(plat, {}).items():
        subs = get_subcategories(key, platform=plat)
        if not subs:
            continue
        categories.append({
            "key": key,
            "display_name": meta["display_name"],
            "description": meta["description"],
            "icon_class": meta["icon_class"],
            "total_subchecks": len(subs),
            "completed": 0,
            "percentage": 0,
            "status": "not_started",
            "conditional": False,
            "locked": False,
            "locked_reason": None,
            "muted": False,
            "muted_reason": None,
        })
    return categories


# ========================================================================
#   Intake 
# ========================================================================

def apply_intake_overrides(categories) -> list:
    """
    Returns the dashboard categories unchanged.

    The Ads edition gates categories by intake answers (demand-side vs.
    supply-side and which platform). This stub returns categories unchanged;
    the Demand/Supply fork logic should be implemented here when the taxonomy
    is built. Site type captured at intake feeds the in-check
    site_type_overlays; it does not lock
    or hide anything here.

    This is kept as a pass-through (rather than removed) so the dashboard
    route's call site stays stable if intake-driven gating is ever revisited.

    Args:
        categories (list): List of category dicts.

    Returns:
        list: The same categories, unchanged.
    """
    return categories


# ========================================================================
#   Run (Development Only)
# ========================================================================

# Start in debug mode when running directly (python app.py)
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
