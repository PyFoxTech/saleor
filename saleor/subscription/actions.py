import logging
from decimal import Decimal
from typing import TYPE_CHECKING, List

from django.db import transaction

from ..core import analytics
from ..extensions.manager import get_extensions_manager
from . import SubscriptionStatus, emails, events, utils
from .utils import (
    update_subscription_status,
)

if TYPE_CHECKING:
    from .models import Subscription
    from ..account.models import User


logger = logging.getLogger(__name__)


def subscription_draft_created(subscription: "Subscription", user: "User"):
    events.subscription_draft_created_event(subscription=subscription, user=user)
    manager = get_extensions_manager()
    manager.subscription_created(subscription)

def subscription_activated(subscription: "Subscription", user: "User"):
    events.subscription_activated_event(subscription=subscription, user=user)
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.save(update_fields=["status"])
    get_extensions_manager().subscription_updated(subscription)

def subscription_recurrence_rule_updated(
    subscription: "Subscription", 
    user: "User", 
    rrule: str,
    ):
    events.subscription_recurrence_rule_updated_event(
        subscription=subscription, 
        user=user, 
        rrule=rrule,
        )
    subscription.rrule = rrule
    subscription.save(update_fields=["rrule"])
    get_extensions_manager().subscription_updated(subscription)

# def subscription_shipping_updated(subscription: "Subscription"):
#     events.subscription_shipping_address_updated_event(subscription=subscription, user=user)
#     subscription.quantity = quantity
#     subscription.save(update_fields=["quantity"])
#     get_extensions_manager().subscription_updated(subscription)

def subscription_product_quantity_updated(
    subscription: "Subscription", 
    user: "User", 
    quantity: int,
    ):
    events.subscription_product_quantity_updated_event(
        subscription=subscription, 
        user=user, 
        quantity=quantity,
        )
    subscription.quantity = quantity
    subscription.save(update_fields=["quantity"])
    get_extensions_manager().subscription_updated(subscription)

def subscription_paused(subscription: "Subscription", user: "User"):
    events.subscription_paused_event(subscription=subscription, user=user)
    subscription.status = SubscriptionStatus.PAUSED
    subscription.save(update_fields=["status"])
    get_extensions_manager().subscription_updated(subscription)

def end_subscription(subscription: "Subscription", user: "User", restock: bool):
    events.subscription_ended_event(subscription=subscription, user=user)
    subscription.status = SubscriptionStatus.ENDED
    subscription.save(update_fields=["status"])
    manager = get_extensions_manager()
    manager.subscription_ended(subscription)
    manager.subscription_updated(subscription)


