# config.py
# Environment-based configuration for Auditmaton: Ads.
# Provides separate settings for development and production,
# with a shared base class for common configuration.

import os
from datetime import timedelta


# ========================================================================
#   Base Configuration
# ========================================================================

class Config:
    """
    Base configuration shared across all environments.

    Subclasses override specific settings for dev vs production.
    """

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key — loaded from environment, falls back to dev default
    SECRET_KEY = os.environ.get("SECRET_KEY", "auditmaton-ads-dev-secret-key")

    # Session settings — 180-day lifetime so users don't get logged out
    # mid-project. The remember cookie matches so Flask-Login can silently
    # restore the session if the browser drops the session cookie.
    # App-unique cookie name. Every Auditmaton edition is served from the
    # same host under its own path prefix, so Flask's default name "session"
    # at Path=/ lets each app overwrite the others' cookie. Because each app
    # signs cookies with a different SECRET_KEY, an overwritten cookie fails
    # the signature check and bounces the user to login. A unique name per
    # app keeps the cookies separate so moving between editions in one
    # browser no longer logs you out.
    SESSION_COOKIE_NAME = "auditmaton_ads_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_PATH = "/"
    PERMANENT_SESSION_LIFETIME = timedelta(days=180)

    # Remember-me cookie (Flask-Login). Without these, defaults are used
    # and the cookie ships without Secure/SameSite, which the browser
    # may drop on HTTPS sites — causing surprise logouts when the
    # session cookie expires.
    REMEMBER_COOKIE_DURATION = timedelta(days=180)
    REMEMBER_COOKIE_NAME = "auditmaton_ads_remember"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # Route prefix for deployment behind reverse proxy
    APPLICATION_ROOT = os.environ.get("APPLICATION_ROOT", "/tools/auditmaton/ads-audits")

    # Firebase Authentication (client-side JS SDK config)
    FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")
    FIREBASE_AUTH_DOMAIN = os.environ.get("FIREBASE_AUTH_DOMAIN", "")
    FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "")

    # Request size limit (16 MB — covers crawl file uploads)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Task Queue (Huey)
    HUEY_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "queue", "huey.db")
    HUEY_WORKERS = int(os.environ.get("HUEY_WORKERS", "4"))
    HUEY_IMMEDIATE = False

    # Upload directory for crawl CSV files (relative to app root)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")

    # Authorize.net Payment Processing
    AUTHORIZE_NET_API_LOGIN_ID = os.environ.get("AUTHORIZE_NET_API_LOGIN_ID", "")
    AUTHORIZE_NET_TRANSACTION_KEY = os.environ.get("AUTHORIZE_NET_TRANSACTION_KEY", "")
    AUTHORIZE_NET_PUBLIC_CLIENT_KEY = os.environ.get("AUTHORIZE_NET_PUBLIC_CLIENT_KEY", "")
    AUTHORIZE_NET_SANDBOX = os.environ.get("AUTHORIZE_NET_SANDBOX", "true").lower() == "true"

    # Email (Flask-Mail / Gmail SMTP)
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@annielytics.com")


# ========================================================================
#   Development Configuration
# ========================================================================

class DevelopmentConfig(Config):
    """
    Development-specific configuration.

    Uses local PostgreSQL, enables debug mode, and relaxes
    cookie security for localhost testing.
    """

    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0

    # Local PostgreSQL (no password needed for peer/trust auth on macOS)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://anniecushing@localhost:5432/auditmaton_ads"
    )

    # Cookies do not require HTTPS in development
    SESSION_COOKIE_SECURE = False

    # Tasks run synchronously in dev — no worker process needed
    HUEY_IMMEDIATE = True


# ========================================================================
#   Production Configuration
# ========================================================================

class ProductionConfig(Config):
    """
    Production-specific configuration.

    Uses Cloud SQL, enforces HTTPS cookies, and tightens
    session lifetime. Secrets loaded from Google Secret Manager
    or environment variables set by the hosting platform.
    """

    DEBUG = False

    # Cloud SQL connection string (set via environment variable)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # Enforce HTTPS-only cookies — both the session cookie and the
    # Flask-Login remember cookie must carry the Secure flag so they
    # round-trip cleanly behind Cloudflare.
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
