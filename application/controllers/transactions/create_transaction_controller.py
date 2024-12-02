from typing import Dict, Any, Optional

from application.errors import WalletError, PaymentCreationError
from application.models.instrument import Instrument
from application.models.transactions import Transaction, TRANSACTION_STATUS_COMPLETED, TRANSACTION_STATUS_FAILED
from application.providers.stripe_charge_provider import StripeChargeProvider, BaseChargeProvider
from application.repositories.transaction_repository import TransactionRepository
from application.repositories.wallet_repository import WalletRepository


class CreateTransactionController:

    PROVIDER_MAPPING: Dict[str, BaseChargeProvider] = {
        'stripe': StripeChargeProvider()
    }

    def __init__(self) -> None:
        self.txn_repository = TransactionRepository()
        self.wallet_repository = WalletRepository()

    def process(self, txn: Transaction) -> Transaction:
        # validate, write to record, generate payload, call provider, update record, generate response
        self.validate(txn=txn)

        # write to record
        self.txn_repository.create_record(transaction=txn)

        # read token
        instrument = self.wallet_repository.get_by_instrument_id(instrument_id=txn.instrument_id)

        # get provider
        provider_to_route = self.get_provider(instrument=instrument)
        provider = self.PROVIDER_MAPPING[provider_to_route]

        # call provider
        result = self.call_provider(
            provider=provider,
            instrument=instrument,
            txn=txn
        )

        if not result.has_error():
            result.status = TRANSACTION_STATUS_COMPLETED
            result.provider_transaction_id = provider.get_provider_transaction_id(
                txn=result
            )
        else:
            result.status = TRANSACTION_STATUS_FAILED

        # update DB with result
        self.txn_repository.update_record(transaction=result)

        return result


    def validate(self, txn: Transaction):
        raise NotImplemented()

    def get_provider(self, instrument: Instrument) -> str:
        provider_tokens = instrument.tokens
        available_providers = [provider_token.provider for provider_token in provider_tokens]
        if not available_providers:
            raise WalletError("There is no route-able provider")
        return available_providers[0]

    def call_provider(
            self,
            provider: BaseChargeProvider,
            instrument: Instrument,
            txn: Transaction,
            parent_txn: Optional[Transaction] = None,
    ) -> Transaction:
        raise NotImplemented()


class CreateAuthController(CreateTransactionController):
    def validate(self, txn: Transaction):
        if txn.transaction_id != txn.parent_transaction_id:
            raise PaymentCreationError('Parent txn ID and txn ID does not match for auth')

    def call_provider(
            self,
            provider: BaseChargeProvider,
            instrument: Instrument,
            txn: Transaction,
            parent_txn: Optional[Transaction] = None,
    ) -> Transaction:
        transaction = provider.create_auth(txn=txn, instrument=instrument)
        return transaction

class CaptureAuthController(CreateTransactionController):
    def validate(self, txn: Transaction):
        pass

    def call_provider(
            self,
            provider: BaseChargeProvider,
            instrument: Instrument,
            txn: Transaction,
            parent_txn: Optional[Transaction] = None,
    ) -> Transaction:
        transaction = provider.capture_auth(txn=txn, parent_txn=parent_txn)
        return transaction


class VoidAuthController(CreateTransactionController):
    def validate(self, txn: Transaction):
        pass

    def call_provider(
            self,
            provider: BaseChargeProvider,
            instrument: Instrument,
            txn: Transaction,
            parent_txn: Optional[Transaction] = None,
    ) -> Transaction:
        transaction = provider.void_auth(txn=txn, parent_txn=parent_txn)
        return transaction


class RefundController(CreateTransactionController):
    def validate(self, txn: Transaction):
        pass

    def call_provider(
            self,
            provider: BaseChargeProvider,
            instrument: Instrument,
            txn: Transaction,
            parent_txn: Optional[Transaction] = None,
    ) -> Transaction:
        transaction = provider.refund(txn=txn, parent_txn=parent_txn)
        return transaction





