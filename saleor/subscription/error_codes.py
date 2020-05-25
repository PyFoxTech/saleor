from enum import Enum


class SubscriptionErrorCode(Enum):
    INVALID_RECURRENCE_RULE = "recurrence_rule_is_not_valid"
    GRAPHQL_ERROR = "graphql_error"
    START_DATE_NOT_SET = "start_date_not_set"
    BILLING_ADDRESS_NOT_SET = "billing_address_not_set"
    SHIPPING_ADDRESS_NOT_SET = "shipping_address_not_set"
    CANNOT_DELETE = "cannot_delete"
    NOT_EDITABLE = "not_editable"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    ZERO_QUANTITY = "zero_quantity"
