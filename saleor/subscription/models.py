from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timezone import now

from . import SubscriptionStatus, SubscriptionEvents
from ..account.models import Address
from ..core.models import ModelWithMetadata
from ..core.permissions import SubscriptionPermissions
from ..core.utils.json_serializer import CustomJsonEncoder


class SubscriptionQueryset(models.QuerySet):
    def confirmed(self):
        """Return non-draft subscriptions."""
        return self.exclude(status=SubscriptionStatus.DRAFT)

    def draft(self):
        """Return draft subscriptions. """
        return self.filter(status=SubscriptionStatus.DRAFT)

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
    rrule = models.TextField()
    start_date = models.DateTimeField()
    upcoming_order_creation_date = models.DateTimeField(null=True)
    upcoming_delivery_date = models.DateTimeField(null=True)
    created = models.DateTimeField(default=now, editable=False)
    status = models.CharField(
        max_length=32, default=SubscriptionStatus.DRAFT,
        choices=SubscriptionStatus.CHOICES
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=False,
        null=False,
        related_name="subscriptions",
        on_delete=models.PROTECT,
    )
    billing_address = models.ForeignKey(
        Address, related_name="+", editable=False, null=True, on_delete=models.SET_NULL
    )
    shipping_address = models.ForeignKey(
        Address, related_name="+", editable=False, null=True, on_delete=models.SET_NULL
    )
    token = models.CharField(max_length=36, unique=True, blank=True)
    customer_note = models.TextField(blank=True, default="")
    ended_with_reason = models.TextField(blank=True, default="")
    variant = models.ForeignKey(
        "product.ProductVariant",
        on_delete=models.PROTECT,
        blank=False,
        null=False,
    )
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    objects = SubscriptionQueryset.as_manager()

    class Meta:
        ordering = ("-pk",)
        permissions = ((SubscriptionPermissions.MANAGE_SUBSCRIPTIONS.codename,
                        "Manage subscriptions."),)

    def __repr__(self):
        return "<Subscription #%r>" % (self.id,)

    def __str__(self):
        return "#%d" % (self.id,)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid4())
        return super().save(*args, **kwargs)

    def end(self, *args, **kwargs):
        self.status = SubscriptionStatus.ENDED
        if 'ended_with_reason' in kwargs:
            self.ended_with_reason = kwargs["ended_with_reason"]


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
            (type_name.upper(), type_name) for type_name, _ in
            SubscriptionEvents.CHOICES
        ],
    )
    subscription = models.ForeignKey(Subscription, related_name="events",
                                     on_delete=models.PROTECT)
    parameters = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        related_name="+",
    )

    class Meta:
        ordering = ("date",)

    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.type!r}, user={self.user!r})"
