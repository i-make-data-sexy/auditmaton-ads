# extensions.py
# Flask extension instances shared across blueprints and services.
# Extensions are instantiated here without an app, then initialized
# in app.py via init_app(). This avoids circular imports.

from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
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
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],       # Global defaults
    storage_uri="memory://",                             # In-memory for dev; Redis in production
)

# Email extension for sending SMTP messages via Flask-Mail
mail = Mail()
