import graphene

from ...graphql.core.enums import to_enum
from ...subscription import (
    SubscriptionEvents, 
    SubscriptionEventsEmails,
    SubscriptionStatus
    )

SubscriptionStatusEnum = to_enum(SubscriptionStatus)
SubscriptionEventsEnum = to_enum(SubscriptionEvents)
SubscriptionEventsEmailsEnum = to_enum(SubscriptionEventsEmails)


class SubscriptionStatusFilter(graphene.Enum):
    ACTIVATED = "activated"
    PAUSED = "paused"
    ENDED = "ended"
