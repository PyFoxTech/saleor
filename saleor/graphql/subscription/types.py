import graphene
import graphene_django_optimizer as gql_optimizer
from django.core.exceptions import ValidationError
from graphene import relay
from graphql_jwt.exceptions import PermissionDenied
from dateutil.rrule import rrule, rrulestr

from ...core.permissions import AccountPermissions, SubscriptionPermissions
from ...extensions.manager import get_extensions_manager
from ...subscription import models
from ..account.types import User
from ..core.connection import CountableDjangoObjectType
from ..core.resolvers import resolve_meta, resolve_private_meta
from ..core.types.common import Image
from ..core.types.meta import MetadataObjectType
from ..core.types.money import Money, TaxedMoney
from ..decorators import permission_required
from ..product.types import ProductVariant
from .enums import SubscriptionEventsEmailsEnum, SubscriptionEventsEnum


class SubscriptionEvent(CountableDjangoObjectType):
    date = graphene.types.datetime.DateTime(
        description="Date when event happened at in ISO 8601 format."
    )
    type = SubscriptionEventsEnum(description="Subscription event type.")
    user = graphene.Field(User, description="User who performed the action.")
    message = graphene.String(description="Content of the event.")
    email = graphene.String(description="Email of the customer.")
    email_type = SubscriptionEventsEmailsEnum(
        description="Type of an email sent to the customer."
    )
    quantity = graphene.Int(description="Number of items.")
    subscription_number = graphene.String(description="User-friendly number of an subscription.")


    class Meta:
        description = "History log of the subscription."
        model = models.SubscriptionEvent
        interfaces = [relay.Node]
        only_fields = ["id"]

    @staticmethod
    def resolve_user(root: models.SubscriptionEvent, info):
        user = info.context.user
        if (
            user == root.user
            or user.has_perm(AccountPermissions.MANAGE_USERS)
            or user.has_perm(AccountPermissions.MANAGE_STAFF)
        ):
            return root.user
        raise PermissionDenied()

    @staticmethod
    def resolve_email(root: models.SubscriptionEvent, _info):
        return root.parameters.get("email", None)

    @staticmethod
    def resolve_email_type(root: models.SubscriptionEvent, _info):
        return root.parameters.get("email_type", None)

    @staticmethod
    def resolve_quantity(root: models.SubscriptionEvent, _info):
        quantity = root.parameters.get("quantity", None)
        return int(quantity) if quantity else None

    @staticmethod
    def resolve_message(root: models.SubscriptionEvent, _info):
        return root.parameters.get("message", None)

    @staticmethod
    def resolve_subscription_number(root: models.SubscriptionEvent, _info):
        return root.subscription_id


class Subscription(MetadataObjectType, CountableDjangoObjectType):
    actions = graphene.List(
        SubscriptionAction,
        description=(
            "List of actions that can be performed in the current state of a subscription."
        ),
        required=True,
    )
    number = graphene.String(description="User-friendly number of a subscription.")
    status_display = graphene.String(description="User-friendly subscription status.")
    can_finalize = graphene.Boolean(
        description=(
            "Informs whether a draft subscription can be finalized"
            "(turned into a regular subscription)."
        ),
        required=True,
    )
    events = gql_optimizer.field(
        graphene.List(
            SubscriptionEvent, description="List of events associated with the subscription."
        ),
        model_field="events",
    )
    user_email = graphene.String(
        required=False, description="Email address of the customer."
    )


    class Meta:
        description = "Represents a subscription in the shop."
        interfaces = [relay.Node]
        model = models.Subscription
        only_fields = [
            "rrule_str",
            "start_date",
            "upcoming_order_creation_date",
            "upcoming_delivery_date",
            "created",
            "status",
            "user",
            "billing_address",
            "shipping_address",
            "token",
            "customer_note",
            "id",
            "ended_with_reason"
            "product_name",
            "variant_name",
            "quantity",
        ]


    @staticmethod
    def resolve_actions(root: models.Subscription, _info):
        actions = []
        rule = root.get_rrule_str()
        if root.can_capture(payment):
            actions.append(SubscriptionAction.CAPTURE)
        if root.can_mark_as_paid():
            actions.append(SubscriptionAction.MARK_AS_PAID)
        if root.can_refund(payment):
            actions.append(SubscriptionAction.REFUND)
        if root.can_void(payment):
            actions.append(SubscriptionAction.VOID)
        return actions

    @staticmethod
    @permission_required(SubscriptionPermissions.MANAGE_SUBSCRIPTIONS)
    def resolve_events(root: models.Subscription, _info):
        return root.events.all().order_by("pk")

    @staticmethod
    def resolve_number(root: models.Subscription, _info):
        return str(root.pk)

    @staticmethod
    def resolve_status_display(root: models.Subscription, _info):
        return root.get_status_display()

    @staticmethod
    @gql_optimizer.resolver_hints(select_related="user")
    def resolve_user_email(root: models.Subscription, _info):
        return root.get_customer_email()

    @staticmethod
    def resolve_user(root: models.Subscription, info):
        user = info.context.user
        if user == root.user or user.has_perm(AccountPermissions.MANAGE_USERS):
            return root.user
        raise PermissionDenied()

    @staticmethod
    @permission_required(SubscriptionPermissions.MANAGE_SUBSCRIPTIONS)
    def resolve_private_meta(root: models.Subscription, _info):
        return resolve_private_meta(root, _info)

    @staticmethod
    def resolve_meta(root: models.Subscription, _info):
        return resolve_meta(root, _info)
