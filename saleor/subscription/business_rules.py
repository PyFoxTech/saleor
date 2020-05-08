from datetime import timedelta


def get_order_creation_date_from_expected_delivery_date(expected_delivery_date):
    delta = timedelta(days = 2)
    return expected_delivery_date - delta


def is_user_trusted():
    return True