import graphene
from graphene.types import InputObjectType
from django.core.exceptions import ValidationError

from ....account.models import User
from ....core.permissions import SubscriptionPermissions
from ....subscription import events, models
from ....subscription.actions import (
    # subscription_shipping_updated,
    subscription_draft_created,
    subscription_activated,
    subscription_recurrence_rule_updated,
    subscription_product_quantity_updated,
    subscription_paused,
    end_subscription,
)
from ....subscription.error_codes import SubscriptionErrorCode
from ....subscription.utils import get_valid_shipping_methods_for_subscription
from ...account.types import AddressInput
from ...core.mutations import (
    BaseMutation,
    ClearMetaBaseMutation,
    UpdateMetaBaseMutation,
)
from ...core.scalars import Decimal
from ...core.types import MetaInput, MetaPath
from ...core.types.common import SubscriptionError
from ...subscription.types import Subscription, SubscriptionEvent
from ...shipping.types import ShippingMethod


class SubscriptionUpdateInput(InputObjectType):
    billing_address = AddressInput(description="Billing address of the customer.")
    user_email = graphene.String(description="Email address of the customer.")
    shipping_address = AddressInput(description="Shipping address of the customer.")
    rrule = graphene.String(description="Recurrence rule of the subscription")
    status = graphene.String(description="status of the subscription")



class SubscriptionUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an subscription to update.")
        input = SubscriptionUpdateInput(
            required=True, description="Fields required to update a subscription."
        )

    class Meta:
        description = "Updates a subscription."
        model = models.Subscription
        permissions = (SubscriptionPermissions.MANAGE_SUBSCRIPTIONS,)
        error_type_class = SubscriptionError
        error_type_field = "subscription_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        subscription_cleaned_input = super().clean_input(info, instance, data)

        editable_fields = ["billing_address", "shipping_address", "user_email", "rrule", "status"]
        cleaned_input = {}
        for key in subscription_cleaned_input:
            if key in editable_fields:
                cleaned_input[key] = subscription_cleaned_input[key]
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super().save(info, instance, cleaned_input)
        if instance.user_email:
            user = User.objects.filter(email=instance.user_email).first()
            instance.user = user
        instance.save()


class SubscriptionAddNoteInput(graphene.InputObjectType):
    message = graphene.String(description="Note message.", name="message")


class SubscriptionAddNote(BaseMutation):
    subscription = graphene.Field(Subscription, description="Subscription with the note added.")
    event = graphene.Field(SubscriptionEvent, description="Subscription note created.")

    class Arguments:
        id = graphene.ID(
            required=True,
            description="ID of the subscription to add a note for.",
            name="subscription",
        )
        input = SubscriptionAddNoteInput(
            required=True, description="Fields required to create a note for the subscription."
        )

    class Meta:
        description = "Adds note to the subscription."
        permissions = (SubscriptionPermissions.MANAGE_SUBSCRIPTIONS,)
        error_type_class = SubscriptionError
        error_type_field = "subscription_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        subscription = cls.get_node_or_error(info, data.get("id"), only_type=Subscription)
        event = events.subscription_note_added_event(
            subscription=subscription, user=info.context.user, message=data.get("input")["message"]
        )
        return SubscriptionAddNote(subscription=subscription, event=event)


class SubscriptionUpdateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Updates meta for subscription."
        model = models.Subscription
        public = True

    class Arguments:
        token = graphene.UUID(
            description="Token of an object to update.", required=True
        )
        input = MetaInput(
            description="Fields required to update new or stored metadata item.",
            required=True,
        )

    @classmethod
    def get_instance(cls, info, **data):
        token = data["token"]
        return models.Subscription.objects.get(token=token)


class SubscriptionUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Updates private meta for subscription."
        model = models.Subscription
        permissions = (SubscriptionPermissions.MANAGE_SUBSCRIPTIONS,)
        public = False


class SubscriptionClearMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears stored metadata value."
        model = models.Subscription
        permissions = (SubscriptionPermissions.MANAGE_SUBSCRIPTIONS,)
        public = True

    class Arguments:
        token = graphene.UUID(description="Token of an object to clear.", required=True)
        input = MetaPath(
            description="Fields required to update new or stored metadata item.",
            required=True,
        )

    @classmethod
    def get_instance(cls, info, **data):
        token = data["token"]
        return models.Subscription.objects.get(token=token)


class SubscriptionClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears stored private metadata value."
        model = models.Subscription
        permissions = (SubscriptionPermissions.MANAGE_SUBSCRIPTIONS,)
        public = False
