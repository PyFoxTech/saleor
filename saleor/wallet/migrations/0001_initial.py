# Generated by Django 2.2.10 on 2020-04-21 19:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import saleor.wallet.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted', models.NullBooleanField(editable=False)),
                ('currency', models.CharField(default='INR', editable=False, max_length=3)),
                ('current_balance', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=12)),
                ('credit_limit', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=12)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wallet', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='WalletTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('deleted', models.NullBooleanField(editable=False)),
                ('transaction_type', models.CharField(choices=[(saleor.wallet.models.WalletTransactionType('Credit'), 'Credit'), (saleor.wallet.models.WalletTransactionType('Debit'), 'Debit')], max_length=40)),
                ('amount', models.DecimalField(decimal_places=2, editable=False, max_digits=12)),
                ('ledger_amount', models.DecimalField(decimal_places=2, editable=False, max_digits=12)),
                ('source', models.CharField(max_length=40)),
                ('reason', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=255)),
                ('wallet', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wallet_transactions', to='wallet.Wallet')),
            ],
        ),
    ]