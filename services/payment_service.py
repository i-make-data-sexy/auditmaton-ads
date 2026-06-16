# services/payment_service.py
# Authorize.net payment processing for Auditmaton for Site Audits. Handles credit card
# charges via Accept.js opaque data (PCI-compliant client-side tokenization)
# and records successful payments in the database. Card numbers never touch
# this server — only the opaque nonce from Accept.js is used.

import logging
from datetime import datetime, timedelta, timezone

from flask import current_app
from extensions import db
from models.billing import Product, UserProduct, UserSubscription, PaymentRecord, TokenTransaction

logger = logging.getLogger(__name__)


# ========================================================================
#   Authorize.net SDK Setup
# ========================================================================

def _get_merchant_auth():
    """
    Creates an Authorize.net merchantAuthentication object from app config.

    Returns:
        apicontractsv1.merchantAuthenticationType: Configured merchant auth,
            or None if credentials are missing.
    """
    from authorizenet import apicontractsv1

    api_login_id = current_app.config.get("AUTHORIZE_NET_API_LOGIN_ID", "")
    transaction_key = current_app.config.get("AUTHORIZE_NET_TRANSACTION_KEY", "")

    if not api_login_id or not transaction_key:
        logger.error("Authorize.net credentials not configured")
        return None

    merchant_auth = apicontractsv1.merchantAuthenticationType()
    merchant_auth.name = api_login_id
    merchant_auth.transactionKey = transaction_key

    return merchant_auth


def _get_environment():
    """
    Returns the Authorize.net API endpoint based on sandbox config.

    Returns:
        str: The Authorize.net API endpoint constant.
    """
    from authorizenet import constants

    if current_app.config.get("AUTHORIZE_NET_SANDBOX", True):
        return constants.SANDBOX
    return constants.PRODUCTION


# ========================================================================
#   Card Charge
# ========================================================================

def charge_card(opaque_data_descriptor, opaque_data_value, amount_cents, user_email, description="Auditmaton for Site Audits Subscription"):
    """
    Charges a credit card using an Accept.js opaque payment nonce.

    The opaque data comes from the client-side Accept.js SDK, which tokenizes
    the card details in the browser. We never see the actual card number.

    Args:
        opaque_data_descriptor (str): The data descriptor from Accept.js (e.g., "COMMON.ACCEPT.INAPP.PAYMENT").
        opaque_data_value (str): The opaque payment nonce from Accept.js.
        amount_cents (int): The charge amount in cents (e.g., 29500 = $295.00).
        user_email (str): Customer email for the transaction record.
        description (str): Line item description for the transaction.

    Returns:
        tuple: (success: bool, transaction_id: str or None, error_message: str or None)
    """
    from authorizenet import apicontractsv1
    from authorizenet.apicontrollers import createTransactionController

    merchant_auth = _get_merchant_auth()
    if not merchant_auth:
        return (False, None, "Payment service is not configured")

    # Build the opaque data payment type
    opaque_data = apicontractsv1.opaqueDataType()
    opaque_data.dataDescriptor = opaque_data_descriptor
    opaque_data.dataValue = opaque_data_value

    payment = apicontractsv1.paymentType()
    payment.opaqueData = opaque_data

    # Build the transaction request
    amount_dollars = f"{amount_cents / 100:.2f}"

    # Line item for the receipt
    line_item = apicontractsv1.lineItemType()
    line_item.itemId = "subscription"
    line_item.name = "Annual Subscription"
    line_item.description = description
    line_item.quantity = "1"
    line_item.unitPrice = amount_dollars

    # Customer email
    customer = apicontractsv1.customerDataType()
    customer.email = user_email

    # Transaction request
    txn_request = apicontractsv1.transactionRequestType()
    txn_request.transactionType = "authCaptureTransaction"
    txn_request.amount = amount_dollars
    txn_request.payment = payment
    txn_request.customer = customer
    txn_request.lineItems = apicontractsv1.ArrayOfLineItem()
    txn_request.lineItems.lineItem = [line_item]

    # API request wrapper
    create_request = apicontractsv1.createTransactionRequest()
    create_request.merchantAuthentication = merchant_auth
    create_request.transactionRequest = txn_request

    # Execute the request
    controller = createTransactionController(create_request)
    controller.setenvironment(_get_environment())
    controller.execute()

    response = controller.getresponse()

    if response is None:
        logger.error("No response from Authorize.net")
        return (False, None, "Payment service did not respond. Please try again.")

    # Check the response
    if response.messages.resultCode == "Ok":
        if hasattr(response, "transactionResponse") and response.transactionResponse:
            txn_response = response.transactionResponse

            # Check for transaction-level errors
            if hasattr(txn_response, "errors") and txn_response.errors:
                error_msg = txn_response.errors.error[0].errorText
                logger.warning("Transaction error: %s", error_msg)
                return (False, None, str(error_msg))

            txn_id = str(txn_response.transId)
            logger.info("Payment approved: transaction %s for $%s", txn_id, amount_dollars)
            return (True, txn_id, None)

    # Handle error response
    error_message = "Payment failed. Please try again."
    if hasattr(response, "transactionResponse") and response.transactionResponse:
        txn_response = response.transactionResponse
        if hasattr(txn_response, "errors") and txn_response.errors:
            error_message = str(txn_response.errors.error[0].errorText)
    elif response.messages and response.messages.message:
        error_message = str(response.messages.message[0].text)

    logger.warning("Payment declined: %s", error_message)
    return (False, None, error_message)


