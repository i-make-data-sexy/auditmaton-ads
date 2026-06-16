# models/editorial.py
# Editorial overlay models for Auditmaton for Site Audits. Stores content override
# proposals (with approval workflow) and text-anchored comments that
# layer on top of JSON-rendered audit content. The JSON files remain
# the canonical source; approved overrides are applied at render time.

import uuid
from datetime import datetime, timezone

from extensions import db


# ========================================================================
#   Content Override Model
# ========================================================================

class ContentOverride(db.Model):
    """
    Stores proposed text edits that override JSON-rendered content.

    Each override maps a specific JSON field path to replacement text.
    Overrides are proposed by editors and require owner approval before
    they take effect. The original JSON files are never modified.
    """

    __tablename__ = "content_overrides"

    # ================================================
    #   Primary Key
    # ================================================

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ================================================
    #   Scope
    # ================================================

    # "global" applies to all audits; "audit" applies to one specific audit
    scope = db.Column(db.String(10), default="global", nullable=False)

    # Only set when scope="audit"
    audit_id = db.Column(
        db.String(36),
        db.ForeignKey("audit_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # ================================================
    #   Content Identification
    # ================================================

    # Check identifier matching the JSON check ID (e.g., "robots-txt-non-200")
    check_id = db.Column(db.String(100), nullable=False, index=True)

    # Dot-notation path to the JSON field (e.g., "educate.base", "learn_more[0].source_url")
    field_path = db.Column(db.String(255), nullable=False)

    # ================================================
    #   Override Content
    # ================================================

    # Snapshot of the original text at proposal time
    original_text = db.Column(db.Text, nullable=False)

    # The proposed replacement text
    proposed_text = db.Column(db.Text, nullable=False)

    # The page URL where the edit was proposed (for click-through from dashboard)
    source_url = db.Column(db.String(500), nullable=True)

    # ================================================
    #   Workflow
    # ================================================

    # Values: pending, approved, rejected
    status = db.Column(db.String(20), default="pending", nullable=False)

    # Who proposed the edit
    proposed_by_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
    )

    # Who reviewed (approved/rejected) the edit
    reviewed_by_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=True,
    )

    # Optional note from the reviewer explaining approval or rejection
    review_note = db.Column(db.Text, nullable=True)

    # ================================================
    #   Timestamps
    # ================================================

    proposed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # ================================================
    #   Relationships
    # ================================================

    proposed_by = db.relationship("User", foreign_keys=[proposed_by_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])
    audit = db.relationship("AuditSession", foreign_keys=[audit_id])

    # ================================================
    #   Indexes
    # ================================================

    __table_args__ = (
        db.Index("ix_override_lookup", "check_id", "field_path", "status"),
    )

    def __repr__(self):
        """Returns a readable string representation of the ContentOverride."""
        return f"<ContentOverride {self.check_id}::{self.field_path} ({self.status})>"


# ========================================================================
#   Content Comment Model
# ========================================================================

class ContentComment(db.Model):
    """
    Text-anchored comments on rendered audit content.

    Comments are anchored to specific text selections using the W3C
    Web Annotation approach (exact text + prefix/suffix context).
    Each comment triggers an email notification to feedback@annielytics.com.
    """

    __tablename__ = "content_comments"

    # ================================================
    #   Primary Key
    # ================================================

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ================================================
    #   Context
    # ================================================

    # Nullable because editorial comments can exist before a real audit session
    audit_id = db.Column(
        db.String(36),
        db.ForeignKey("audit_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Check identifier (e.g., "robots-txt-non-200")
    check_id = db.Column(db.String(100), nullable=False, index=True)

    # ================================================
    #   Text Anchor (W3C Web Annotation style)
    # ================================================

    # The data-content-path value identifying the JSON field
    content_path = db.Column(db.String(255), nullable=False)

    # The exact text that was selected
    anchor_exact = db.Column(db.Text, nullable=False)

    # ~30 characters before and after the selection for robust re-anchoring
    anchor_prefix = db.Column(db.String(100), nullable=True)
    anchor_suffix = db.Column(db.String(100), nullable=True)

    # Fallback character offsets within the content_path element
    anchor_start_offset = db.Column(db.Integer, nullable=True)
    anchor_end_offset = db.Column(db.Integer, nullable=True)

    # The page URL where the comment was made (for click-through from dashboard)
    source_url = db.Column(db.String(500), nullable=True)

    # ================================================
    #   Comment Content
    # ================================================

    comment_text = db.Column(db.Text, nullable=False)

    author_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
    )

    # ================================================
    #   State
    # ================================================

    resolved = db.Column(db.Boolean, default=False, nullable=False)

    resolved_by_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=True,
    )

    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # ================================================
    #   Timestamps
    # ================================================

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ================================================
    #   Relationships
    # ================================================

    author = db.relationship("User", foreign_keys=[author_id])
    resolved_by = db.relationship("User", foreign_keys=[resolved_by_id])
    audit = db.relationship("AuditSession", foreign_keys=[audit_id])
    replies = db.relationship(
        "CommentReply",
        backref="parent_comment",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        """Returns a readable string representation of the ContentComment."""
        return f"<ContentComment {self.check_id} by={self.author_id}>"


# ========================================================================
#   Comment Reply Model
# ========================================================================

class CommentReply(db.Model):
    """
    Threaded replies on content comments.

    Supports a flat reply thread (no nesting) under each parent comment.
    """

    __tablename__ = "comment_replies"

    # ================================================
    #   Primary Key
    # ================================================

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ================================================
    #   Foreign Keys
    # ================================================

    comment_id = db.Column(
        db.String(36),
        db.ForeignKey("content_comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
    )

    # ================================================
    #   Content
    # ================================================

    reply_text = db.Column(db.Text, nullable=False)

    # ================================================
    #   Timestamps
    # ================================================

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ================================================
    #   Relationships
    # ================================================

    author = db.relationship("User", foreign_keys=[author_id])

    def __repr__(self):
        """Returns a readable string representation of the CommentReply."""
        return f"<CommentReply comment={self.comment_id}>"
