import graphene

from .mutations import WalletRechargeCreate, WalletRechargePaymentCreate, \
    WalletRechargeComplete
from .resolvers import resolve_wallets, resolve_wallet, resolve_wallet_recharge
from .types import Wallet, WalletRecharge
from ..checkout.types import PaymentGateway
from ..core.fields import PrefetchingConnectionField
from ...plugins.manager import get_plugins_manager


class WalletQueries(graphene.ObjectType):
    wallet = graphene.Field(
        Wallet,
        description="Look up an wallet by ID.",
        id=graphene.Argument(graphene.ID, description="ID of an wallet.",
                             required=True),
    )
    wallets = PrefetchingConnectionField(
        Wallet,
        description="List of wallets of authenticated user",
    )

    wallet_recharge = graphene.Field(
        WalletRecharge,
        description="Look up an wallet recharge by ID.",
        id=graphene.Argument(graphene.ID, description="ID of an wallet recharge.",
                             required=True),
    )

    wallet_recharge_available_payment_gateways = graphene.List(
        PaymentGateway,
        description="List of available payment gateways.",
        required=True
    )

    def resolve_wallet(self, info, **data):
        return resolve_wallet(info, data.get("id"))

    def resolve_wallets(self, info, **_kwargs):
        return resolve_wallets(info)

    def resolve_wallet_recharge(self, info, **data):
        return resolve_wallet_recharge(info, data.get("id"))

    def resolve_wallet_recharge_available_payment_gateways(self, *_args, **_kwargs):
        available_payment_gateways = [
            gtw for gtw in
            get_plugins_manager().list_payment_gateways() if
            gtw.get('name').strip().lower() != 'wallet']
        return available_payment_gateways


class WalletMutations(graphene.ObjectType):
    wallet_recharge_create = WalletRechargeCreate.Field()
    wallet_recharge_payment_create = WalletRechargePaymentCreate.Field()
    wallet_recharge_complete = WalletRechargeComplete.Field()
