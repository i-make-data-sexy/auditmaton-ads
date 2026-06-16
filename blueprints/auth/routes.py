# blueprints/auth/routes.py
# Authentication routes for Auditmaton: Ads. Handles registration, login,
# logout, password reset, and email verification. All credential management
# is delegated to Firebase Authentication — this server only verifies
# Firebase ID tokens and manages Flask-Login sessions.

import logging
from datetime import datetime, timedelta, timezone

from flask import (
    render_template, request, redirect, url_for, flash, jsonify, make_response
)
from flask_login import login_user, logout_user, login_required, current_user

from blueprints.auth import auth_bp
from extensions import db, limiter
from models.user import User
from models.billing import Product
from blueprints.auth.devices import (
    validate_device, can_register_device, register_device,
    update_device_activity, find_device_by_token
)
from services.payment_service import charge_card, record_payment, calculate_total

logger = logging.getLogger(__name__)


# ========================================================================
#   Firebase Admin SDK Initialization
# ========================================================================

# Firebase Admin SDK is initialized lazily on first use.
# This avoids import-time failures when credentials are not yet configured.
_firebase_app = None


def _get_firebase_auth():
    """
    Lazily initializes Firebase Admin SDK and returns the auth module.

    Uses the GOOGLE_APPLICATION_CREDENTIALS environment variable to find
    the service account key file. Returns None if Firebase is not configured
    (allows the app to start without Firebase for local development).

    Returns:
        module or None: The firebase_admin.auth module, or None if unavailable.
    """
    global _firebase_app

    try:
        import firebase_admin
        from firebase_admin import auth as firebase_auth

        if _firebase_app is None:
            # Initialize with default credentials (GOOGLE_APPLICATION_CREDENTIALS env var)
            _firebase_app = firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized successfully")

        return firebase_auth

    except (ImportError, ValueError, Exception) as e:
        logger.warning("Firebase Admin SDK not available: %s", e)
        return None


# ========================================================================
#   Account Lockout Helpers
# ========================================================================

def _check_lockout(user):
    """
    Checks whether a user account is locked due to failed login attempts.

    Args:
        user (User): The user to check.

    Returns:
        bool: True if the account is currently locked.
    """
    if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
        return True

    # If lock has expired, reset the counter
    if user.locked_until and datetime.now(timezone.utc) >= user.locked_until:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.session.commit()

    return False


def _record_failed_login(user):
    """
    Increments failed login attempts and applies lockout if thresholds are exceeded.

    Lockout escalation:
      - 5 failures → 15-minute lock
      - 10 failures → 1-hour lock
      - 20 failures → indefinite lock (requires email verification)

    Args:
        user (User): The user whose login attempt failed.
    """
    user.failed_login_attempts += 1
    attempts = user.failed_login_attempts

    if attempts >= 20:
        # Indefinite lock — set far-future date
        user.locked_until = datetime.now(timezone.utc) + timedelta(days=365)
        logger.warning("Account permanently locked for user %s after %d attempts", user.email, attempts)
    elif attempts >= 10:
        user.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
        logger.warning("Account locked 1 hour for user %s after %d attempts", user.email, attempts)
    elif attempts >= 5:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        logger.info("Account locked 15 minutes for user %s after %d attempts", user.email, attempts)

    db.session.commit()


def _reset_failed_logins(user):
    """
    Resets the failed login counter after a successful login.

    Args:
        user (User): The user who logged in successfully.
    """
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.session.commit()


# ========================================================================
#   Login Route
# ========================================================================

