from enum import Enum


class SubscriptionErrorCode(Enum):
    INVALID_RECURRENCE_RULE = "recurrence rule is not valid"
    GRAPHQL_ERROR = "graphql_error"
    BILLING_ADDRESS_NOT_SET = "billing_address_not_set"
    SHIPPING_ADDRESS_NOT_SET = "shipping_address_not_set"
    CANNOT_DELETE = "cannot_delete"
    NOT_EDITABLE = "not_editable"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    ZERO_QUANTITY = "zero_quantity"
