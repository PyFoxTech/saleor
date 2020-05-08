from graphene_federation import build_schema

from .account.schema import AccountMutations, AccountQueries
from .checkout.schema import CheckoutMutations, CheckoutQueries
from .core.schema import CoreMutations, CoreQueries
from .discount.schema import DiscountMutations, DiscountQueries
from .extensions.schema import ExtensionsMutations, ExtensionsQueries
from .giftcard.schema import GiftCardMutations, GiftCardQueries
from .menu.schema import MenuMutations, MenuQueries
from .meta.schema import MetaMutations
from .order.schema import OrderMutations, OrderQueries
from .page.schema import PageMutations, PageQueries
from .payment.schema import PaymentMutations, PaymentQueries
from .product.schema import ProductMutations, ProductQueries
from .shipping.schema import ShippingMutations, ShippingQueries
from .shop.schema import ShopMutations, ShopQueries
from .translations.schema import TranslationQueries
from .wallet.schema import WalletQueries, WalletMutations
from .warehouse.schema import (
    StockMutations,
    StockQueries,
    WarehouseMutations,
    WarehouseQueries,
)
from .webhook.schema import WebhookMutations, WebhookQueries
from .wishlist.schema import WishlistMutations


class Query(
    AccountQueries,
    CheckoutQueries,
    CoreQueries,
    DiscountQueries,
    ExtensionsQueries,
    GiftCardQueries,
    MenuQueries,
    OrderQueries,
    PageQueries,
    PaymentQueries,
    ProductQueries,
    ShippingQueries,
    ShopQueries,
    StockQueries,
    TranslationQueries,
    WalletQueries,
    WarehouseQueries,
    WebhookQueries,
):
    pass


class Mutation(
    AccountMutations,
    CheckoutMutations,
    CoreMutations,
    DiscountMutations,
    ExtensionsMutations,
    GiftCardMutations,
    MenuMutations,
    MetaMutations,
    OrderMutations,
    PageMutations,
    PaymentMutations,
    ProductMutations,
    ShippingMutations,
    ShopMutations,
    StockMutations,
    WarehouseMutations,
    WebhookMutations,
    WishlistMutations,
    WalletMutations,
):
    pass


schema = build_schema(Query, mutation=Mutation)
