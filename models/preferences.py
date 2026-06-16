# models/preferences.py
# Per-user UI preferences keyed by string. Used so a user's view choices
# (filter selections, sort orders, table columns, etc.) follow them
# across devices and browsers. Values are stored as JSON-serialized
# strings so any structure can round-trip through one schema.

import uuid
from datetime import datetime, timezone

from extensions import db


# ========================================================================
#   User Preference Model
# ========================================================================

class UserPreference(db.Model):
    """
    A single key/value preference scoped to a user.

    The value column is a JSON string — callers serialize/deserialize on
    write/read. Keys are namespaced strings (e.g.,
    "worth_it_filter::rich-results") so different features can coexist
    in one table without collision.
    """

    __tablename__ = "user_preferences"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    pref_key = db.Column(db.String(200), nullable=False)
    pref_value = db.Column(db.Text, nullable=False)

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship("User", foreign_keys=[user_id])

    # One row per (user, key) — upserts replace in place
    __table_args__ = (
        db.UniqueConstraint("user_id", "pref_key", name="uq_user_pref"),
        db.Index("ix_user_pref_lookup", "user_id", "pref_key"),
    )

    def __repr__(self):
        """Returns a readable string representation."""
        return f"<UserPreference {self.user_id} :: {self.pref_key}>"
