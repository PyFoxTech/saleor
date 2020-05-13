import logging
from decimal import Decimal
from typing import TYPE_CHECKING, List

from django.db import transaction

from ..core import analytics
from ..extensions.manager import get_extensions_manager
from ..payment import ChargeStatus, CustomPaymentChoices, PaymentError
from ..warehouse.management import decrease_stock
from . import SubscriptionStatus, emails, events, utils
from .emails import send_fulfillment_confirmation_to_customer, send_payment_confirmation
from .utils import (
    get_subscription_country,
    subscription_line_needs_automatic_fulfillment,
    recalculate_subscription,
    restock_fulfillment_lines,
    update_subscription_status,
)

if TYPE_CHECKING:
    from .models import Subscription
    from ..account.models import User
    from ..payment.models import Payment


logger = logging.getLogger(__name__)


def subscription_created(subscription: "Subscription", user: "User"):
    events.subscription_activated_event(subscription=subscription, user=user)
    manager = get_extensions_manager()
    manager.subscription_created(subscription)


def handle_fully_paid_subscription(subscription: "Subscription"):
    events.subscription_fully_paid_event(subscription=subscription)

    if subscription.get_customer_email():
        events.email_sent_event(
            subscription=subscription, user=None, email_type=events.SubscriptionEventsEmails.PAYMENT
        )
        send_payment_confirmation.delay(subscription.pk)

        if utils.subscription_needs_automatic_fullfilment(subscription):
            automatically_fulfill_digital_lines(subscription)
    try:
        analytics.report_subscription(subscription.tracking_client_id, subscription)
    except Exception:
        # Analytics failing should not abort the checkout flow
        logger.exception("Recording subscription in analytics failed")
    manager = get_extensions_manager()
    manager.subscription_fully_paid(subscription)
    manager.subscription_updated(subscription)


def cancel_subscription(subscription: "Subscription", user: "User", restock: bool):
    """Cancel subscription and associated fulfillments.

    Return products to corresponding stocks if restock is set to True.
    """

    events.subscription_canceled_event(subscription=subscription, user=user)
    if restock:
        events.fulfillment_restocked_items_event(
            subscription=subscription, user=user, fulfillment=subscription
        )
        utils.restock_subscription_lines(subscription)

    for fulfillment in subscription.fulfillments.all():
        fulfillment.status = FulfillmentStatus.CANCELED
        fulfillment.save(update_fields=["status"])
    subscription.status = SubscriptionStatus.CANCELED
    subscription.save(update_fields=["status"])

    payments = subscription.payments.filter(is_active=True).exclude(
        charge_status=ChargeStatus.FULLY_REFUNDED
    )

    from ..payment import gateway

    for payment in payments:
        if payment.can_refund():
            gateway.refund(payment)
        elif payment.can_void():
            gateway.void(payment)

    manager = get_extensions_manager()
    manager.subscription_cancelled(subscription)
    manager.subscription_updated(subscription)


def subscription_refunded(subscription: "Subscription", user: "User", amount: "Decimal", payment: "Payment"):
    events.payment_refunded_event(
        subscription=subscription, user=user, amount=amount, payment=payment
    )
    get_extensions_manager().subscription_updated(subscription)


def subscription_voided(subscription: "Subscription", user: "User", payment: "Payment"):
    events.payment_voided_event(subscription=subscription, user=user, payment=payment)
    get_extensions_manager().subscription_updated(subscription)


def subscription_fulfilled(
    fulfillment: "Fulfillment",
    user: "User",
    fulfillment_lines: List["FulfillmentLine"],
    notify_customer=True,
):
    subscription = fulfillment.subscription
    update_subscription_status(subscription)
    events.fulfillment_fulfilled_items_event(
        subscription=subscription, user=user, fulfillment_lines=fulfillment_lines
    )
    manager = get_extensions_manager()
    manager.subscription_updated(subscription)

    if subscription.status == SubscriptionStatus.FULFILLED:
        manager.subscription_fulfilled(subscription)

    if notify_customer:
        send_fulfillment_confirmation_to_customer(subscription, fulfillment, user)


def subscription_shipping_updated(subscription: "Subscription"):
    recalculate_subscription(subscription)
    get_extensions_manager().subscription_updated(subscription)


