# wsgi.py
# Gunicorn entry point for production deployment.
# Creates the Flask app using the factory pattern from app.py.

from app import create_app

app = create_app()
