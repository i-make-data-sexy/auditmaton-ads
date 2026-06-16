# blueprints/audit/__init__.py
# Registers the audit blueprint for audit session management,
# dashboard, category/subcategory views, and intake form

from blueprints.audit.routes import audit_bp
from blueprints.audit.intake import intake_bp
