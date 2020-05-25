from ...graphql.core.enums import to_enum
from ...subscription import SubscriptionEvents, SubscriptionEventsEmails

SubscriptionEventsEnum = to_enum(SubscriptionEvents)
SubscriptionEventsEmailsEnum = to_enum(SubscriptionEventsEmails)
