from typing import Any

from loguru import logger

from application.controllers.orders.order_base_controller import OrderBaseController
from application.providers.stripe_charge_provider import StripeChargeProvider
from application.repositories.order_repository import OrderRepository
from application.repositories.purchase_record_repository import PurchaseRecordRepository
from application.repositories.transaction_repository import TransactionRepository


class OrderUpdatedController(OrderBaseController):
    PROVIDER_MAP = {
        'stripe': StripeChargeProvider()
    }

    def __init__(
            self,
            txn_repo: TransactionRepository,
            order_repo: OrderRepository,
            purchase_record_repo: PurchaseRecordRepository
    ) -> None:
        self.txn_repo = txn_repo
        super().__init__(
            order_repo=order_repo,
            purchase_record_repo=purchase_record_repo
        )

    def process(
            self,
            transaction_id: str,
            provider: str,
            data: Any
    ) -> None:
        logger.info("Updating order from webhook", kv={
            'transaction_id': transaction_id,
            'provider': provider
        })
        txn = self.txn_repo.get_by_transaction_id(transaction_id=transaction_id)
        order = self.order_repo.get_by_order_id(
            order_id=txn.order_id
        )
        purchase_records = [
            self.purchase_record_repo.get_by_id(record_id=record_id) for record_id in order.purchase_record_ids
        ]
        provider = self.PROVIDER_MAP[provider]
        logger.info("Updating order", kv={
            'transaction_id': transaction_id,
            'provider': provider,
            'order_id': order.order_id,
            'current_txn_status': txn.status,
            'order_status': order.status
        })
        txn_result = provider.handle_provider_response(
            transaction=txn, stripe_response=data
        )
        updated_order = self.post_payment_process(
            txn=txn_result, order=order
        )
        self.post_order_processing(
            order=updated_order, purchase_records=purchase_records
        )

        logger.info("Order update complete", kv={
            'transaction_id': transaction_id,
            'provider': provider,
            'order_id': order.order_id,
            'current_txn_status': txn_result.status,
            'order_status': updated_order.status
        })


order_updated_controller = OrderUpdatedController(
    txn_repo=TransactionRepository(),
    order_repo=OrderRepository(),
    purchase_record_repo=PurchaseRecordRepository()
)