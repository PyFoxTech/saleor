import graphene

from ...core.permissions import SubscriptionPermissions
from ..core.enums import ReportingPeriod
from ..core.fields import FilterInputConnectionField, PrefetchingConnectionField
from ..core.types import FilterInputObjectType, TaxedMoney
from ..decorators import permission_required
from .enums import SubscriptionStatusFilter
from .filters import DraftOrderFilter, OrderFilter
from .mutations.draft_orders import (
    DraftOrderComplete,
    DraftOrderCreate,
    DraftOrderDelete,
    DraftOrderUpdate,
)
from .mutations.orders import (
    OrderAddNote,
    OrderCancel,
    OrderCapture,
    OrderClearMeta,
    OrderClearPrivateMeta,
    OrderMarkAsPaid,
    OrderRefund,
    OrderUpdate,
    OrderUpdateMeta,
    OrderUpdatePrivateMeta,
    OrderUpdateShipping,
    OrderVoid,
)
from .resolvers import (
    resolve_draft_orders,
    resolve_homepage_events,
    resolve_order,
    resolve_order_by_token,
    resolve_orders,
    resolve_orders_total,
)
from .sorters import OrderSortingInput
from .types import Order, OrderEvent


class OrderFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = OrderFilter


class OrderDraftFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = DraftOrderFilter


class OrderQueries(graphene.ObjectType):
    homepage_events = PrefetchingConnectionField(
        OrderEvent,
        description=(
            "List of activity events to display on "
            "homepage (at the moment it only contains order-events)."
        ),
    )
    order = graphene.Field(
        Order,
        description="Look up an order by ID.",
        id=graphene.Argument(graphene.ID, description="ID of an order.", required=True),
    )
    orders = FilterInputConnectionField(
        Order,
        sort_by=OrderSortingInput(description="Sort orders."),
        filter=OrderFilterInput(description="Filtering options for orders."),
        created=graphene.Argument(
            ReportingPeriod,
            description=(
                "Filter orders from a selected timespan. "
                "DEPRECATED: Will be removed in Saleor 2.11, "
                "use the `filter` field instead."
            ),
        ),
        status=graphene.Argument(
            OrderStatusFilter,
            description=(
                "Filter order by status. "
                "DEPRECATED: Will be removed in Saleor 2.11, "
                "use the `filter` field instead."
            ),
        ),
        description="List of orders.",
    )
    draft_orders = FilterInputConnectionField(
        Order,
        sort_by=OrderSortingInput(description="Sort draft orders."),
        filter=OrderDraftFilterInput(description="Filtering options for draft orders."),
        created=graphene.Argument(
            ReportingPeriod,
            description=(
                "Filter draft orders from a selected timespan. "
                "DEPRECATED: Will be removed in Saleor 2.11, "
                "use the `filter` field instead."
            ),
        ),
        description="List of draft orders.",
    )
    orders_total = graphene.Field(
        TaxedMoney,
        description="Return the total sales amount from a specific period.",
        period=graphene.Argument(ReportingPeriod, description="A period of time."),
    )
    order_by_token = graphene.Field(
        Order,
        description="Look up an order by token.",
        token=graphene.Argument(
            graphene.UUID, description="The order's token.", required=True
        ),
    )

    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_homepage_events(self, *_args, **_kwargs):
        return resolve_homepage_events()

    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_order(self, info, **data):
        return resolve_order(info, data.get("id"))

    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_orders(
        self, info, created=None, status=None, query=None, sort_by=None, **_kwargs
    ):
        return resolve_orders(info, created, status, query, sort_by)

    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_draft_orders(
        self, info, created=None, query=None, sort_by=None, **_kwargs
    ):
        return resolve_draft_orders(info, created, query, sort_by)

    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_orders_total(self, info, period, **_kwargs):
        return resolve_orders_total(info, period)

    def resolve_order_by_token(self, _info, token):
        return resolve_order_by_token(token)


class OrderMutations(graphene.ObjectType):
    draft_order_complete = DraftOrderComplete.Field()
    draft_order_create = DraftOrderCreate.Field()
    draft_order_delete = DraftOrderDelete.Field()
    draft_order_update = DraftOrderUpdate.Field()

    order_add_note = OrderAddNote.Field()
    order_cancel = OrderCancel.Field()
    order_capture = OrderCapture.Field()
    order_clear_private_meta = OrderClearPrivateMeta.Field()
    order_clear_meta = OrderClearMeta.Field()
    order_mark_as_paid = OrderMarkAsPaid.Field()
    order_refund = OrderRefund.Field()
    order_update = OrderUpdate.Field()
    order_update_meta = OrderUpdateMeta.Field()
    order_update_private_meta = OrderUpdatePrivateMeta.Field()
    order_update_shipping = OrderUpdateShipping.Field()
    order_void = OrderVoid.Field()

