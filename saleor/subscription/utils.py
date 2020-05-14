from datetime import timedelta

from . import SubscriptionBusinessParameters


def get_next_order_creation_date(expected_delivery_date):
    delta = timedelta(days = SubscriptionBusinessParameters.TIMEDELTA_ORDER_CREATION_TO_EXPECTED_DELIVERY_IN_DAYS)
    return expected_delivery_date - delta


def is_user_trusted():
    return True