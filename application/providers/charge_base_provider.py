from typing import Any, Optional

from application.models.instrument import Instrument
from application.models.transactions import Transaction


class BaseChargeProvider:

    def create_auth(self, txn: Transaction, instrument: Optional[Instrument]=None) -> Transaction:
        raise NotImplemented()

    def capture_auth(self, txn: Transaction, parent_txn: Transaction) -> Transaction:
        raise NotImplemented()

    def void_auth(self, txn: Transaction, parent_txn: Transaction) -> Transaction:
        raise NotImplemented()

    def refund(self, txn: Transaction, parent_txn: Transaction) -> Transaction:
        raise NotImplemented()

    def get_provider_transaction_id(self, txn: Transaction) -> str:
        raise NotImplemented()

    def handle_provider_response(
            self,
            res: Any,
            transaction: Transaction
    ) -> Transaction:
        raise NotImplemented()

    def handle_provider_exceptions(
            self,
            exception: Exception,
            transaction: Transaction
    ):
        raise NotImplemented()