# ========================================================================
#   Payment Recording
# ========================================================================

def record_payment(user, transaction_id, amount_cents, product_slugs):
    """
    Records a successful payment and provisions the user's subscription.

    Creates the PaymentRecord, links purchased products via UserProduct rows,
    creates the UserSubscription, and allocates AI tokens if the AI add-on
    was purchased.

    Args:
        user (User): The user who made the payment.
        transaction_id (str): Authorize.net transaction ID.
        amount_cents (int): Total amount charged in cents.
        product_slugs (list[str]): List of product slugs purchased (e.g., ["base", "viz"]).

    Returns:
        UserSubscription: The newly created subscription.
    """

    # Create payment record
    payment = PaymentRecord(
        user_id=user.id,
        authorize_net_txn_id=transaction_id,
        amount_cents=amount_cents,
        status="approved",
        payment_type="subscription",
    )
    db.session.add(payment)

    # Look up and link purchased products
    total_tokens = 0
    for slug in product_slugs:
        product = Product.query.filter_by(slug=slug, is_active=True).first()
        if product:
            user_product = UserProduct(
                user_id=user.id,
                product_id=product.id,
            )
            db.session.add(user_product)
            total_tokens += product.annual_token_allocation

    # Create subscription
    now = datetime.now(timezone.utc)
    subscription = UserSubscription(
        user_id=user.id,
        status="active",
        start_date=now,
        end_date=now + timedelta(days=365),
        total_price_cents=amount_cents,
        token_balance=total_tokens,
    )
    db.session.add(subscription)

    # Record token allocation if any tokens were granted
    if total_tokens > 0:
        token_txn = TokenTransaction(
            user_id=user.id,
            amount=total_tokens,
            transaction_type="allocation",
            description="Annual AI token allocation",
        )
        db.session.add(token_txn)

    db.session.commit()

    logger.info(
        "Payment recorded for user %s: $%.2f, products=%s, tokens=%d",
        user.email, amount_cents / 100, product_slugs, total_tokens
    )

    return subscription


# ========================================================================
#   Price Calculation
# ========================================================================

def calculate_total(product_slugs):
    """
    Calculates the total price for a set of products.

    Args:
        product_slugs (list[str]): List of product slugs to price.

    Returns:
        tuple: (total_cents: int, products: list[Product]) or (0, []) if invalid.
    """
    products = []
    total_cents = 0

    for slug in product_slugs:
        product = Product.query.filter_by(slug=slug, is_active=True).first()
        if not product:
            return (0, [])
        products.append(product)
        total_cents += product.price_cents

    return (total_cents, products)
