from graphene_federation import build_schema

from .account.schema import AccountMutations, AccountQueries
from .app.schema import AppMutations, AppQueries
from .checkout.schema import CheckoutMutations, CheckoutQueries
from .core.schema import CoreMutations, CoreQueries
from .discount.schema import DiscountMutations, DiscountQueries
from .giftcard.schema import GiftCardMutations, GiftCardQueries
from .menu.schema import MenuMutations, MenuQueries
from .meta.schema import MetaMutations
from .order.schema import OrderMutations, OrderQueries
from .page.schema import PageMutations, PageQueries
from .payment.schema import PaymentMutations, PaymentQueries
from .plugins.schema import PluginsMutations, PluginsQueries
from .product.schema import ProductMutations, ProductQueries
from .shipping.schema import ShippingMutations, ShippingQueries
from .shop.schema import ShopMutations, ShopQueries
from .subscription.schema import SubscriptionMutations, SubscriptionQueries
from .translations.schema import TranslationQueries
from .wallet.schema import WalletQueries, WalletMutations
from .warehouse.schema import StockQueries, WarehouseMutations, WarehouseQueries
from .webhook.schema import WebhookMutations, WebhookQueries
from .wishlist.schema import WishlistMutations


class Query(
    AccountQueries,
    AppQueries,
    CheckoutQueries,
    CoreQueries,
    DiscountQueries,
    PluginsQueries,
    GiftCardQueries,
    MenuQueries,
    OrderQueries,
    PageQueries,
    PaymentQueries,
    ProductQueries,
    ShippingQueries,
    ShopQueries,
    StockQueries,
    SubscriptionQueries,
    TranslationQueries,
    WalletQueries,
    WarehouseQueries,
    WebhookQueries,
):
    pass


class Mutation(
    AccountMutations,
    AppMutations,
    CheckoutMutations,
    CoreMutations,
    DiscountMutations,
    PluginsMutations,
    GiftCardMutations,
    MenuMutations,
    MetaMutations,
    OrderMutations,
    PageMutations,
    PaymentMutations,
    ProductMutations,
    ShippingMutations,
    ShopMutations,
    SubscriptionMutations,
    WarehouseMutations,
    WebhookMutations,
    WishlistMutations,
    WalletMutations,
):
    pass


schema = build_schema(Query, mutation=Mutation)
