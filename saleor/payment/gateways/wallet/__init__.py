import uuid
from typing import Optional

from saleor.wallet.models import Wallet, WalletTransactionType, WalletTransaction
from ... import TransactionKind
from ...interface import GatewayConfig, GatewayResponse, PaymentData


def get_client_token(**_):
    return str(uuid.uuid4())


def get_wallet(payment_information: PaymentData) -> Optional[Wallet]:
    try:
        return Wallet.objects.get(user__email=payment_information.customer_email,
                                  currency=payment_information.currency, is_active=True)
    except Wallet.DoesNotExist:
        return None


def authorize(
        payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    wallet = get_wallet(payment_information)

    if wallet and wallet.can_spend(payment_information.amount):
        success = True
    else:
        success = False

    error = None
    if not success:
        error = "Unable to authorize transaction"
    return GatewayResponse(
        is_success=success,
        action_required=False,
        kind=TransactionKind.AUTH,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token,
        error=error,
    )


def void(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    error = None
    success = True
    if not success:
        error = "Unable to void the transaction."
    return GatewayResponse(
        is_success=success,
        action_required=False,
        kind=TransactionKind.VOID,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token,
        error=error,
    )


def capture(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    """Perform capture transaction."""
    error = None

    wallet = get_wallet(payment_information)

    if wallet and wallet.can_spend(payment_information.amount):
        wallet_transaction = wallet.withdraw(
            amount=payment_information.amount,
            transaction_type=WalletTransactionType.Debit.value,
            source='Online Store',
            reason=f'Paid for online order',
            description=f'Transaction ID: {payment_information.token}')
        payment_information.token = wallet_transaction.id
        success = True
    else:
        success = False

    if not success:
        error = "Unable to process capture"

    return GatewayResponse(
        is_success=success,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token,
        error=error,
    )


def confirm(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    """Perform confirm transaction."""
    error = None

    wallet = get_wallet(payment_information)

    if wallet:
        try:
            wallet_transaction = wallet.wallet_transactions.get(
                id=payment_information.token)
            success = wallet_transaction.amount == payment_information.amount
        except WalletTransaction.DoesNotExist:
            success = False
    else:
        success = False
    if not success:
        error = "Unable to process capture"

    return GatewayResponse(
        is_success=success,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token,
        error=error,
    )


def refund(payment_information: PaymentData, config: GatewayConfig) -> GatewayResponse:
    error = None

    wallet = get_wallet(payment_information)

    if wallet:
        try:
            wallet_debit_transaction = wallet.wallet_transactions.get(
                id=payment_information.token)
            wallet_credit_transaction = wallet.deposit(
                amount=payment_information.amount,
                transaction_type=WalletTransactionType.Credit.value,
                source='Online Store',
                reason=f'Refund for order {payment_information.order_id}',
                description=f'Original debit transaction ID: {payment_information.token}')
            success = True
        except WalletTransaction.DoesNotExist:
            success = False
    else:
        success = False

    if not success:
        error = "Unable to process refund"
    return GatewayResponse(
        is_success=success,
        action_required=False,
        kind=TransactionKind.REFUND,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token,
        error=error,
    )


def process_payment(
        payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    """Process the payment."""
    return capture(payment_information=payment_information, config=config)
