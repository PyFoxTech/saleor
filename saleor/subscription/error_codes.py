from enum import Enum


class OrderErrorCode(Enum):
    INVALID_RECURRENCE_RULE = "recurrence rule is not valid"
    GRAPHQL_ERROR = "graphql_error"
