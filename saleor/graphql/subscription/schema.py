import graphene

from ...core.permissions import SubscriptionPermissions
from ..core.enums import ReportingPeriod
from ..core.fields import FilterInputConnectionField, PrefetchingConnectionField
from ..core.types import FilterInputObjectType, TaxedMoney
from ..decorators import permission_required
from .enums import SubscriptionStatusFilter
from .filters import DraftSubscriptionFilter, SubscriptionFilter
from .mutations.subscriptions import (
    SubscriptionAddNote,
    SubscriptionPause,
    SubscriptionActivate,
    SubscriptionEnd,
    SubscriptionClearMeta,
    SubscriptionClearPrivateMeta,
    SubscriptionUpdate,
    SubscriptionUpdateMeta,
    SubscriptionUpdatePrivateMeta,
    SubscriptionUpdateShipping,
    SubscriptionVoid,
)
from .resolvers import (
    resolve_subscription,
    resolve_subscriptions,
    resolve_homepage_events,
    resolve_subscription_by_token,
)
from .sorters import SubscriptionSortingInput
from .types import Subscription, SubscriptionEvent


class SubscriptionFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = SubscriptionFilter


class SubscriptionQueries(graphene.ObjectType):
    homepage_events = PrefetchingConnectionField(
        SubscriptionEvent,
        description=(
            "List of activity events to display on "
            "homepage (at the moment it only contains subscription-events)."
        ),
    )
    subscription = graphene.Field(
        Subscription,
        description="Look up an subscription by ID.",
        id=graphene.Argument(graphene.ID, description="ID of an subscription.", required=True),
    )
    subscriptions = FilterInputConnectionField(
        Subscription,
        sort_by=SubscriptionSortingInput(description="Sort subscriptions."),
        filter=SubscriptionFilterInput(description="Filtering options for subscriptions."),
        created=graphene.Argument(
            ReportingPeriod,
            description=(
                "Filter subscriptions from a selected timespan. "
                "DEPRECATED: Will be removed in Saleor 2.11, "
                "use the `filter` field instead."
            ),
        ),
        status=graphene.Argument(
            SubscriptionStatusFilter,
            description=(
                "Filter subscription by status. "
                "DEPRECATED: Will be removed in Saleor 2.11, "
                "use the `filter` field instead."
            ),
        ),
        description="List of subscriptions.",
    )
    subscription_by_token = graphene.Field(
        Subscription,
        description="Look up an subscription by token.",
        token=graphene.Argument(
            graphene.UUID, description="The subscription's token.", required=True
        ),
    )

    @permission_required(SubscriptionPermissions.MANAGE_SUBSCRIPTIONS)
    def resolve_homepage_events(self, *_args, **_kwargs):
        return resolve_homepage_events()

    @permission_required(SubscriptionPermissions.MANAGE_SUBSCRIPTIONS)
    def resolve_subscription(self, info, **data):
        return resolve_subscription(info, data.get("id"))

    @permission_required(SubscriptionPermissions.MANAGE_SUBSCRIPTIONS)
    def resolve_subscriptions(
        self, info, created=None, status=None, query=None, sort_by=None, **_kwargs
    ):
        return resolve_subscriptions(info, created, status, query, sort_by)

    def resolve_subscription_by_token(self, _info, token):
        return resolve_subscription_by_token(token)


class SubscriptionMutations(graphene.ObjectType):
    subscription_add_note = SubscriptionAddNote.Field()
    subscription_pause = SubscriptionPause.Field()
    subscription_activate = SubscriptionActivate.Field()
    subscription_end = SubscriptionEnd.Field()
    subscription_clear_meta = SubscriptionClearMeta.Field()
    subscription_clear_private_meta = SubscriptionClearPrivateMeta.Field()
    subscription_update = SubscriptionUpdate.Field()
    subscription_update_meta = SubscriptionUpdateMeta.Field()
    subscription_update_private_meta = SubscriptionUpdatePrivateMeta.Field()
    subscription_update_shipping = SubscriptionUpdateShipping.Field()
    subscription_void = SubscriptionVoid.Field()