def subscription_captured(subscription: "Subscription", user: "User", amount: "Decimal", payment: "Payment"):
    events.payment_captured_event(
        subscription=subscription, user=user, amount=amount, payment=payment
    )
    get_extensions_manager().subscription_updated(subscription)


def fulfillment_tracking_updated(
    fulfillment: "Fulfillment", user: "User", tracking_number: str
):
    events.fulfillment_tracking_updated_event(
        subscription=fulfillment.subscription,
        user=user,
        tracking_number=tracking_number,
        fulfillment=fulfillment,
    )
    get_extensions_manager().subscription_updated(fulfillment.subscription)


def cancel_fulfillment(fulfillment: "Fulfillment", user: "User", restock: bool):
    """Cancel fulfillment.

    Return products to corresponding stocks if restock is set to True.
    """
    events.fulfillment_canceled_event(
        subscription=fulfillment.subscription, user=user, fulfillment=fulfillment
    )
    if restock:
        events.fulfillment_restocked_items_event(
            subscription=fulfillment.subscription, user=user, fulfillment=fulfillment
        )
        restock_fulfillment_lines(fulfillment)
    for line in fulfillment:
        subscription_line = line.subscription_line
        subscription_line.quantity_fulfilled -= line.quantity
        subscription_line.save(update_fields=["quantity_fulfilled"])
    fulfillment.status = FulfillmentStatus.CANCELED
    fulfillment.save(update_fields=["status"])
    update_subscription_status(fulfillment.subscription)
    get_extensions_manager().subscription_updated(fulfillment.subscription)


@transaction.atomic
def mark_subscription_as_paid(subscription: "Subscription", request_user: "User"):
    """Mark subscription as paid.

    Allows to create a payment for an subscription without actually performing any
    payment by the gateway.
    """
    # pylint: disable=cyclic-import
    from ..payment.utils import create_payment

    payment = create_payment(
        gateway=CustomPaymentChoices.MANUAL,
        payment_token="",
        currency=subscription.total.gross.currency,
        email=subscription.user_email,
        total=subscription.total.gross.amount,
        subscription=subscription,
    )
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = subscription.total.gross.amount
    payment.save(update_fields=["captured_amount", "charge_status", "modified"])

    events.subscription_manually_marked_as_paid_event(subscription=subscription, user=request_user)
    manager = get_extensions_manager()
    manager.subscription_fully_paid(subscription)
    manager.subscription_updated(subscription)


def clean_mark_subscription_as_paid(subscription: "Subscription"):
    """Check if an subscription can be marked as paid."""
    if subscription.payments.exists():
        raise PaymentError("Subscriptions with payments can not be manually marked as paid.",)


def fulfill_subscription_line(subscription_line, quantity):
    """Fulfill subscription line with given quantity."""
    country = get_subscription_country(subscription_line.subscription)
    if subscription_line.variant and subscription_line.variant.track_inventory:
        decrease_stock(subscription_line.variant, country, quantity)
    subscription_line.quantity_fulfilled += quantity
    subscription_line.save(update_fields=["quantity_fulfilled"])


def automatically_fulfill_digital_lines(subscription: "Subscription"):
    """Fulfill all digital lines which have enabled automatic fulfillment setting.

    Send confirmation email afterward.
    """
    digital_lines = subscription.lines.filter(
        is_shipping_required=False, variant__digital_content__isnull=False
    )
    digital_lines = digital_lines.prefetch_related("variant__digital_content")

    if not digital_lines:
        return
    fulfillment, _ = Fulfillment.objects.get_or_create(subscription=subscription)
    for line in digital_lines:
        if not subscription_line_needs_automatic_fulfillment(line):
            continue
        if line.variant:
            digital_content = line.variant.digital_content
            digital_content.urls.create(line=line)
        quantity = line.quantity
        FulfillmentLine.objects.create(
            fulfillment=fulfillment, subscription_line=line, quantity=quantity
        )
        fulfill_subscription_line(subscription_line=line, quantity=quantity)
    emails.send_fulfillment_confirmation_to_customer(
        subscription, fulfillment, user=subscription.user
    )
    update_subscription_status(subscription)
