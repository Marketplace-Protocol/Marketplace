import json

import inflection
import stripe
import stripe.error as stripe_error
from stripe.stripe_object import StripeObject

from application.settings import STRIPE_KEY
from application.models.instrument import Instrument, ProviderToken
from application.models.transactions import Transaction
from application.providers.charge_base_provider import BaseChargeProvider


class StripeChargeProvider(BaseChargeProvider):
    def __init__(self):
        stripe.api_key = STRIPE_KEY
        stripe.default_http_client = stripe.http_client.RequestsClient(timeout=60)

    def _get_stripe_token(self, instrument: Instrument) -> ProviderToken:
        for token in instrument.tokens:
            if token.provider == 'stripe':
                return token

    def create_auth(self, txn: Transaction, instrument: Instrument) -> Transaction:

        provider_request_param = {
            "amount": txn.amount.amount,
            "currency": txn.amount.currency,
            "capture_method": "manual",
            "idempotency_key": txn.transaction_id,
            "automatic_payment_methods": {
                "enabled": True,
                "allow_redirects": "never"
            },
        }
        if instrument:
            stripe_token = self._get_stripe_token(instrument=instrument)
            provider_request_param['payment_method'] = stripe_token.token
            provider_request_param['confirm'] = True
            if stripe_token.customer_id:
                provider_request_param['customer'] = stripe_token.customer_id

        try:
            res = stripe.PaymentIntent.create(**provider_request_param)
            return self.handle_provider_response(
                stripe_response=res,
                transaction=txn
            )
        except Exception as e:
            return self.handle_provider_exceptions(exception=e, transaction=txn)

    def capture_auth(self, txn: Transaction, parent_txn: Transaction) -> Transaction:
        try:
            payment_intent_id = self.get_provider_transaction_id(
                txn=parent_txn
            )
            payment_intent = self.retrieve_payment_intent(
                payment_intent_id=payment_intent_id
            )
            if payment_intent.status == 'succeeded':
                return self.handle_provider_response(
                    stripe_response=payment_intent,
                    transaction=txn
                )
            res = stripe.PaymentIntent.capture(payment_intent_id)
            return self.handle_provider_response(
                stripe_response=res,
                transaction=txn
            )
        except Exception as e:
            return self.handle_provider_exceptions(exception=e, transaction=txn)

    def void_auth(self, txn: Transaction, parent_txn: Transaction) -> Transaction:
        try:
            payment_intent_id = self.get_provider_transaction_id(
                txn=parent_txn
            )
            res = stripe.PaymentIntent.cancel(payment_intent_id)
            return self.handle_provider_response(
                stripe_response=res,
                transaction=txn
            )
        except Exception as e:
            return self.handle_provider_exceptions(exception=e, transaction=txn)

    def refund(self, txn: Transaction, parent_txn: Transaction) -> Transaction:
        try:
            payment_intent_id = self.get_provider_transaction_id(
                txn=parent_txn
            )
            res = stripe.Refund.create(payment_intent_id)
            return self.handle_provider_response(
                stripe_response=res,
                transaction=txn
            )
        except Exception as e:
            return self.handle_provider_exceptions(exception=e, transaction=txn)

    def retrieve_payment_intent(self, payment_intent_id: str) -> StripeObject:
        pi = stripe.PaymentIntent.retrieve(payment_intent_id)
        return pi

    def get_provider_transaction_id(self, txn: Transaction) -> str:
        return txn.provider_transaction_id

    def handle_provider_exceptions(
            self,
            exception: Exception,
            transaction: Transaction
    ) -> Transaction:
        if isinstance(exception, stripe_error.StripeError):
            return self.handle_stripe_response(stripe_error=exception, transaction=transaction)
        else:
            return self.handle_unknown_response(exception=exception, transaction=transaction)


    def handle_provider_response(
            self,
            stripe_response: StripeObject,
            transaction: Transaction
    ) -> Transaction:
        transaction.provider_transaction_id = stripe_response['id']
        transaction.provider_response = json.dumps(stripe_response)
        return transaction

    def handle_stripe_response(
            self,
            stripe_error: Exception,
            transaction: Transaction
    ) -> Transaction:
        stripe_error_info = dict(stripe_error.error)
        transaction.provider_error_details = stripe_error_info
        return transaction

    def handle_unknown_response(
            self,
            exception: Exception,
            transaction: Transaction
    ) -> Transaction:
        stripe_unknown_error = {
            'type': inflection.underscore(exception.__class__.__name__),
            'message': str(exception)
        }
        transaction.provider_error_details = stripe_unknown_error
        return transaction

