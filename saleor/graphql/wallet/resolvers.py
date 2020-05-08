import graphene
import graphene_django_optimizer as gql_optimizer

from .types import Wallet, WalletRecharge
from ...wallet import models


def resolve_wallets(info: graphene.ResolveInfo):
    queryset = models.Wallet.objects.filter(user=info.context.user)

    if queryset.count() == 0:
        models.Wallet.objects.create(user=info.context.user)

    return gql_optimizer.query(queryset, info)


def resolve_wallet(info, wallet_id):
    return graphene.Node.get_node_from_global_id(info, wallet_id, Wallet)


def resolve_wallet_recharge(info, wallet_recharge_id):
    return graphene.Node.get_node_from_global_id(info, wallet_recharge_id,
                                                 WalletRecharge)
