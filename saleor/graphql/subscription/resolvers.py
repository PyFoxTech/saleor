import graphene
import graphene_django_optimizer as gql_optimizer

from ...subscription import SubscriptionStatus, models
from ...subscription.events import SubscriptionEvents
from ...subscription.models import SubscriptionEvent
from ..utils import filter_by_period, filter_by_query_param, sort_queryset
from .enums import SubscriptionStatusFilter
from .sorters import SubscriptionSortField
from .types import Subscription

SUBSCRIPTION_SEARCH_FIELDS = (
        "id", 
        "rrule_str"
        "product_name", 
        "variant_name", 
        "upcoming_order_creation_date",
        "upcoming_delivery_date",
        "token", 
        "user_email", 
        "user__email",
    )


def filter_subscriptions(qs, info, created, status, query):
    qs = filter_by_query_param(qs, query, SUBSCRIPTION_SEARCH_FIELDS)

    if status.lower() in SubscriptionStatusEnum:
        qs = qs.filter(status__exact=status)

    if created is not None:
        qs = filter_by_period(qs, created, "created")

    return gql_optimizer.query(qs, info)


def resolve_subscriptions(info, created, status, query, sort_by=None):
    qs = models.Subscription.objects.confirmed()
    qs = sort_queryset(qs, sort_by, SubscriptionSortField)
    return filter_subscriptions(qs, info, created, status, query)


def resolve_subscription(info, subscription_id):
    return graphene.Node.get_node_from_global_id(info, subscription_id, Subscription)


def resolve_homepage_events():
    # Filter only selected events to be displayed on homepage.
    types = [
        SubscriptionEvents.ACTIVATED,
    ]
    return SubscriptionEvent.objects.filter(type__in=types)


def resolve_subscription_by_token(token):
    return (
        models.Subscription.objects.exclude(status=SubscriptionStatus.ENDED)
        .filter(token=token)
        .first()
    )