@auth_bp.route("/login/", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    """
    Renders the login page (GET) or processes a Firebase ID token login (POST).

    The login flow:
      1. Client-side Firebase JS SDK authenticates the user
      2. Client sends the Firebase ID token to this endpoint via POST
      3. Server verifies the token with Firebase Admin SDK
      4. Server creates or retrieves the User record
      5. Server checks device fingerprint against 2-device limit
      6. Server creates a Flask-Login session

    Returns:
        GET: Rendered login.html template.
        POST: JSON response with redirect URL or error message.
    """

    # Already logged in — redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for("dashboard_home"))

    if request.method == "GET":
        return render_template("auth/login.html")

    # POST: Verify Firebase ID token
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    id_token = data.get("id_token")
    fingerprint_hash = data.get("fingerprint_hash")

    if not id_token:
        return jsonify({"error": "Firebase ID token is required"}), 400

    # Verify the token with Firebase
    firebase_auth = _get_firebase_auth()
    if firebase_auth is None:
        return jsonify({"error": "Authentication service is not configured"}), 503

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
    except Exception as e:
        logger.warning("Firebase token verification failed: %s", e)
        return jsonify({"error": "Invalid or expired token"}), 401

    firebase_uid = decoded_token["uid"]
    email = decoded_token.get("email", "")

    # Find or create the user in our database
    user = User.query.filter_by(firebase_uid=firebase_uid).first()

    if not user:
        # First login — create a local user record
        # Name fields may come from Google Sign-In or registration form
        first_name = data.get("first_name", "").strip() or None
        last_name = data.get("last_name", "").strip() or None

        user = User(
            firebase_uid=firebase_uid,
            email=email,
            first_name=first_name,
            last_name=last_name,
            email_verified=decoded_token.get("email_verified", False),
        )
        db.session.add(user)
        db.session.commit()
        logger.info("Created new user for Firebase UID %s", firebase_uid)

    # Check account lockout
    if _check_lockout(user):
        return jsonify({"error": "Account is temporarily locked due to too many failed attempts. Please try again later."}), 403

    # Check account is active
    if not user.is_active:
        return jsonify({"error": "Account has been deactivated"}), 403

    # Device fingerprint check (if provided)
    client_ip = request.remote_addr
    if fingerprint_hash:
        device = validate_device(user, fingerprint_hash)

        if device:
            # Known device — update activity
            update_device_activity(device, client_ip)
        else:
            # New device — check if under limit
            if not can_register_device(user):
                logger.warning(
                    "Device limit reached for user %s from IP %s",
                    user.email, client_ip
                )
                return jsonify({
                    "error": "device_limit",
                    "message": "You have reached the maximum of 2 authorized devices. Please revoke a device from your account settings to continue."
                }), 403

            # Register the new device
            device = register_device(user, fingerprint_hash, request.user_agent.string, client_ip)

    # Reset failed login counter on success
    _reset_failed_logins(user)

    # Update login metadata
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = client_ip
    user.email_verified = decoded_token.get("email_verified", user.email_verified)
    db.session.commit()

    # Create Flask-Login session
    login_user(user, remember=True)

    logger.info("User %s logged in from %s", user.email, client_ip)

    return jsonify({
        "success": True,
        "redirect": url_for("dashboard_home"),
    })


# ========================================================================
#   Registration Route
# ========================================================================

@auth_bp.route("/register/", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def register():
    """
    Renders the registration page (GET) or processes a new account with payment (POST).

    Registration flow:
      1. Client-side Firebase JS SDK creates the account (email/password or Google)
      2. Client-side Accept.js tokenizes the credit card into an opaque nonce
      3. Client sends both tokens + selected products to this endpoint
      4. Server verifies Firebase token, validates products, charges the card
      5. If payment succeeds: creates User, Subscription, Products, PaymentRecord
      6. If payment fails: returns error (no user created)

    Returns:
        GET: Rendered register.html template with products and Authorize.net config.
        POST: JSON response with redirect URL or error message.
    """

    # Already logged in — redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for("dashboard_home"))

    if request.method == "GET":
        # Load active products for the plan selection UI
        products = Product.query.filter_by(is_active=True).order_by(Product.sort_order).all()
        return render_template("auth/register.html", products=products)

    # POST: Process registration with payment
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    id_token = data.get("id_token")
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    fingerprint_hash = data.get("fingerprint_hash")
    opaque_descriptor = data.get("opaque_data_descriptor", "")
    opaque_value = data.get("opaque_data_value", "")
    selected_products = data.get("selected_products", [])

    # Validate required fields
    if not id_token:
        return jsonify({"error": "Firebase ID token is required"}), 400
    if not opaque_descriptor or not opaque_value:
        return jsonify({"error": "Payment information is required"}), 400
    if not selected_products or "base" not in selected_products:
        return jsonify({"error": "The Base plan is required"}), 400

    # Validate product selections and calculate total
    total_cents, products = calculate_total(selected_products)
    if total_cents == 0:
        return jsonify({"error": "Invalid product selection"}), 400

    # Verify the Firebase token
    firebase_auth = _get_firebase_auth()
    if firebase_auth is None:
        return jsonify({"error": "Authentication service is not configured"}), 503

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
    except Exception as e:
        logger.warning("Firebase token verification failed during registration: %s", e)
        return jsonify({"error": "Invalid or expired token"}), 401

    firebase_uid = decoded_token["uid"]
    email = decoded_token.get("email", "")

    # Check if user already exists
    existing = User.query.filter_by(firebase_uid=firebase_uid).first()
    if existing:
        return jsonify({"error": "Account already exists. Please log in instead."}), 409

    # Charge the card BEFORE creating the user
    description = "Auditmaton for Ad Audits Annual Subscription"
    success, txn_id, error_msg = charge_card(
        opaque_descriptor, opaque_value, total_cents, email, description
    )

    if not success:
        logger.warning("Payment failed for %s: %s", email, error_msg)
        return jsonify({"error": error_msg or "Payment failed. Please try again."}), 402

    # Payment succeeded — create the user
    user = User(
        firebase_uid=firebase_uid,
        email=email,
        first_name=first_name or None,
        last_name=last_name or None,
        email_verified=decoded_token.get("email_verified", False),
    )
    db.session.add(user)
    db.session.commit()

    # Record the payment and create subscription/products
    record_payment(user, txn_id, total_cents, selected_products)

    # Register the first device
    client_ip = request.remote_addr
    if fingerprint_hash:
        register_device(user, fingerprint_hash, request.user_agent.string, client_ip)

    # Update login metadata
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = client_ip
    db.session.commit()

    # Log the user in immediately
    login_user(user, remember=True)

    logger.info(
        "New user registered with payment: %s from %s ($%.2f, products=%s)",
        email, client_ip, total_cents / 100, selected_products
    )

    return jsonify({
        "success": True,
        "redirect": url_for("dashboard_home"),
    })


# ========================================================================
#   Logout Route
# ========================================================================

@auth_bp.route("/logout/", methods=["POST"])
@login_required
def logout():
    """
    Logs the user out by clearing the Flask-Login session.

    Uses POST to prevent CSRF via link prefetching.

    Returns:
        Redirect to the home page.
    """
    logger.info("User %s logged out", current_user.email)
    logout_user()

    # Drop any admin Test as tier override so it never leaks into a later
    # session on this browser
    from services.tier import clear_test_tier
    clear_test_tier()

    flash("You have been logged out.")
    return redirect(url_for("home"))


# ========================================================================
#   Password Reset Route
# ========================================================================

@auth_bp.route("/reset-password/", methods=["GET", "POST"])
@limiter.limit("3 per hour")
def reset_password():
    """
    Renders the password reset page (GET) or triggers a reset email (POST).

    The actual password reset is handled entirely by Firebase. This endpoint
    just triggers the Firebase reset email via the client-side JS SDK.

    Returns:
        GET: Rendered reset_password.html template.
        POST: JSON response confirming the email was sent.
    """
    if request.method == "GET":
        return render_template("auth/reset_password.html")

    # POST is handled client-side by Firebase JS SDK.
    # This endpoint exists so the form has somewhere to submit for
    # progressive enhancement (no-JS fallback).
    return jsonify({"success": True, "message": "If an account exists for that email, a reset link has been sent."})
