import graphene
from django.core.exceptions import ValidationError
from graphql_jwt.exceptions import PermissionDenied

from .types import Subscription
from ..account.i18n import I18nMixin
from ..account.types import AddressInput
from ..core.mutations import ModelMutation
from ..core.types.common import SubscriptionError
from ..product.types import ProductVariant
from ...core.permissions import SubscriptionPermissions
from ...subscription import SubscriptionStatus
from ...subscription import models
from ...subscription.error_codes import SubscriptionErrorCode
from ...subscription.utils import is_valid_rrule


class SubscriptionCreateInput(graphene.InputObjectType):
    rrule = graphene.String(
        description="The recurrence rule of the subscription.",
        required=True)
    start_date = graphene.Date(
        description="Start date of the subscription",
        required=True)
    variant_id = graphene.ID(
        description="Product variant ID.", name="variantId", required=True
    )
    quantity = graphene.Int(description="Number of variant items subscribed.")
    shipping_address = AddressInput(
        description=(
            "The mailing address to where the subscription orders will be shipped. "
        )
    )
    billing_address = AddressInput(description="Billing address of the customer.")
    customer_note = graphene.String(
        description="A note from a customer. Visible by customers in the summary."
    )


class SubscriptionCreate(ModelMutation, I18nMixin):
    class Arguments:
        input = SubscriptionCreateInput(
            required=True, description="Fields required to create subscription."
        )

    class Meta:
        description = "Create a new subscription"
        model = models.Subscription
        exclude = ["upcoming_order_creation_date", "upcoming_delivery_date"]
        return_field_name = "subscription"
        error_type_class = SubscriptionError
        error_type_field = "subscription_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        user = cleaned_input.get("user")

        shipping_address = data.pop("shipping_address", None)
        billing_address = data.pop("billing_address", None)

        # Set up default addresses if possible
        if user and not shipping_address:
            cleaned_input["shipping_address"] = user.default_shipping_address
        if user and not billing_address:
            cleaned_input["billing_address"] = user.default_billing_address
        if shipping_address:
            shipping_address = cls.validate_address(
                shipping_address, instance=instance.shipping_address, info=info
            )
            shipping_address = info.context.plugins.change_user_address(
                shipping_address, "shipping", user=instance
            )
            cleaned_input["shipping_address"] = shipping_address
        if billing_address:
            billing_address = cls.validate_address(
                billing_address, instance=instance.billing_address, info=info
            )
            billing_address = info.context.plugins.change_user_address(
                billing_address, "billing", user=instance
            )
            cleaned_input["billing_address"] = billing_address

        rrule = data.pop("rrule", None)
        if rrule and is_valid_rrule(rrule):
            cleaned_input["rrule"] = rrule
        else:
            raise ValidationError(
                {
                    "message": ValidationError(
                        "Invalid Recurrence Rule",
                        code=SubscriptionErrorCode.INVALID_RECURRENCE_RULE,
                    )
                }
            )
        cleaned_input["start_date"] = data.get("start_date")
        cleaned_input["variant"] = cls.get_node_or_error(
            info,
            data.get("variant_id"),
            only_type=ProductVariant
        )
        cleaned_input["quantity"] = data.pop("quantity", None)
        cleaned_input["status"] = SubscriptionStatus.ACTIVE
        return cleaned_input

    @staticmethod
    def _save_addresses(info, instance: models.Subscription, cleaned_input):
        # Create the draft creation event
        shipping_address = cleaned_input.get("shipping_address")
        if shipping_address:
            shipping_address.save()
            instance.shipping_address = shipping_address.get_copy()
        billing_address = cleaned_input.get("billing_address")
        if billing_address:
            billing_address.save()
            instance.billing_address = billing_address.get_copy()

    @classmethod
    def _commit_changes(cls, info, instance, cleaned_input):
        created = instance.pk
        super().save(info, instance, cleaned_input)
        instance.save(update_fields=["billing_address", "shipping_address"])

    @classmethod
    def save(cls, info, instance, cleaned_input):
        # Process addresses
        cls._save_addresses(info, instance, cleaned_input)

        # Save any changes create/update the draft
        cls._commit_changes(info, instance, cleaned_input)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        user = info.context.user
        if not user.is_authenticated:
            raise PermissionDenied()
        subscription = models.Subscription(user=user)
        cleaned_input = cls.clean_input(info, subscription, data.get("input"))
        subscription = cls.construct_instance(subscription, cleaned_input)
        cls.clean_instance(info, subscription)
        cls.save(info, subscription, cleaned_input)
        cls._save_m2m(info, subscription, cleaned_input)
        return SubscriptionCreate(subscription=subscription)


