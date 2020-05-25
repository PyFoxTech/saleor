import graphene

from .mutations import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionEnd,
)
from .resolvers import resolve_subscription, resolve_subscriptions, \
    resolve_subscription_by_token, resolve_draft_subscriptions
from .types import Subscription
from ..core.fields import FilterInputConnectionField


class SubscriptionQueries(graphene.ObjectType):
    subscription = graphene.Field(
        Subscription,
        description="Look up a subscription by ID.",
        id=graphene.Argument(graphene.ID, description="ID of a subscription.",
                             required=True),
    )
    subscriptions = FilterInputConnectionField(
        Subscription,
        description="List of subscriptions.",
    )
    draft_subscriptions = FilterInputConnectionField(
        Subscription,
        # sort_by=OrderSortingInput(description="Sort draft orders."),
        # filter=OrderDraftFilterInput(description="Filtering options for draft orders."),
        description="List of draft subscriptions.",
    )

    subscription_by_token = graphene.Field(
        Subscription,
        description="Look up a subscription by token.",
        token=graphene.Argument(
            graphene.UUID, description="The subscription's token.", required=True
        ),
    )

    def resolve_subscription(self, info, **data):
        return resolve_subscription(info, data.get("id"))

    def resolve_subscriptions(self, info, **_kwargs):
        return resolve_subscriptions(info)

    def resolve_draft_subscriptions(self, info, **_kwargs):
        return resolve_draft_subscriptions(info)

    def resolve_subscription_by_token(self, _info, token):
        return resolve_subscription_by_token(token)


class SubscriptionMutations(graphene.ObjectType):
    subscription_create = SubscriptionCreate.Field()
    subscription_update = SubscriptionUpdate.Field()
    subscription_end = SubscriptionEnd.Field()
