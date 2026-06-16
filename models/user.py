# models/user.py
# User account model for Auditmaton for Site Audits. Stores account metadata and
# links to Firebase Authentication for credential management.
# Passwords are never stored here — only the Firebase UID.

import uuid
from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy.ext.associationproxy import association_proxy
from extensions import db


# ========================================================================
#   User Model
# ========================================================================

class User(UserMixin, db.Model):
    """
    Core user account.

    Credentials are managed by Firebase Authentication. This table stores
    the Firebase UID as a foreign key reference, along with profile data,
    account state, and login tracking for security monitoring.
    """

    __tablename__ = "users"

    # ================================================
    #   Primary Key
    # ================================================

    # UUID prevents user enumeration attacks
    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ================================================
    #   Firebase Link
    # ================================================

    # Firebase Authentication UID — the only credential reference we store
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False, index=True)

    # ================================================
    #   Profile
    # ================================================

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)

    # ================================================
    #   Account State
    # ================================================

    is_active = db.Column(db.Boolean, default=True, nullable=False)         # Can log in
    is_admin = db.Column(db.Boolean, default=False, nullable=False)         # Admin access
    email_verified = db.Column(db.Boolean, default=False, nullable=False)   # Email confirmed via Firebase

    # Role-based access for editorial features and the admin hub.
    # Values: owner, admin, editor, contributor, viewer
    # 'admin' has admin-hub access plus the same editorial powers as
    # 'editor' (contributor, editor, and admin-allowed routes also
    # accept 'admin'). Routes gated specifically on 'owner' stay
    # owner-only.
    role = db.Column(db.String(20), default="viewer", nullable=False)

    # ================================================
    #   Security: Login Tracking
    # ================================================

    # Account lockout after repeated failed login attempts
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime(timezone=True), nullable=True)

    # Last login metadata for security monitoring
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)                 # IPv6 max length is 45

    # ================================================
    #   Timestamps
    # ================================================

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ================================================
    #   Relationships
    # ================================================

    devices = db.relationship("DeviceSession", backref="user", lazy="dynamic")
    audits = db.relationship("AuditSession", backref="user", lazy="dynamic")
    subscription = db.relationship("UserSubscription", backref="user", uselist=False)
    token_transactions = db.relationship("TokenTransaction", backref="user", lazy="dynamic")
    user_products = db.relationship("UserProduct", backref="user", lazy="select")

    def __repr__(self):
        """Returns a readable string representation of the User."""
        return f"<User {self.email}>"

    def is_locked(self):
        """
        Checks whether the account is currently locked due to failed login attempts.

        Returns:
            bool: True if the account is locked and the lock has not expired.
        """
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    # ================================================
    #   Subscription & Product Helpers
    # ================================================

    @property
    def has_active_subscription(self):
        """
        Checks whether the user has a current, active subscription.

        Returns:
            bool: True if subscription exists, is active, and has not expired.
        """
        if not self.subscription:
            return False
        if self.subscription.status != "active":
            return False
        if self.subscription.end_date and datetime.now(timezone.utc) > self.subscription.end_date:
            return False
        return True

    def has_product(self, slug):
        """
        Checks whether the user has purchased a specific product.

        Args:
            slug (str): Product slug (e.g., "viz", "ai", "timeline-overlay").

        Returns:
            bool: True if the user owns the product.
        """
        for up in self.user_products:
            if up.product and up.product.slug == slug:
                return True
        return False

    # ================================================
    #   Editorial Role Helpers
    # ================================================

    @property
    def can_propose_edits(self):
        """
        Checks whether the user can propose inline text edits.

        Returns:
            bool: True if user has editor or owner role.
        """
        return self.role in ("editor", "owner")

    @property
    def can_comment(self):
        """
        Checks whether the user can leave text-anchored comments.

        Returns:
            bool: True if user has contributor, editor, or owner role.
        """
        return self.role in ("contributor", "editor", "owner")

    @property
    def can_approve_edits(self):
        """
        Checks whether the user can approve or reject edit proposals.

        Returns:
            bool: True if user has owner role.
        """
        return self.role == "owner"
