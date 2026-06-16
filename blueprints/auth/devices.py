# blueprints/auth/devices.py
# Device fingerprinting and 2-device limit enforcement for Auditmaton for Site Audits.
# Uses browser fingerprint hashes to identify returning devices and
# persistent tokens for cross-session recognition. Each user is limited
# to 2 authorized devices to prevent credential sharing.

import secrets
from datetime import datetime, timezone

from extensions import db
from models.device import DeviceSession


# ========================================================================
#   Constants
# ========================================================================

MAX_DEVICES_PER_USER = 2


# ========================================================================
#   Device Validation
# ========================================================================

def validate_device(user, fingerprint_hash):
    """
    Checks whether a device is authorized for the given user.

    Returns the DeviceSession if this fingerprint is already authorized,
    or None if it is a new/unrecognized device.

    Args:
        user: The User model instance.
        fingerprint_hash (str): SHA-256 hash of the browser fingerprint.

    Returns:
        DeviceSession or None: The existing authorized device, or None.
    """
    return DeviceSession.query.filter_by(
        user_id=user.id,
        fingerprint_hash=fingerprint_hash,
        is_authorized=True,
    ).first()


def can_register_device(user):
    """
    Checks whether the user has room for another device.

    Admins bypass the 2-device cap so support/dev work isn't gated by
    the same fingerprint accounting that protects against credential
    sharing on regular accounts.

    Args:
        user: The User model instance.

    Returns:
        bool: True if the user has fewer than MAX_DEVICES_PER_USER authorized devices.
    """
    if getattr(user, "is_admin", False):
        return True

    active_count = DeviceSession.query.filter_by(
        user_id=user.id,
        is_authorized=True,
    ).count()

    return active_count < MAX_DEVICES_PER_USER


def register_device(user, fingerprint_hash, user_agent, ip_address):
    """
    Registers a new device for the user and returns a persistent device token.

    Call can_register_device() first to check the limit.

    Args:
        user: The User model instance.
        fingerprint_hash (str): SHA-256 hash of the browser fingerprint.
        user_agent (str): The browser's User-Agent string.
        ip_address (str): The client's IP address.

    Returns:
        DeviceSession: The newly created device session.
    """

    # Generate a cryptographically random device token for cookie-based recognition
    device_token = secrets.token_urlsafe(64)

    device = DeviceSession(
        user_id=user.id,
        fingerprint_hash=fingerprint_hash,
        device_token=device_token,
        user_agent=user_agent,
        ip_address=ip_address,
        is_authorized=True,
    )

    db.session.add(device)
    db.session.commit()

    return device


def update_device_activity(device, ip_address):
    """
    Updates the last-seen timestamp and IP address for a returning device.

    Args:
        device (DeviceSession): The device session to update.
        ip_address (str): The client's current IP address.
    """
    device.last_seen_at = datetime.now(timezone.utc)
    device.ip_address = ip_address
    db.session.commit()


def get_user_devices(user):
    """
    Returns all authorized devices for a user.

    Args:
        user: The User model instance.

    Returns:
        list[DeviceSession]: List of authorized device sessions.
    """
    return DeviceSession.query.filter_by(
        user_id=user.id,
        is_authorized=True,
    ).order_by(DeviceSession.last_seen_at.desc()).all()


def revoke_device(device_id, user):
    """
    Revokes authorization for a specific device.

    Users can revoke a device to free up a slot for a new one.

    Args:
        device_id (str): The UUID of the device session to revoke.
        user: The User model instance (for ownership verification).

    Returns:
        bool: True if the device was found and revoked, False otherwise.
    """
    device = DeviceSession.query.filter_by(
        id=device_id,
        user_id=user.id,
        is_authorized=True,
    ).first()

    if not device:
        return False

    device.is_authorized = False
    db.session.commit()
    return True


def find_device_by_token(device_token):
    """
    Looks up a device by its persistent token (from cookie).

    Used to recognize returning devices even after session expiry.

    Args:
        device_token (str): The persistent device token.

    Returns:
        DeviceSession or None: The matching device session, or None.
    """
    if not device_token:
        return None

    return DeviceSession.query.filter_by(
        device_token=device_token,
        is_authorized=True,
    ).first()
