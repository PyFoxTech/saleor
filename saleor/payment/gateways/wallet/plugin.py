from typing import TYPE_CHECKING

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField
from . import GatewayConfig, capture, process_payment, refund

GATEWAY_NAME = "Wallet"

if TYPE_CHECKING:
    from . import GatewayResponse, PaymentData


class WalletGatewayPlugin(BasePlugin):
    PLUGIN_NAME = GATEWAY_NAME
    PLUGIN_ID = "pyfox.payments.wallet"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = GatewayConfig(
            gateway_name=GATEWAY_NAME,
            auto_capture=True,
            connection_params={},
            store_customer=False,
        )

    @classmethod
    def _get_default_configuration(cls):
        defaults = {
            "name": cls.PLUGIN_NAME,
            "description": "",
            "active": False,
            "configuration": [],
        }
        return defaults

    def _get_gateway_config(self):
        return self.config

    def capture_payment(
            self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return capture(payment_information, self._get_gateway_config())

    def refund_payment(
            self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return refund(payment_information, self._get_gateway_config())

    def process_payment(
            self, payment_information: "PaymentData", previous_value
    ) -> "GatewayResponse":
        return process_payment(payment_information, self._get_gateway_config())

    def get_payment_config(self, previous_value):
        return []
