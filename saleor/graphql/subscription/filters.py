import django_filters
from django.db.models import Sum

from ...subscription.models import Subscription
from ..core.filters import ListObjectTypeFilter, ObjectTypeFilter
from ..core.types.common import DateRangeInput
from ..utils import filter_by_query_param
from .enums import SubscriptionStatusFilter, SubscriptionStatusEnum


def filter_status(qs, _, value):
    if value.lower() in SubscriptionStatusEnum:
        return qs.filter(status__iexact=value)

def filter_customer(qs, _, value):
    customer_fields = [
        "user_email",
        "user__first_name",
        "user__last_name",
        "user__email",
    ]
    qs = filter_by_query_param(qs, value, customer_fields)
    return qs


def filter_created_range(qs, _, value):
    gte, lte = value.get("gte"), value.get("lte")
    if gte:
        qs = qs.filter(created__date__gte=gte)
    if lte:
        qs = qs.filter(created__date__lte=lte)
    return qs

def filter_start_date_range(qs, _, value):
    gte, lte = value.get("gte"), value.get("lte")
    if gte:
        qs = qs.filter(start_date__date__gte=gte)
    if lte:
        qs = qs.filter(start_date__date__lte=lte)
    return qs


def filter_order_search(qs, _, value):
    order_fields = [
        "pk",
        "user_email",
        "user__first_name",
        "user__last_name",
        "product_name",
        "variant_name",
    ]
    qs = filter_by_query_param(qs, value, order_fields)
    return qs


class DraftSubscriptionFilter(django_filters.FilterSet):
    customer = django_filters.CharFilter(method=filter_customer)
    created = ObjectTypeFilter(input_class=DateRangeInput, method=filter_created_range)
    search = django_filters.CharFilter(method=filter_order_search)

    class Meta:
        model = Subscription
        fields = ["customer", "created", "search"]


class SubscriptionFilter(DraftSubscriptionFilter):
    status = ListObjectTypeFilter(input_class=SubscriptionStatusFilter, method=filter_status)
    customer = django_filters.CharFilter(method=filter_customer)
    created = ObjectTypeFilter(input_class=DateRangeInput, method=filter_created_range)
    start_date = ObjectTypeFilter(input_class=DateRangeInput, method=filter_start_date_range)
    search = django_filters.CharFilter(method=filter_order_search)

    class Meta:
        model = Subscription
        fields = ["payment_status", "status", "customer", "created", "search"]
