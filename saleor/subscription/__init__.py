class SubscriptionStatus:
    ACTIVE = "active" # orders will be automatically created as per the recurrence rule
    PAUSED = "paused" # orders will not tbe created
    ENDED = "ended" # permanently ended subscription

    CHOICES = [
        (ACTIVE, "Active"),
        (PAUSED, "Paused"),
        (ENDED, "Ended"),
    ]

class SubscriptionBusinessParameters:
    TIMEDELTA_ORDER_CREATION_TO_EXPECTED_DELIVERY_IN_DAYS = 2


class SubscriptionEvents:
    """The different subscription events."""

    ACTIVATED = "activated"

    RECURRENCE_RULE_UPDATED = "recurrence_rule_updated" 
    SHIPPING_ADDRESS_UPDATED = "shipping_address_updated"
    PRODUCT_QUANTITY_UPDATED = "product_quantity_updated"

    UPCOMING_ORDER_DRAFT_CREATED = "upcoming_order_draft_created"
    UPCOMING_ORDER_CONFIRMED = "upcoming_order_confirmed"
    LATEST_ORDER_DELIVERED = "upcoming_order_delivered"
    UPCOMING_ORDER_CANCELLED = "upcoming_order_cancelled"

    UPCOMING_DELIVERY_DATE_UPDATED = "upcoming_delivery_date_updated"
    UPCOMING_ORDER_CREATION_DATE_UPDATED = "upcoming_order_creation_date_updated"

    PAUSED = "paused"
    ENDED = "ended"

    EMAIL_SENT = "email_sent"

    NOTE_ADDED = "note_added"

    OTHER = "other"

    CHOICES = [
        (ACTIVATED, "The subscription was activated"),
        (RECURRENCE_RULE_UPDATED, "Recurrence rule for this subscription was updated"),
        (SHIPPING_ADDRESS_UPDATED, "Shipping address for this subscription was updated"),
        (PRODUCT_QUANTITY_UPDATED, "Product quantity for this subscription was updated"),
        (UPCOMING_ORDER_DRAFT_CREATED, "Draft of next order for this subscription was created"),
        (UPCOMING_ORDER_CONFIRMED, "Upcoming order for this subscription was confirmed"),
        (LATEST_ORDER_DELIVERED, "Latest order for this subscription was delivered"),
        (UPCOMING_ORDER_CANCELLED, "Upcoming order for this subscription was cancelled"),
        (PAUSED,"The subscription was paused"),
        (ENDED, "The subscription was ended"),
        (EMAIL_SENT, "The email was sent"),
        (NOTE_ADDED, "A note was added to the subscription"),
        (OTHER, "An unknown subscription event containing a message"),
    ]


class SubscriptionEventsEmails:
    """The different subscription emails event types."""

    RECHARGE_WALLET_TO_CONTIUNE_ORDER_CREATION = "recharge_wallet_to_contiune_order_creation"
    ORDER_CREATED = "order_creation"
    DIGITAL_LINKS = "digital_links"

    CHOICES = [
        (RECHARGE_WALLET_TO_CONTIUNE_ORDER_CREATION, "The wallet recharge request email was sent"),
        (ORDER_CREATED, "The order placement confirmation email was sent"),
        (DIGITAL_LINKS, "The email containing the digital links was sent"),
    ]
