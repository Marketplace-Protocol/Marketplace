from typing import Dict, Any, Optional

from loguru import logger

from application.errors import WalletError, PaymentCreationError, PaymentContextValidationError
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

        return self._process(txn=txn)

    def reprocess(self, txn_id) -> Transaction:
        # write to record
        txn = self.txn_repository.get_by_transaction_id(transaction_id=txn_id)
        return self._process(txn=txn)

    def _process(self, txn: Transaction) -> Transaction:
        logger.info(
            "Attempting to process payments",
            kv={
                "transaction_id": txn.transaction_id,
                "order_id": txn.order_id,
                "instrument_id": txn.instrument_id
            }
        )
        instrument = None

        if txn.instrument_id:
            # read token
            instrument = self.wallet_repository.get_by_instrument_id(instrument_id=txn.instrument_id)

            # get provider
            provider_to_route = self.get_provider(instrument=instrument)
        else:
            provider_to_route = 'stripe'

        txn.provider = provider_to_route
        provider = self.PROVIDER_MAPPING[provider_to_route]

        logger.info("Calling Payment Provider", kv={
            "transaction_id": txn.transaction_id,
            "order_id": txn.order_id,
            "instrument_id": txn.instrument_id,
            "provider": provider_to_route
        })
        # call provider
        result = self.call_provider(
            provider=provider,
            instrument=instrument,
            txn=txn
        )

        logger.info("Provider call complete", kv={
            "transaction_id": result.transaction_id,
            "order_id": result.order_id,
            "provider": provider_to_route,
            "transaction_status": result.status,
            "provider_transaction_id": result.provider_transaction_id,
            "provider_request": result.provider_request,
            "provider_response": result.provider_response,
            "provider_error": result.provider_error_details
        })
        # update DB with result
        self.txn_repository.update_record(transaction=result)

        return result

    def validate(self, txn: Transaction):
        raise NotImplemented()

    def get_provider(self, instrument: Instrument) -> str:
        provider_tokens = instrument.tokens
        available_providers = [provider_token.provider for provider_token in provider_tokens]
        if not available_providers:
            # Default to stripe
            return 'stripe'
        return available_providers[0]

    def call_provider(
            self,
            provider: BaseChargeProvider,
            txn: Transaction,
            instrument: Optional[Instrument] = None,
            parent_txn: Optional[Transaction] = None,
    ) -> Transaction:
        raise NotImplemented()


class CreateAuthController(CreateTransactionController):
    def validate(self, txn: Transaction):
        if not txn.transaction_id or not txn.parent_transaction_id\
                or not txn.action or not txn.status or not txn.amount.amount or not txn.amount.currency:
            raise PaymentContextValidationError('Transaction attribute missing')

        if txn.transaction_id != txn.parent_transaction_id:
            raise PaymentContextValidationError('Parent txn ID and txn ID does not match for auth')

    def call_provider(
            self,
            provider: BaseChargeProvider,
            txn: Transaction,
            instrument: Optional[Instrument] = None,
            parent_txn: Optional[Transaction] = None,
    ) -> Transaction:
        transaction = provider.create_auth(txn=txn, instrument=instrument)
        return transaction

class CaptureAuthController(CreateTransactionController):
    def validate(self, txn: Transaction):
        if not txn.transaction_id or not txn.parent_transaction_id \
                or not txn.action or not txn.status or not txn.amount.amount or not txn.amount.currency:
            raise PaymentContextValidationError('Transaction attribute missing')

        if txn.transaction_id == txn.parent_transaction_id:
            raise PaymentContextValidationError('Invalid combination of Parent txn ID and txn ID')
        #Can do more sophisticated validation here like amount based with respect to overcapture limits

    def call_provider(
            self,
            provider: BaseChargeProvider,
            txn: Transaction,
            instrument: Optional[Instrument] = None,
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
            txn: Transaction,
            instrument: Optional[Instrument] = None,
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
            txn: Transaction,
            instrument: Optional[Instrument] = None,
            parent_txn: Optional[Transaction] = None,
    ) -> Transaction:
        transaction = provider.refund(txn=txn, parent_txn=parent_txn)
        return transaction





