# blueprints/auth/permissions.py
# Role-based access control decorators for Auditmaton for Site Audits editorial features.
# Provides a @role_required decorator that restricts route access to users
# with specified roles (owner, editor, contributor, viewer).

from functools import wraps

from flask import abort, current_app
from flask_login import current_user


# ========================================================================
#   Role Decorators
# ========================================================================

def role_required(*roles):
    """
    Decorator that restricts route access to users with specified roles.

    Checks the current user's role against the allowed list and aborts
    with 401 (unauthenticated) or 403 (insufficient role) if access
    is denied. Must be used after @login_required. Honors the Flask-Login
    LOGIN_DISABLED config flag so local development can run without auth.

    Args:
        *roles: One or more role strings (e.g., "owner", "editor").

    Returns:
        function: Decorated route function that enforces role-based access.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            """Checks user authentication and role before allowing access."""

            if current_app.config.get("LOGIN_DISABLED"):
                return f(*args, **kwargs)

            if not current_user.is_authenticated:
                abort(401)

            if current_user.role not in roles:
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator
