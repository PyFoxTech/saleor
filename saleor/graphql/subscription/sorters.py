import graphene
from django.db.models import FilteredRelation, Max, Q, QuerySet

from ..core.types import SortInputObjectType


class SubscriptionSortField(graphene.Enum):
    NUMBER = "pk"
    CREATION_DATE = "created"
    CUSTOMER = "customer"
    UPCOMING_ORDER_CREATION_DATE = "upcoming_order_creation_date",
    UPCOMING_DELIVERY_DATE = "upcoming_delivery_date",

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            SubscriptionSortField.NAME,
            SubscriptionSortField.CREATION_DATE,
            SubscriptionSortField.CUSTOMER,
            SubscriptionSortField.UPCOMING_ORDER_CREATION_DATE,
            SubscriptionSortField.UPCOMING_DELIVERY_DATE,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort subscriptions by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def sort_by_customer(queryset: QuerySet, sort_by: SortInputObjectType) -> QuerySet:
        return queryset.order_by(
            f"{sort_by.direction}billing_address__first_name",
            f"{sort_by.direction}billing_address__last_name",
        )


class SubscriptionSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = SubscriptionSortField
        type_name = "subscriptions"
