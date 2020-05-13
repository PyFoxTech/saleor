from datetime import datetime

from dateutil.rrule import rrule, rrulestr

from .utils import (
    get_order_creation_date_from_expected_delivery_date,
    is_user_trusted
    )


class Subscription:  

    def __init__(self, rule, sub_start_date):  
        self.next_expected_delivery_date = get_next_recurrence(rule)
        self.next_order_creation_date = get_order_creation_date_from_expected_delivery_date(sub_start_date)
        self.rule = rule
        self.dtstart = sub_start_date

def get_next_recurrence(rule):
    rule_obj = rrulestr(rule)
    return rule_obj.after(datetime.now())

def is_rule_valid(rule):
#     rule_obj = rrulestr("FREQ=DAILY;INTERVAL=10;COUNT=5")
    try:
        rrule_obj = rrulestr(rule)
        return True
    except Exception as e:
        pass
    else:
        return False


