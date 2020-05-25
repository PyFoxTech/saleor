"""Subscription-related utility functions."""

from dateutil.rrule import rrulestr


def is_valid_rrule(rrule):
    try:
        rule_obj = rrulestr(rrule)
        return True
    except Exception as e:
        return False
