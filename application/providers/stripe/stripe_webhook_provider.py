from typing import Any

import stripe

from loguru import logger

from application.controllers.orders.order_updated_controller import order_updated_controller
from application.errors import ValidationError, ContextValidationError
from application.models.webhook_instruction import WebhookInstruction
from application.providers.stripe.constants import PAYLOAD_ENCODING, SIGNATURE_HEADER
from application.settings import STRIPE_WEBHOOK_SECRET


class WebhookProvider:
    EVENT_CONTROLLER_HANDLER = {
        'transaction_updated': order_updated_controller
    }

    def validate_and_construct(self, webhook: Any) -> Any:
        raise NotImplemented()

    def validate_context(self, event: Any) -> Any:
        raise NotImplemented()

    def process(self, webhook: Any) -> None:
        raise NotImplemented()


class StripeWebhookProvider(WebhookProvider):
    EVENT_TYPE_MAPPER = {
        'payment_intent.succeeded': 'transaction_updated',
        'payment_intent.payment_failed': 'transaction_updated',
        'payment_intent.requires_action': 'transaction_updated',
    }
    SUPPORTED_EVENT_TYPES = EVENT_TYPE_MAPPER.keys()

    def validate_and_construct(self, webhook: Any) -> Any:
        try:
            payload = webhook.data.decode(PAYLOAD_ENCODING)
            signature = webhook.headers.get(SIGNATURE_HEADER)

            webhook_secret = self._get_webhook_secret()

            event = stripe.Webhook.construct_event(payload, signature, webhook_secret)

            return event
        except Exception as e:
            raise ValidationError(str(e))

    def validate_context(self, event: stripe.Event) -> Any:
        event_type = event.get('type')
        if event_type not in self.SUPPORTED_EVENT_TYPES:
            raise ContextValidationError("Unsupported event type")


    def process(self, webhook: Any) -> None:
        logger.info("Stripe webhook received", kv=webhook)
        event = self.validate_and_construct(webhook=webhook)
        self.validate_context(event=event)

        logger.info("Stripe webhook validated", kv=webhook)

        event_id = event.get('id')
        event_type = self.EVENT_TYPE_MAPPER[event.get('type')]

        webhook_instruction = WebhookInstruction(
            webhook_id=event_id,
            actor='stripe',
            type=event_type
        )

        logger.info("webhook instruction created", kv=webhook)

        stripe_object = self.extract_transaction_from_webhook(event=event)
        logger.info(stripe_object)
        metadata = stripe_object.get('metadata')
        transaction_id = metadata.get('transaction_id')

        controller = self.EVENT_CONTROLLER_HANDLER[webhook_instruction.type]

        controller.create(
            transaction_id = transaction_id,
            provider='stripe',
            data=stripe_object
        )

        logger.info("webhook processed", kv=webhook)

        return


    def _get_webhook_secret(self) -> str:
        return STRIPE_WEBHOOK_SECRET

    def extract_transaction_from_webhook(self, event: stripe.Event) -> stripe.Object:
        return event.data.object



stripe_webhook_provider = StripeWebhookProvider()