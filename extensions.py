# extensions.py
# Flask extension instances shared across blueprints and services.
# Extensions are instantiated here without an app, then initialized
# in app.py via init_app(). This avoids circular imports.

from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# ========================================================================
#   Extension Instances
# ========================================================================

# Database ORM
db = SQLAlchemy()

# Database migration management (Alembic)
migrate = Migrate()

# User session and authentication management
login_manager = LoginManager()
login_manager.login_view = "auth.login"                  # Redirect target for @login_required
login_manager.login_message_category = "info"            # Flash message category

# CSRF protection for all forms and AJAX endpoints
csrf = CSRFProtect()

# Rate limiting to prevent brute force and abuse


def _exempt_privileged_from_default_limits():
    """
    Skips the global default rate limits for authenticated admin and owner
    accounts. Privileged users legitimately make many requests while
    managing the app, so the blanket browse limits should not throttle
    them. The explicit, per-route brute-force limits on the auth blueprint
    (login, register, password reset) are NOT affected by this exemption,
    so those protections stay in place for everyone.

    Returns:
        bool: True to skip the default limits for this request, else False.
    """

    try:
        return current_user.is_authenticated and getattr(current_user, "role", None) in ("admin", "owner")
    except Exception:
        # Outside a request/login context, or before login is wired up,
        # fall back to applying the default limits.
        return False


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],       # Global defaults
    default_limits_exempt_when=_exempt_privileged_from_default_limits,
    storage_uri="memory://",                             # In-memory for dev; Redis in production
)

# Email extension for sending SMTP messages via Flask-Mail
mail = Mail()
