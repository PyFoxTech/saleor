import graphene
from graphql_jwt.exceptions import PermissionDenied

from .enums import SubscriptionEventsEnum, SubscriptionEventsEmailsEnum
from ..account.types import User
from ..core.connection import CountableDjangoObjectType
from ..meta.types import ObjectWithMetadata
from ...core.permissions import AccountPermissions
from ...subscription import models


class Subscription(CountableDjangoObjectType):
    class Meta:
        only_fields = [
            "rrule",
            "start_date",
            "status",
            "created",
            "ended_with_reason",
            "customer_note",
            "quantity",
            "variant_name",
            "product_name",
            "variant",
            "shipping_address",
            "billing_address",
            "token",
        ]
        description = "Subscription object."
        model = models.Subscription
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
        filter_fields = ["token"]


class SubscriptionEvent(CountableDjangoObjectType):
    date = graphene.types.datetime.DateTime(
        description="Date when event happened at in ISO 8601 format."
    )
    type = SubscriptionEventsEnum(description="Order event type.")
    user = graphene.Field(User, description="User who performed the action.")
    message = graphene.String(description="Content of the event.")
    email_type = SubscriptionEventsEmailsEnum(
        description="Type of an email sent to the customer."
    )
    quantity = graphene.Int(description="Number of items.")
    subscription_number = graphene.String(
        description="User-friendly number of a subscription")

    class Meta:
        description = "SubscriptionEvent object."
        model = models.SubscriptionEvent
        interfaces = [graphene.relay.Node, ObjectWithMetadata]
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
    def resolve_email_type(root: models.SubscriptionEvent, _info):
        return root.parameters.get("email_type", None)

    @staticmethod
    def resolve_quantity(root: models.SubscriptionEvent, _info):
        quantity = root.parameters.get("quantity", None)
        return int(quantity) if quantity else None

    @staticmethod
    def resolve_message(root: models.SubscriptionEvent, _info):
        return root.parameters.get("message", None)
