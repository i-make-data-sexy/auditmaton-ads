# models/billing.py
# Billing and subscription models for Auditmaton for Site Audits. Uses a composable
# base + add-ons pricing model: one required Base product ($295/year)
# plus optional add-ons (Viz, AI, Timeline Overlay at $100/year each).
# Authorize.net handles payment processing; this module tracks products,
# subscriptions, token balances, and payment records.

import uuid
from datetime import datetime, timezone

from extensions import db


# ========================================================================
#   Product Model
# ========================================================================

class Product(db.Model):
    """
    Defines purchasable products (base subscription and add-ons).

    The base product is required for all users. Add-on products extend
    functionality (charts, AI features, timeline overlay). Each product
    has a price, feature flags, and an optional token allocation.
    """

    __tablename__ = "products"

    # ================================================
    #   Primary Key
    # ================================================

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ================================================
    #   Product Details
    # ================================================

    # URL-safe identifier (e.g., "base", "viz", "ai", "timeline-overlay")
    slug = db.Column(db.String(50), unique=True, nullable=False)

    # Display name (e.g., "Base", "Viz Add-on")
    display_name = db.Column(db.String(100), nullable=False)

    # Short marketing description shown on the registration page
    description = db.Column(db.String(255), nullable=True)

    # Font Awesome icon class for pricing page cards (e.g., "fa-solid fa-chart-line")
    icon_class = db.Column(db.String(50), nullable=True)

    # Short marketing hook for pricing page cards (e.g., "See Your Data Come Alive")
    marketing_headline = db.Column(db.String(150), nullable=True)

    # Longer marketing copy for pricing page lightbox modals (supports multiple paragraphs)
    marketing_description = db.Column(db.Text, nullable=True)

    # Annual price in cents (e.g., 29500 = $295.00)
    price_cents = db.Column(db.Integer, nullable=False)

    # "base" or "addon" — base is required, addons are optional
    product_type = db.Column(db.String(20), nullable=False)

    # Annual token allocation (only non-zero for AI add-on)
    annual_token_allocation = db.Column(db.Integer, default=0, nullable=False)

    # Feature flags as JSON (e.g., {"charts": true, "ai_narrative": false})
    features = db.Column(db.JSON, default=dict)

    # Whether this product is currently available for purchase
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Display order on the registration page (lower = first)
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    # ================================================
    #   Relationships
    # ================================================

    user_products = db.relationship("UserProduct", backref="product", lazy="dynamic")

    def __repr__(self):
        """Returns a readable string representation of the Product."""
        return f"<Product {self.slug} (${self.price_cents / 100:.2f}/yr)>"


# ========================================================================
#   User Product Junction Model
# ========================================================================

class UserProduct(db.Model):
    """
    Links a user to their purchased products.

    Each row represents one product the user has access to (base or add-on).
    The unique constraint on (user_id, product_id) prevents duplicate purchases.
    """

    __tablename__ = "user_products"

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

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id = db.Column(
        db.String(36),
        db.ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    # ================================================
    #   Timestamps
    # ================================================

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ================================================
    #   Constraints
    # ================================================

    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_user_product"),
    )

    def __repr__(self):
        """Returns a readable string representation of the UserProduct."""
        return f"<UserProduct user={self.user_id} product={self.product_id}>"


# ========================================================================
#   User Subscription Model
# ========================================================================

class UserSubscription(db.Model):
    """
    Tracks a user's active subscription period.

    The subscription is created at registration when payment succeeds.
    The specific products purchased are tracked in the UserProduct
    junction table; this table tracks the subscription lifecycle
    (dates, status, token balance) and the total amount paid.
    """

    __tablename__ = "user_subscriptions"

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
        unique=True,
        nullable=False,
    )

    # ================================================
    #   Subscription Lifecycle
    # ================================================

    # Values: active, cancelled, expired
    status = db.Column(db.String(20), default="active", nullable=False)

    start_date = db.Column(db.DateTime(timezone=True), nullable=False)
    end_date = db.Column(db.DateTime(timezone=True), nullable=True)

    # Total amount paid at purchase (sum of base + selected add-ons) in cents
    total_price_cents = db.Column(db.Integer, default=0, nullable=False)

    # Current token balance (decremented on usage, incremented on purchase/allocation)
    token_balance = db.Column(db.Integer, default=0, nullable=False)

    # ================================================
    #   Timestamps
    # ================================================

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        """Returns a readable string representation of the UserSubscription."""
        return f"<UserSubscription user={self.user_id} ({self.status})>"


# ========================================================================
#   Token Transaction Model
# ========================================================================

class TokenTransaction(db.Model):
    """
    Immutable ledger of all token balance changes.

    Every token allocation, usage, purchase, or refund is recorded
    as a transaction. The token_balance on UserSubscription is the
    running total; this table is the audit trail.
    """

    __tablename__ = "token_transactions"

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
    #   Transaction Details
    # ================================================

    # Positive for credits (allocation, purchase, refund), negative for usage
    amount = db.Column(db.Integer, nullable=False)

    # Values: allocation, usage, purchase, refund, adjustment
    transaction_type = db.Column(db.String(20), nullable=False)

    # Human-readable description (e.g., "Annual allocation", "AI narrative generation")
    description = db.Column(db.String(255), nullable=True)

    # ================================================
    #   Timestamps
    # ================================================

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        """Returns a readable string representation of the TokenTransaction."""
        return f"<TokenTransaction {self.transaction_type} {self.amount:+d}>"


# ========================================================================
#   Payment Record Model
# ========================================================================

class PaymentRecord(db.Model):
    """
    Records payment transactions from Authorize.net.

    Stores the Authorize.net transaction ID, amount, and status for
    subscription payments and token pack purchases. Linked to the
    user who made the payment.
    """

    __tablename__ = "payment_records"

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
    #   Payment Details
    # ================================================

    # Authorize.net transaction reference
    authorize_net_txn_id = db.Column(db.String(100), nullable=True)

    # Amount in cents (e.g., 29500 = $295.00)
    amount_cents = db.Column(db.Integer, nullable=False)

    # Values: pending, approved, declined, refunded, voided
    status = db.Column(db.String(20), nullable=False)

    # What was purchased (e.g., "subscription", "token_pack_5000")
    payment_type = db.Column(db.String(50), nullable=False)

    # ================================================
    #   Timestamps
    # ================================================

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        """Returns a readable string representation of the PaymentRecord."""
        return f"<PaymentRecord {self.payment_type} ${self.amount_cents / 100:.2f} ({self.status})>"
