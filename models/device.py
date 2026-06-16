# models/device.py
# Device session tracking for the 2-device limit per account.
# Uses browser fingerprinting hashes to identify returning devices
# and persistent tokens for cross-session recognition.

import uuid
from datetime import datetime, timezone

from extensions import db


# ========================================================================
#   Device Session Model
# ========================================================================

class DeviceSession(db.Model):
    """
    Tracks authorized devices for each user account.

    Each user is limited to 2 authorized devices to prevent credential
    sharing among agency teams. The fingerprint_hash is a SHA-256 hash
    of the browser fingerprint generated client-side.
    """

    __tablename__ = "device_sessions"

    # ================================================
    #   Primary Key
    # ================================================

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ================================================
    #   Foreign Key
    # ================================================

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ================================================
    #   Device Identification
    # ================================================

    # SHA-256 hash of the browser fingerprint (64 hex characters)
    fingerprint_hash = db.Column(db.String(64), nullable=False, index=True)

    # Persistent token stored in an HttpOnly cookie for device recognition
    device_token = db.Column(db.String(128), unique=True, nullable=True)

    # ================================================
    #   Metadata
    # ================================================

    user_agent = db.Column(db.String(512), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)                    # IPv6 max length is 45
    is_authorized = db.Column(db.Boolean, default=True, nullable=False)

    # ================================================
    #   Timestamps
    # ================================================

    last_seen_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        """Returns a readable string representation of the DeviceSession."""
        return f"<DeviceSession user={self.user_id} fingerprint={self.fingerprint_hash[:8]}...>"
