# blueprints/auth/__init__.py
# Authentication blueprint for Auditmaton for Site Audits. Handles user registration,
# login, logout, password reset, and email verification via Firebase
# Authentication with Flask-Login session management.

from flask import Blueprint

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
)

from blueprints.auth import routes  # noqa: F401, E402
