class SubscriptionStatus:
    DRAFT = "draft"  # All the details needed to create subscription havent been filled
    ACTIVE = "active"  # orders will be automatically created as per the recurrence rule
    PAUSED = "paused"  # orders will not tbe created
    ENDED = "ended"  # permanently ended subscription

    CHOICES = [
        (DRAFT, "Draft"),
        (ACTIVE, "Active"),
        (PAUSED, "Paused"),
        (ENDED, "Ended"),
    ]


class SubscriptionBusinessParameters:
    TIMEDELTA_ORDER_CREATION_TO_EXPECTED_DELIVERY_IN_DAYS = 2


class SubscriptionEvents:
    """The different subscription events."""
    DRAFT_CREATED = "draft_created"
    ACTIVATED = "activated"

    RECURRENCE_RULE_UPDATED = "recurrence_rule_updated"
    START_DATE_UPDATED = "start_date_updated"
    SHIPPING_ADDRESS_UPDATED = "shipping_address_updated"
    PRODUCT_QUANTITY_UPDATED = "product_quantity_updated"

    PAUSED = "paused"
    ENDED = "ended"

    NOTIFICATION_SENT = "notification_sent"

    NOTE_ADDED = "note_added"

    OTHER = "other"

    CHOICES = [
        (DRAFT_CREATED, "The draft of a subscription was created"),
        (ACTIVATED, "The subscription was activated"),
        (RECURRENCE_RULE_UPDATED, "Recurrence rule for this subscription was updated"),
        (START_DATE_UPDATED, "Start Date of the subscription was updated."),
        (
        SHIPPING_ADDRESS_UPDATED, "Shipping address for this subscription was updated"),
        (
        PRODUCT_QUANTITY_UPDATED, "Product quantity for this subscription was updated"),
        (PAUSED, "The subscription was paused"),
        (ENDED, "The subscription was ended"),
        (NOTIFICATION_SENT, "The notification was sent"),
        (NOTE_ADDED, "A note was added to the subscription"),
        (OTHER, "An unknown subscription event containing a message"),
    ]


class SubscriptionEventsEmails:
    """The different subscription emails event types."""

    LOW_BALANCE_ALERT = "low_balance_alert"
    ORDER_CREATED = "order_creation"

    CHOICES = [
        (LOW_BALANCE_ALERT, "The recharge request notification was sent"),
        (ORDER_CREATED, "The order placement confirmation email was sent"),
    ]
