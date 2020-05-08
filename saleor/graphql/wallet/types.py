import graphene
import graphene_django_optimizer as gql_optimizer

from ..core.connection import CountableDjangoObjectType
from ..core.types import Money
from ...wallet import models

WalletTransactionType = graphene.Enum.from_enum(models.WalletTransactionType)
WalletRechargeStatus = graphene.Enum.from_enum(models.WalletRechargeStatus)


class WalletTransaction(CountableDjangoObjectType):
    transaction_type = WalletTransactionType()
    transaction_id = graphene.String()

    class Meta:
        description = "An object representing a single wallet transaction."
        interfaces = [graphene.relay.Node]
        model = models.WalletTransaction
        filter_fields = ["id"]
        only_fields = [
            "id",
            "created",
            "wallet",
            "transaction_type",
            "amount",
            "ledger_amount",
            "source",
            "reason",
            "description",
        ]

    @staticmethod
    def resolve_transaction_id(root: models.WalletTransaction, _info):
        return str(root.id)


class Wallet(CountableDjangoObjectType):
    current_balance = graphene.Field(Money, description="Current Wallet Balance.")
    credit_limit = graphene.Field(Money, description="Current Wallet Credit limit.")
    wallet_transactions = gql_optimizer.field(
        graphene.List(WalletTransaction,
                      description="List of transactions for the wallet."),
        model_field="wallet_transactions",
    )

    class Meta:
        description = "An object representing a single wallet."
        interfaces = [graphene.relay.Node]
        model = models.Wallet
        filter_fields = ["id"]
        only_fields = [
            "id",
            "is_active",
            "created",
            "user",
            "currency",
            "credit_limit",
            "current_balance",
        ]

    @staticmethod
    def resolve_current_balance(root: models.Wallet, _info):
        return root.get_current_balance()

    @staticmethod
    def resolve_credit_limit(root: models.Wallet, _info):
        return root.get_credit_limit()

    @staticmethod
    def resolve_wallet_transactions(root: models.Wallet, *_args, **_kwargs):
        return root.wallet_transactions.all()


class WalletRecharge(CountableDjangoObjectType):
    status = WalletRechargeStatus()

    class Meta:
        description = "An object representing a single wallet recharge."
        interfaces = [graphene.relay.Node]
        model = models.WalletRecharge
        filter_fields = ["id"]
        only_fields = [
            "id",
            "created",
            "wallet",
            "payment",
            "amount",
            "status",
        ]
