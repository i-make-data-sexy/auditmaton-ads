# models/audit.py
# Audit-related models for Auditmaton for Site Audits. Tracks audit sessions, intake
# selections, individual check completions, crawl file uploads, column
# mappings, and canvas (rich text) content blocks.

import uuid
from datetime import datetime, timezone

from extensions import db


# ========================================================================
#   Audit Session Model
# ========================================================================

class AuditSession(db.Model):
    """
    Represents a single audit engagement for a domain.

    Users can have multiple audit sessions (one per site they audit).
    Each session tracks overall progress, the subscription tier at
    creation time, and links to all related audit data.
    """

    __tablename__ = "audit_sessions"

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
    #   Audit Details
    # ================================================

    # The domain being audited (e.g., "example.com")
    domain = db.Column(db.String(255), nullable=False)

    # Current status of the audit
    status = db.Column(
        db.String(20),
        default="in_progress",
        nullable=False,
    )  # Values: in_progress, completed, archived

    # Subscription tier when audit was created (for feature gating)
    tier_at_creation = db.Column(db.String(20), nullable=False)             # Values: base, viz, ai

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

    intake = db.relationship("AuditIntake", backref="audit", uselist=False, cascade="all, delete-orphan")
    check_completions = db.relationship("AuditCheckCompletion", backref="audit", lazy="dynamic", cascade="all, delete-orphan")
    crawl_files = db.relationship("CrawlFile", backref="audit", lazy="dynamic", cascade="all, delete-orphan")
    column_mappings = db.relationship("ColumnMapping", backref="audit", lazy="dynamic", cascade="all, delete-orphan")
    canvas_blocks = db.relationship("CanvasBlock", backref="audit", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        """Returns a readable string representation of the AuditSession."""
        return f"<AuditSession {self.domain} ({self.status})>"


# ========================================================================
#   Audit Intake Model
# ========================================================================

class AuditIntake(db.Model):
    """
    Stores intake form selections for an audit session.

    Captures all choices from the 5-step intake wizard: site types,
    Rich Results schemas, international flag, crawl tool, SEO tools,
    and JavaScript frameworks. Persisted to the database so users can
    resume audits across sessions and devices.
    """

    __tablename__ = "audit_intakes"

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

    audit_id = db.Column(
        db.String(36),
        db.ForeignKey("audit_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # ================================================
    #   Intake Selections (JSON columns for flexible list data)
    # ================================================

    # Step 1: Site profile
    site_types = db.Column(db.JSON, default=list)                           # e.g., ["ecommerce", "publishing"]
    rich_results_schemas = db.Column(db.JSON, default=list)                 # e.g., ["article", "product", "faq"]
    international = db.Column(db.Boolean, default=False)

    # Step 2: Site size
    site_size = db.Column(db.String(50), nullable=True)                     # e.g., "small", "medium", "large", "enterprise"

    # Step 3: (Crawl file upload handled by CrawlFile model)

    # Step 4: Tools and frameworks
    crawl_tool = db.Column(db.String(50), nullable=True)                    # e.g., "screaming_frog", "sitebulb"
    seo_tools = db.Column(db.JSON, default=list)                            # e.g., ["ahrefs", "gsc", "semrush"]
    js_frameworks = db.Column(db.JSON, default=list)                        # e.g., ["react_nextjs", "no_minimal"]
    has_ads = db.Column(db.Boolean, default=False)

    # Step 5: Branding and voice preferences
    brand_colors = db.Column(db.JSON, nullable=True)                        # e.g., {"primary": "#FFA500", "secondary": "#0273BE"}
    narrative_voice = db.Column(db.String(50), nullable=True)               # e.g., "professional", "casual"

    # Server log access (sophistication signal for enterprise clients)
    has_server_logs = db.Column(db.Boolean, default=False)

    # ================================================
    #   Timestamps
    # ================================================

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        """Returns a readable string representation of the AuditIntake."""
        return f"<AuditIntake audit={self.audit_id}>"


# ========================================================================
#   Audit Check Completion Model
# ========================================================================

class AuditCheckCompletion(db.Model):
    """
    Tracks the completion status of individual audit checks.

    Each row represents one check within a category/subcategory.
    The check_id matches the JSON filename (e.g., 'title_tags').
    """

    __tablename__ = "audit_check_completions"

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

    audit_id = db.Column(
        db.String(36),
        db.ForeignKey("audit_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ================================================
    #   Check Identification
    # ================================================

    # Category directory name (e.g., "crawl", "content", "ai-geo")
    category = db.Column(db.String(50), nullable=False)

    # Subcategory slug (e.g., "title-tags", "meta-descriptions")
    subcategory = db.Column(db.String(100), nullable=False)

    # Individual check identifier matching the JSON filename
    check_id = db.Column(db.String(100), nullable=False)

    # ================================================
    #   Status
    # ================================================

    # Values: not_started, in_progress, completed, skipped
    status = db.Column(db.String(20), default="not_started", nullable=False)

    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # ================================================
    #   Unique Constraint
    # ================================================

    # One completion record per check per audit
    __table_args__ = (
        db.UniqueConstraint("audit_id", "check_id", name="uq_audit_check"),
    )

    def __repr__(self):
        """Returns a readable string representation of the AuditCheckCompletion."""
        return f"<AuditCheckCompletion {self.check_id} ({self.status})>"


# ========================================================================
#   Crawl File Model
# ========================================================================

class CrawlFile(db.Model):
    """
    Tracks crawl CSV file uploads for an audit session.

    Files are stored on the local filesystem under the uploads/
    directory. This table records the file path, original filename,
    and metadata. Users can update their crawl file mid-audit from
    the dashboard scorecard-utility div.
    """

    __tablename__ = "crawl_files"

    # ================================================
    #   Primary Key
    # ================================================

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ================================================
    #   Foreign Keys and Ownership
    # ================================================

    # Nullable until AuditSession creation is wired into intake flow
    audit_id = db.Column(
        db.String(36),
        db.ForeignKey("audit_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Owner of the file (allows lookup before audit_id is assigned)
    user_id = db.Column(db.String(36), nullable=False, index=True)

    # ================================================
    #   File Details
    # ================================================

    # Local filesystem path relative to UPLOAD_FOLDER (e.g., "user_id/crawl-20260305.csv")
    file_path = db.Column(db.String(500), nullable=False)

    # Original filename as uploaded by the user
    original_filename = db.Column(db.String(255), nullable=False)

    # File metadata
    row_count = db.Column(db.Integer, nullable=True)
    column_count = db.Column(db.Integer, nullable=True)

    # Whether this is the currently active crawl file for the audit
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # ================================================
    #   Processing Status
    # ================================================

    # Background task lifecycle: pending → queued → processing → complete | failed
    processing_status = db.Column(db.String(20), default="pending", nullable=False)

    # Huey task ID for status polling
    task_id = db.Column(db.String(64), nullable=True)

    # Error message if processing failed
    processing_error = db.Column(db.Text, nullable=True)

    # ================================================
    #   Timestamps
    # ================================================

    uploaded_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    processing_started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    processing_completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def __repr__(self):
        """Returns a readable string representation of the CrawlFile."""
        return f"<CrawlFile {self.original_filename}>"


# ========================================================================
#   Column Mapping Model
# ========================================================================

class ColumnMapping(db.Model):
    """
    Maps crawl file column headers to canonical internal keys.

    Different crawl tools (Screaming Frog, Sitebulb, Ahrefs, etc.)
    use different column names for the same data. This table stores
    the mapping so the audit engine can work with standardized keys.
    """

    __tablename__ = "column_mappings"

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

    audit_id = db.Column(
        db.String(36),
        db.ForeignKey("audit_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ================================================
    #   Mapping Data
    # ================================================

    # Internal canonical key (e.g., "title", "meta_description", "status_code")
    canonical_key = db.Column(db.String(100), nullable=False)

    # The actual header from the user's crawl file (e.g., "Title 1", "Meta Description 1")
    user_header = db.Column(db.String(255), nullable=False)

    # ================================================
    #   Unique Constraint
    # ================================================

    # One mapping per canonical key per audit
    __table_args__ = (
        db.UniqueConstraint("audit_id", "canonical_key", name="uq_audit_column"),
    )

    def __repr__(self):
        """Returns a readable string representation of the ColumnMapping."""
        return f"<ColumnMapping {self.canonical_key} → {self.user_header}>"


# ========================================================================
#   Canvas Block Model
# ========================================================================

class CanvasBlock(db.Model):
    """
    Stores rich text content created by users in the Canvas editor.

    Each block belongs to a specific audit check and contains the
    user's notes, findings, and recommendations written in the
    Quill.js rich text editor.
    """

    __tablename__ = "canvas_blocks"

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

    audit_id = db.Column(
        db.String(36),
        db.ForeignKey("audit_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The check this canvas block belongs to (matches JSON filename)
    check_id = db.Column(db.String(100), nullable=False)

    # ================================================
    #   Content
    # ================================================

    # Quill.js Delta format stored as JSON
    content = db.Column(db.JSON, nullable=True)

    # Display order within the check's canvas
    position = db.Column(db.Integer, default=0, nullable=False)

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

    def __repr__(self):
        """Returns a readable string representation of the CanvasBlock."""
        return f"<CanvasBlock check={self.check_id} pos={self.position}>"
