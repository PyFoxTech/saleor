from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union

from ..account import events as account_events
from ..account.models import User
from ..subscription.models import Subscription, SubscriptionEvent
from . import SubscriptionEvents, SubscriptionEventsEmails

UserType = User

def subscription_draft_created_event(*, subscription: Subscription, user: UserType) -> SubscriptionEvent:
    return SubscriptionEvent.objects.create(
        subscription=subscription,
        type=SubscriptionEvents.DRAFT_CREATED,
        user=user,
    )

def subscription_activated_event(*, subscription: Subscription, user: UserType) -> SubscriptionEvent:
    return SubscriptionEvent.objects.create(
        subscription=subscription,
        type=SubscriptionEvents.ACTIVATED,
        user=user,
    )

def subscription_recurrence_rule_updated_event(*, subscription: Subscription, user: UserType) -> SubscriptionEvent:
    return SubscriptionEvent.objects.create(
        subscription=subscription,
        type=SubscriptionEvents.RECURRENCE_RULE_UPDATED,
        user=user,
        parameters={}
    )

def subscription_shipping_address_updated_event(*, subscription: Subscription, user: UserType) -> SubscriptionEvent:
    return SubscriptionEvent.objects.create(
        subscription=subscription,
        type=SubscriptionEvents.SHIPPING_ADDRESS_UPDATED,
        user=user,
        parameters={}
    )

def subscription_product_quantity_updated_event(*, subscription: Subscription, user: UserType) -> SubscriptionEvent:
    return SubscriptionEvent.objects.create(
        subscription=subscription,
        type=SubscriptionEvents.PRODUCT_QUANTITY_UPDATED,
        user=user,
        parameters={}
    )


def subscription_paused_event(*, subscription: Subscription, user: UserType) -> SubscriptionEvent:
    return SubscriptionEvent.objects.create(
        subscription=subscription,
        type=SubscriptionEvents.PAUSED,
        user=user,
        parameters={}
    )


def subscription_ended_event(*, subscription: Subscription, user: UserType) -> SubscriptionEvent:
    return SubscriptionEvent.objects.create(
        subscription=subscription,
        type=SubscriptionEvents.ENDED,
        user=user,
        parameters={}
    )

def order_note_added_event(*, subscription: Order, user: UserType, message: str) -> OrderEvent:
    kwargs = {}
    if user is not None and not user.is_anonymous:
        if subscription.user is not None and subscription.user.pk == user.pk:
            account_events.customer_added_to_note_subscription_event(
                user=user, subscription=subscription, message=message
            )
        kwargs["user"] = user

    return SubscriptionEvent.objects.create(
        subscription=subscription,
        type=SubscriptionEvents.NOTE_ADDED,
        parameters={"message": message},
        **kwargs,
    )