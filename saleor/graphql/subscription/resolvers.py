import graphene
import graphene_django_optimizer as gql_optimizer

from .types import Subscription
from ...subscription import SubscriptionStatus, models

SUBSCRIPTION_SEARCH_FIELDS = ("id", "token")


def resolve_subscriptions(info, **_kwargs):
    queryset = models.Subscription.objects.filter(user=info.context.user.id)
    return gql_optimizer.query(queryset, info)

def resolve_draft_subscriptions(info, **_kwargs):
    return models.Subscription.objects.confirmed().filter(
        status=SubscriptionStatus.DRAFT)


def resolve_subscription(info, subscription_id):
    return graphene.Node.get_node_from_global_id(info, subscription_id, Subscription)


def resolve_subscription_by_token(token):
    return (
        models.Subscription.objects.exclude(status=SubscriptionStatus.DRAFT)
            .filter(token=token)
            .first()
    )
