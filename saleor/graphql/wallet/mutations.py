import uuid

import graphene
from django.core.exceptions import ValidationError

from .types import Wallet, WalletRecharge
from ..account.i18n import I18nMixin
from ..core.mutations import BaseMutation
from ..core.scalars import Decimal
from ..core.types import common as common_types
from ..core.utils import from_global_id_strict_type
from ..payment.types import Payment
from ...checkout.error_codes import CheckoutErrorCode
from ...core.utils import get_client_ip
from ...payment import PaymentError, gateway, models as payment_models
from ...payment.utils import create_razorpay_order
from ...wallet import models


class WalletRechargePaymentInput(graphene.InputObjectType):
    gateway = graphene.Field(
        graphene.String,
        description="A gateway to use for that recharge payment.",
        required=True,
    )
    amount = Decimal(
        required=False,
        description=(
            "Total amount of recharge."
        ),
    )


class WalletRechargeCreate(BaseMutation, I18nMixin):
    wallet_recharge = graphene.Field(WalletRecharge,
                                     description="Wallet recharge object.")

    class Arguments:
        wallet_id = graphene.ID(description="Wallet ID.", required=True)

    class Meta:
        description = "Create a new wallet recharge."

    @classmethod
    def perform_mutation(cls, _root, info, wallet_id, **data):
        wallet_id = from_global_id_strict_type(
            wallet_id, only_type=Wallet, field="wallet_id"
        )
        wallet = models.Wallet.objects.prefetch_related().get(pk=wallet_id)

        wallet_recharge = models.WalletRecharge(
            wallet=wallet,
            status=models.WalletRechargeStatus.initiated.value,
        )
        wallet_recharge.save()

        return WalletRechargeCreate(wallet_recharge=wallet_recharge)


class WalletRechargePaymentCreate(BaseMutation, I18nMixin):
    wallet_recharge = graphene.Field(WalletRecharge,
                                     description="Wallet recharge object.")
    payment = graphene.Field(Payment, description='Related Payment object')

    class Arguments:
        wallet_recharge_id = graphene.ID(description="WalletRecharge ID.",
                                         required=True)
        input = WalletRechargePaymentInput(
            description="Data required to create a new wallet recharge.", required=True
        )

    class Meta:
        description = "Create a new payment for given wallet recharge."
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def perform_mutation(cls, _root, info, wallet_recharge_id, **data):
        wallet_recharge_id = from_global_id_strict_type(
            wallet_recharge_id, only_type=WalletRecharge, field="wallet_recharge_id"
        )
        wallet_recharge: models.WalletRecharge = models.WalletRecharge.objects.select_related(
            'wallet__user__default_billing_address').get(pk=wallet_recharge_id)

        user = wallet_recharge.wallet.user
        billing_email = user.email or ''
        billing_address = user.default_billing_address

        if wallet_recharge.wallet.user.default_billing_address:
            defaults = {
                "billing_first_name": billing_address.first_name,
                "billing_last_name": billing_address.last_name,
                "billing_company_name": billing_address.company_name,
                "billing_address_1": billing_address.street_address_1,
                "billing_address_2": billing_address.street_address_2,
                "billing_city": billing_address.city,
                "billing_postal_code": billing_address.postal_code,
                "billing_country_code": billing_address.country.code,
                "billing_country_area": billing_address.country_area,
            }
        else:
            defaults = {
                "billing_first_name": user.first_name,
                "billing_last_name": user.last_name,
                "billing_company_name": "",
                "billing_address_1": "",
                "billing_address_2": "",
                "billing_city": "",
                "billing_postal_code": "",
                "billing_country_code": "",
                "billing_country_area": "",
            }

        data = data["input"]
        amount = data["amount"]
        extra_data = {"customer_user_agent": info.context.META.get("HTTP_USER_AGENT")}

        payment, _created = payment_models.Payment.objects.get_or_create(
            **defaults,
            gateway=data["gateway"],
            token=str(wallet_recharge.id),
            total=amount,
            currency=wallet_recharge.wallet.currency,
            billing_email=billing_email,
            extra_data=extra_data,
            customer_ip_address=get_client_ip(info.context),
        )
        create_razorpay_order(payment)

        wallet_recharge.payment = payment
        wallet_recharge.amount = amount
        wallet_recharge.status = models.WalletRechargeStatus.initiated.value
        wallet_recharge.save()

        return WalletRechargePaymentCreate(
            wallet_recharge=wallet_recharge,
            payment=payment)


class WalletRechargeComplete(BaseMutation, I18nMixin):
    wallet_recharge = graphene.Field(WalletRecharge,
                                     description="Wallet recharge object.")

    class Arguments:
        wallet_recharge_id = graphene.ID(description="WalletRecharge ID.",
                                         required=True)

    class Meta:
        description = (
            "Completes the checkout. As a result a new order is created and "
            "a payment charge is made. This action requires a successful "
            "payment before it can be performed. "
            "In case additional confirmation step as 3D secure is required "
            "confirmationNeeded flag will be set to True and no order created "
            "until payment is confirmed with second call of this mutation."
        )

    @classmethod
    def perform_mutation(cls, _root, info, wallet_recharge_id, **data):
        wallet_recharge_id = from_global_id_strict_type(
            wallet_recharge_id, only_type=WalletRecharge, field="wallet_recharge_id"
        )
        wallet_recharge = models.WalletRecharge.objects.select_related(
            'wallet__user').get(pk=wallet_recharge_id)

        payment: payment_models.Payment = wallet_recharge.payment

        payment_confirmation = payment.to_confirm
        try:
            if payment_confirmation:
                txn = gateway.confirm(payment)
            else:
                txn = gateway.process_payment(
                    payment=payment, token=payment.token, store_source=False
                )

            if not txn.is_success:
                raise PaymentError(txn.error)
        except PaymentError as e:
            wallet_recharge.status = models.WalletRechargeStatus.failed.value
            wallet_recharge.save()
            raise ValidationError(str(e), code=CheckoutErrorCode.PAYMENT_ERROR)

        wallet: models.Wallet = wallet_recharge.wallet

        wallet.deposit(amount=wallet_recharge.amount,
                       transaction_type=models.WalletTransactionType.Credit.value,
                       source='App', reason='Recharge',
                       description=f'Paid using {payment.gateway}. Txn Id: {payment.token}')

        wallet_recharge.status = models.WalletRechargeStatus.successful.value
        wallet_recharge.save()

        return WalletRechargeComplete(wallet_recharge=wallet_recharge)
