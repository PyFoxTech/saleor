import enum
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from prices import Money

from .exceptions import InsufficientWalletBalance
from ..payment.models import Payment


class WalletTransactionType(enum.Enum):
    Credit = 'Credit'
    Debit = 'Debit'

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class WalletQueryset(models.QuerySet):
    def delete(self):
        self.update(deleted=True)

    def active(self):
        return self.filter(is_active=True)


class WalletManager(models.Manager):
    use_for_related_fields = True

    def with_deleted(self):
        return WalletQueryset(self.model, using=self._db)

    def deleted(self):
        return self.with_deleted().filter(deleted=True)

    def get_queryset(self):
        return self.with_deleted().exclude(deleted=True)


class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="wallet",
        db_index=True
    )
    deleted = models.NullBooleanField(editable=False)

    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
        default=settings.DEFAULT_CURRENCY,
        editable=False,
    )
    current_balance = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
        editable=False,
    )
    credit_limit = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
        editable=False,
    )

    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def delete(self, *args, **kwargs):
        self.deleted = True
        self.save()

    objects = WalletManager()

    def get_current_balance(self):
        return Money(self.current_balance,
                     self.currency or settings.DEFAULT_CURRENCY)

    def get_credit_limit(self):
        return Money(self.credit_limit,
                     self.currency or settings.DEFAULT_CURRENCY)

    def can_spend(self, amount: Decimal):
        return amount <= (self.current_balance + self.credit_limit)

    def deposit(self, amount: Decimal, transaction_type: WalletTransactionType,
                source: str,
                reason: str, description: str) -> "WalletTransaction":
        """Deposits a value to the wallet.
        Also creates a new transaction with the deposit
        value.
        """
        assert transaction_type == WalletTransactionType.Credit.value
        ledger_amount = self.current_balance + amount
        wallet_transaction = self.wallet_transactions.create(
            transaction_type=transaction_type,
            amount=amount,
            ledger_amount=ledger_amount,
            source=source,
            reason=reason,
            description=description,
        )
        self.current_balance = ledger_amount
        self.save()

        return wallet_transaction

    def withdraw(self, amount: Decimal, transaction_type: WalletTransactionType,
                 source: str,
                 reason: str, description: str) -> "WalletTransaction":
        """Withdraw's a value from the wallet.
        Also creates a new transaction with the withdraw
        value.
        Should the withdrawn amount is greater than the
        balance this wallet currently has, it raises an
        :mod:`InsufficientBalance` error. This exception
        inherits from :mod:`django.db.IntegrityError`. So
        that it automatically rolls-back during a
        transaction lifecycle.
        """
        assert transaction_type == WalletTransactionType.Debit.value

        if not self.can_spend(amount):
            raise InsufficientWalletBalance('This wallet has insufficient balance.')

        ledger_amount = self.current_balance - amount
        wallet_transaction = self.wallet_transactions.create(
            transaction_type=transaction_type,
            amount=-amount,
            ledger_amount=ledger_amount,
            source=source,
            reason=reason,
            description=description,
        )
        self.current_balance = ledger_amount
        self.save()

        return wallet_transaction


class WalletTransactionQueryset(models.QuerySet):
    def delete(self):
        self.update(deleted=True)


class WalletTransactionManager(models.Manager):
    use_for_related_fields = True

    def with_deleted(self):
        return WalletTransactionQueryset(self.model, using=self._db)

    def deleted(self):
        return self.with_deleted().filter(deleted=True)

    def get_queryset(self):
        return self.with_deleted().exclude(deleted=True)


def get_random_big_integer():
    return int.from_bytes(uuid.uuid1().bytes, byteorder='big', signed=False) >> 64


class WalletTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    deleted = models.NullBooleanField(editable=False)
    wallet = models.ForeignKey(Wallet, related_name='wallet_transactions', null=True,
                               on_delete=models.SET_NULL, db_index=True)
    transaction_type = models.CharField(max_length=40,
                                        choices=WalletTransactionType.choices(),
                                        db_index=True)
    amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        editable=False,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    ledger_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        editable=False,
    )
    source = models.CharField(max_length=40)
    reason = models.CharField(max_length=100)
    description = models.CharField(max_length=255)

    def delete(self, *args, **kwargs):
        self.deleted = True
        self.save()

    objects = WalletTransactionManager()

    class Meta:
        ordering = ['-created']


class WalletRechargeStatus(enum.Enum):
    initiated = 'initiated'
    payment_created = 'payment_created'
    abandoned = 'abandoned'
    failed = 'failed'
    successful = 'successful'

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class WalletRecharge(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, db_index=True,
                               related_name='wallet_recharges')
    payment = models.ForeignKey(Payment, null=True, on_delete=models.PROTECT)
    amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        editable=False,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    status = models.CharField(max_length=40, choices=WalletRechargeStatus.choices(),
                              db_index=True,
                              default=WalletRechargeStatus.initiated.value)

    class Meta:
        ordering = ['-created']