class SubscriptionUpdateInput(graphene.InputObjectType):
    rrule = graphene.String(
        description="The recurrence rule of the subscription.")
    start_date = graphene.Date(
        description="Start date of the subscription")
    quantity = graphene.Int(description="Number of variant items subscribed.")
    shipping_address = AddressInput(
        description=(
            "The mailing address to where the subscription orders will be shipped. "
        )
    )
    customer_note = graphene.String(
        description="A note from a customer. Visible by customers in the summary."
    )
    status = graphene.String(
        description="Status of the subscription"
    )


class SubscriptionUpdate(ModelMutation, I18nMixin):
    subscription = graphene.Field(Subscription, description="An updated subscription.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a subscription to update.")
        input = SubscriptionUpdateInput(
            description="Fields required to update an subscription."
        )

    class Meta:
        description = "Updates a subscription."
        model = models.Subscription
        exclude = ["upcoming_order_creation_date", "upcoming_delivery_date"]
        return_field_name = "subscription"
        error_type_class = SubscriptionError
        error_type_field = "subscription_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        shipping_address = data.pop("shipping_address", None)
        if shipping_address:
            shipping_address = cls.validate_address(
                shipping_address, instance=instance.shipping_address, info=info
            )
            shipping_address = info.context.plugins.change_user_address(
                shipping_address, "shipping", user=instance
            )
            cleaned_input["shipping_address"] = shipping_address
        rrule = data.pop("rrule", None)
        if rrule and is_valid_rrule(rrule):
            cleaned_input["rrule"] = rrule
        status = data.pop("status", None)
        if status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.PAUSED,
        ]:
            cleaned_input["status"] = status
        return cleaned_input

    @staticmethod
    def _save_addresses(info, instance: models.Subscription, cleaned_input):
        shipping_address = cleaned_input.get("shipping_address")
        if shipping_address:
            shipping_address.save()
            instance.shipping_address = shipping_address.get_copy()

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        user = info.context.user
        if not user.is_authenticated:
            raise PermissionDenied()
        subscription = cls.get_instance(info, **data)
        if subscription.status == SubscriptionStatus.ENDED:
            raise PermissionDenied()
        cleaned_input = cls.clean_input(info, subscription, data.get("input"))
        subscription = cls.construct_instance(subscription, cleaned_input)
        cls.save(info, subscription, cleaned_input)
        return cls.success_response(subscription)


class SubscriptionEndInput(graphene.InputObjectType):
    ended_with_reason = graphene.String(
        description="Reason given by customer to end subscription"
    )


class SubscriptionEnd(ModelMutation, I18nMixin):
    subscription = graphene.Field(Subscription, description="An ended subscription.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a subscription to end.")
        input = SubscriptionEndInput(description="Fields to end a subscription.")

    class Meta:
        description = "Ends a subscription."
        model = models.Subscription
        exclude = ["upcoming_order_creation_date", "upcoming_delivery_date"]
        permissions = (SubscriptionPermissions.MANAGE_SUBSCRIPTIONS,)
        error_type_class = SubscriptionError
        error_type_field = "subscription_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        user = info.context.user
        if not user.is_authenticated:
            raise PermissionDenied()
        subscription = cls.get_instance(info, **data)
        cleaned_input = cls.clean_input(info, subscription, data.get("input"))
        if "ended_with_reason" in cleaned_input:
            subscription.end(ended_with_reason=cleaned_input["ended_with_reason"])
        else:
            subscription.end()
        subscription.save()
        return cls.success_response(subscription)
