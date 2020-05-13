from decimal import Decimal
from typing import Optional
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timezone import now
from django_prices.models import MoneyField, TaxedMoneyField

from ..account.models import Address
from ..core.models import ModelWithMetadata
from ..core.permissions import SubscriptionPermissions
from ..core.utils.json_serializer import CustomJsonEncoder
from .utils import get_order_creation_date_from_expected_delivery_date
from . import SubscriptionStatus, SubscriptionEvents


class SubscriptionQueryset(models.QuerySet):
    def active(self):
        """ Return active subscriptions."""
        return self.filter(status=SubscriptionStatus.ACTIVE)
    def paused(self):
        """ Return active subscriptions."""
        return self.filter(status=SubscriptionStatus.PAUSED)
    def ended(self):
        """ Return active subscriptions."""
        return self.filter(status=SubscriptionStatus.ENDED)



class Subscription(ModelWithMetadata):
    rrule_str = models.TextField()
    start_date = models.DateTimeField()
    upcoming_order_creation_date = models.DateTimeField()
    upcoming_delivery_date = models.DateTimeField()
    created = models.DateTimeField(default=now, editable=False)
    status = models.CharField(
        max_length=32, default=SubscriptionStatus.ACTIVE, choices=SubscriptionStatus.CHOICES
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="subscriptions",
        on_delete=models.SET_NULL,
    )
    billing_address = models.ForeignKey(
        Address, related_name="+", editable=False, null=True, on_delete=models.SET_NULL
    )
    shipping_address = models.ForeignKey(
        Address, related_name="+", editable=False, null=True, on_delete=models.SET_NULL
    )
    user_email = models.EmailField(blank=True, default="")
    token = models.CharField(max_length=36, unique=True, blank=True)
    customer_note = models.TextField(blank=True, default="")
    ended_with_reason = models.TextField(blank=True, default="")
    variant = models.ForeignKey(
        "product.ProductVariant",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    # max_length is as produced by ProductVariant's display_product method
    product_name = models.CharField(max_length=386)
    variant_name = models.CharField(max_length=255, default="", blank=True)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])

    objects = SubscriptionQueryset.as_manager()

    class Meta:
        ordering = ("-pk",)
        permissions = ((SubscriptionPermissions.MANAGE_SUBSCRIPTIONS.codename, "Manage subscriptions."),)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid4())
        return super().save(*args, **kwargs)

    def __iter__(self):
        return iter(self.lines.all())

    def __repr__(self):
        return "<Subscription #%r>" % (self.id,)

    def __str__(self):
        return "#%d" % (self.id,)

    def get_rrule_str(self):
        return self.rrule_str

    def get_customer_email(self):
        return self.user.email if self.user else self.user_email

    def _index_billing_phone(self):
        return self.billing_address.phone

    def _index_shipping_phone(self):
        return self.shipping_address.phone

    def get_upcoming_delivery_date(self):
        return self.upcoming_delivery_date

    def get_upcoming_order_creation_date(self):
        return self.upcoming_order_creation_date


class SubscriptionEvent(models.Model):
    """Model used to store events that happened during the subscription lifecycle.

    Args:
        parameters: Values needed to display the event on the storefront
        type: Type of a subscription

    """

    date = models.DateTimeField(default=now, editable=False)
    type = models.CharField(
        max_length=255,
        choices=[
            (type_name.upper(), type_name) for type_name, _ in SubscriptionEvents.CHOICES
        ],
    )
    subscription = models.ForeignKey(Subscription, related_name="events", on_delete=models.CASCADE)
    parameters = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ("date",)

    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.type!r}, user={self.user!r})"
