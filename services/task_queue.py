# services/task_queue.py
# Huey task queue instance and Flask app context helper. The Huey consumer
# process imports the `huey` object from this module. Tasks use
# `with_app_context()` to access Flask extensions (SQLAlchemy, etc.)
# inside background workers.

import os
from functools import wraps

from huey import SqliteHuey


# ========================================================================
#   Huey Instance
# ========================================================================

# Read config from environment or use defaults matching config.py
_db_path = os.environ.get(
    "HUEY_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "queue", "huey.db"),
)

# In development (FLASK_ENV unset or "development"), run tasks synchronously
# so developers don't need a separate worker process. In production
# (FLASK_ENV=production), tasks are enqueued to the Huey SQLite backend.
_env = os.environ.get("FLASK_ENV", "development")
_immediate_default = "true" if _env == "development" else "false"
_immediate = os.environ.get("HUEY_IMMEDIATE", _immediate_default).lower() == "true"

huey = SqliteHuey(
    "crawl_canvas",
    filename=_db_path,
    immediate=_immediate,
)


# ========================================================================
#   App Context Helper
# ========================================================================

# Cache the Flask app instance so we only call create_app() once per worker
_app = None


def _get_app():
    """
    Returns a Flask app instance for use in background workers.

    Lazily creates the app on first call and caches it for the lifetime
    of the worker process. This avoids creating a new app (and new DB
    connection pool) for every task execution.

    Returns:
        Flask: The configured Flask application instance.
    """
    global _app
    if _app is None:
        from app import create_app
        _app = create_app()
    return _app


def with_app_context(fn):
    """
    Decorator that wraps a function to run inside a Flask app context.

    Use this on Huey task functions that need access to SQLAlchemy, Flask
    config, or other Flask extensions. The app context is created fresh
    for each task invocation to ensure clean database sessions.

    Args:
        fn: The function to wrap.

    Returns:
        function: The wrapped function.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        """Runs the wrapped function inside a Flask application context."""
        app = _get_app()
        with app.app_context():
            return fn(*args, **kwargs)
    return wrapper
