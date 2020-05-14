import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....core.permissions import SubscriptionPermissions
from ....core.taxes import zero_taxed_money
from ....subscription import events, models
from ....subscription.actions import (
    cancel_subscription,
        subscription_shipping_updated,
    subscription_voided,
)
from ....subscription.error_codes import SubscriptionErrorCode
from ....subscription.utils import get_valid_shipping_methods_for_subscription
from ....payment import CustomPaymentChoices, PaymentError, gateway
from ...account.types import AddressInput
from ...core.mutations import (
    BaseMutation,
    ClearMetaBaseMutation,
    UpdateMetaBaseMutation,
)
from ...core.scalars import Decimal
from ...core.types import MetaInput, MetaPath
from ...core.types.common import SubscriptionError
from ...subscription.mutations.draft_subscriptions import DraftSubscriptionUpdate
from ...subscription.types import Subscription, SubscriptionEvent
from ...shipping.types import ShippingMethod


def clean_subscription_update_shipping(subscription, method):
    if not subscription.shipping_address:
        raise ValidationError(
            {
                "subscription": ValidationError(
                    "Cannot choose a shipping method for an subscription without "
                    "the shipping address.",
                    code=SubscriptionErrorCode.SUBSCRIPTION_NO_SHIPPING_ADDRESS,
                )
            }
        )

    valid_methods = get_valid_shipping_methods_for_subscription(subscription)
    if valid_methods is None or method.pk not in valid_methods.values_list(
        "id", flat=True
    ):
        raise ValidationError(
            {
                "shipping_method": ValidationError(
                    "Shipping method cannot be used with this subscription.",
                    code=SubscriptionErrorCode.SHIPPING_METHOD_NOT_APPLICABLE,
                )
            }
        )


def clean_subscription_cancel(subscription):
    if subscription and not subscription.can_cancel():
        raise ValidationError(
            {
                "subscription": ValidationError(
                    "This subscription can't be canceled.",
                    code=SubscriptionErrorCode.CANNOT_CANCEL_SUBSCRIPTION,
                )
            }
        )


class SubscriptionUpdateInput(graphene.InputObjectType):
    billing_address = AddressInput(description="Billing address of the customer.")
    user_email = graphene.String(description="Email address of the customer.")
    shipping_address = AddressInput(description="Shipping address of the customer.")


class SubscriptionUpdate(DraftSubscriptionUpdate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an subscription to update.")
        input = SubscriptionUpdateInput(
            required=True, description="Fields required to update an subscription."
        )

    class Meta:
        description = "Updates an subscription."
        model = models.Subscription
        permissions = (SubscriptionPermissions.MANAGE_SUBSCRIPTIONS,)
        error_type_class = SubscriptionError
        error_type_field = "subscription_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        draft_subscription_cleaned_input = super().clean_input(info, instance, data)

        # We must to filter out field added by DraftSubscriptionUpdate
        editable_fields = ["billing_address", "shipping_address", "user_email"]
        cleaned_input = {}
        for key in draft_subscription_cleaned_input:
            if key in editable_fields:
                cleaned_input[key] = draft_subscription_cleaned_input[key]
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super().save(info, instance, cleaned_input)
        if instance.user_email:
            user = User.objects.filter(email=instance.user_email).first()
            instance.user = user
        instance.save()


class SubscriptionUpdateShippingInput(graphene.InputObjectType):
    shipping_method = graphene.ID(
        description="ID of the selected shipping method.", name="shippingMethod"
    )


class SubscriptionUpdateShipping(BaseMutation):
    subscription = graphene.Field(Subscription, description="Subscription with updated shipping method.")

    class Arguments:
        id = graphene.ID(
            required=True,
            name="subscription",
            description="ID of the subscription to update a shipping method.",
        )
        input = SubscriptionUpdateShippingInput(
            description="Fields required to change shipping method of the subscription."
        )

    class Meta:
        description = "Updates a shipping method of the subscription."
        permissions = (SubscriptionPermissions.MANAGE_SUBSCRIPTIONS,)
        error_type_class = SubscriptionError
        error_type_field = "subscription_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        subscription = cls.get_node_or_error(info, data.get("id"), only_type=Subscription)
        data = data.get("input")

        if not data["shipping_method"]:
            if not subscription.is_draft() and subscription.is_shipping_required():
                raise ValidationError(
                    {
                        "shipping_method": ValidationError(
                            "Shipping method is required for this subscription.",
                            code=SubscriptionErrorCode.SHIPPING_METHOD_REQUIRED,
                        )
                    }
                )

            subscription.shipping_method = None
            subscription.shipping_price = zero_taxed_money()
            subscription.shipping_method_name = None
            subscription.save(
                update_fields=[
                    "currency",
                    "shipping_method",
                    "shipping_price_net_amount",
                    "shipping_price_gross_amount",
                    "shipping_method_name",
                ]
            )
            return SubscriptionUpdateShipping(subscription=subscription)

        method = cls.get_node_or_error(
            info,
            data["shipping_method"],
            field="shipping_method",
            only_type=ShippingMethod,
        )

        clean_subscription_update_shipping(subscription, method)

        subscription.shipping_method = method
        subscription.shipping_price = info.context.extensions.calculate_subscription_shipping(subscription)
        subscription.shipping_method_name = method.name
        subscription.save(
            update_fields=[
                "currency",
                "shipping_method",
                "shipping_method_name",
                "shipping_price_net_amount",
                "shipping_price_gross_amount",
            ]
        )
        # Post-process the results
        subscription_shipping_updated(subscription)
        return SubscriptionUpdateShipping(subscription=subscription)


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


class SubscriptionCancel(BaseMutation):
    subscription = graphene.Field(Subscription, description="Canceled subscription.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the subscription to cancel.")
        restock = graphene.Boolean(
            required=True, description="Determine if lines will be restocked or not."
        )

    class Meta:
        description = "Cancel an subscription."
        permissions = (SubscriptionPermissions.MANAGE_SUBSCRIPTIONS,)
        error_type_class = SubscriptionError
        error_type_field = "subscription_errors"

    @classmethod
    def perform_mutation(cls, _root, info, restock, **data):
        subscription = cls.get_node_or_error(info, data.get("id"), only_type=Subscription)
        clean_subscription_cancel(subscription)
        cancel_subscription(subscription=subscription, user=info.context.user, restock=restock)
        return SubscriptionCancel(subscription=subscription)


class SubscriptionVoid(BaseMutation):
    subscription = graphene.Field(Subscription, description="A voided subscription.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the subscription to void.")

    class Meta:
        description = "Void an subscription."
        permissions = (SubscriptionPermissions.MANAGE_SUBSCRIPTIONS,)
        error_type_class = SubscriptionError
        error_type_field = "subscription_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        subscription = cls.get_node_or_error(info, data.get("id"), only_type=Subscription)
        payment = subscription.get_last_payment()
        clean_void_payment(payment)

        try_payment_action(subscription, info.context.user, payment, gateway.void, payment)
        subscription_voided(subscription, info.context.user, payment)
        return SubscriptionVoid(subscription=subscription)


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
