from typing import Any, List, Dict, Optional
import shortuuid

from loguru import logger

from application.controllers.orders.order_base_controller import OrderBaseController
from application.controllers.transactions.create_transaction_controller import CreateAuthController
from application.errors import ValidationError, InvoiceCreationError, PaymentCreationError
from application.models.money import Money
from application.models.order import Order, LineItem, Invoice, INVOICE_TYPE_INCOMING, INVOICE_STATUS_CREATED, \
    ORDER_STATUS_CREATED, ORDER_STATUS_BOOKED, INVOICE_STATUS_PENDING
from application.models.purchase_record import PurchaseRecord, PURCHASE_RECORD_READY, PURCHASE_RECORD_CREATED
from application.models.transactions import Transaction, TRANSACTION_ACTION_AUTH, TRANSACTION_STATUS_CREATED
from application.repositories.order_repository import OrderRepository
from application.repositories.purchase_record_repository import PurchaseRecordRepository
from application.services.task_queue import TaskQueueService
from application.utils import now_in_epoch_sec


class CreateOrderController(OrderBaseController):
    def __init__(self):
        self.order_repository = OrderRepository()
        self.create_auth_controller = CreateAuthController()
        self.task_queue = TaskQueueService()
        self.purchase_record_repo = PurchaseRecordRepository()
        super().__init__(
            order_repo=self.order_repository,
            purchase_record_repo=self.purchase_record_repo
        )

    def process(self, request: Any):
        self.validate_request(request=request)
        purchase_records = self.generate_purchase_records(request=request)
        [self.validate_context(purchase_record=purchase_record) for purchase_record in purchase_records]
        logger.info('Purchase Record retrieved', kv={
            'record_ids': [record.record_id for record in purchase_records],
        })

        instrument_id = request.get('instrument_id', None)
        order = self.generate_order(instrument_id=instrument_id, purchase_records=purchase_records)
        self.order_repository.create_order(order=order)
        logger.info(
            'created invoice and order',
            kv={
                "order_id": order.order_id,
                "record_ids": order.purchase_record_ids,
            }
        )

        # queue force complete
        self.task_queue.queue_order_fulfillment(
            payload={'order_id': order.order_id},
            delay=10
        )

        # Create auth
        txn_result = self.create_auth_controller.process(
            txn=self.generate_auth_transaction_from_order(order=order)
        )

        logger.info(
            'Payment processed',
            kv={
                "order_id": order.order_id,
                "transaction_id": txn_result.transaction_id
            }
        )

        # Update order
        order_result = self.post_payment_process(
            txn=txn_result, order=order
        )

        # Update purchase record
        self.post_order_processing(
            order=order_result, purchase_records=purchase_records
        )
        logger.info(
            'Post processing completed',
            kv={
                "order_id": order.order_id,
            }
        )
        return self.generate_response(order=order, txn=txn_result)

    def generate_response(
            self,
            order: Optional[Order] = None,
            txn: Optional[Transaction] = None,
    ) -> Dict[str, Any]:
        res = {}
        if txn:
            txn_res = {
                'status': txn.status
            }
            if txn.is_declined():
                res['error_details'] = {
                    'error_message': 'Your payment failed.. Please make sure your payment information is correct!',
                    'error_details': 'Auth was declined',
                    'error_type': 'PaymentFailure'
                }
            elif txn.is_created():
                client_secret = txn.client_secret
                txn_res['client_secret'] = client_secret
            res['payment'] = txn_res
        if order:
            res['order'] = {
                'status': order.status,
                'order_id': order.order_id
            }
            res['purchase_intent'] = {
                'record_ids': order.purchase_record_ids
            }

        logger.info('Returning result', kv={
            'order_id': order.order_id if order else 'NONE',
            'response': res
        })
        return res

    def validate_context(self, purchase_record: PurchaseRecord):
        # TODO: purchase record, instrument id, line item & product package
        logger.info("Validating context")
        logger.info(purchase_record)
        return None

    def validate_request(self, request: Any) -> None:
        if 'purchases' not in request:
            raise ValidationError("record_id missing")

        purchases = request['purchases']
        for purchase in purchases:
            if 'record_id' not in purchase:
                raise ValidationError("record_id missing")

    def generate_purchase_records(self, request: Any) -> List[PurchaseRecord]:
        purchase_list = []
        purchases = request['purchases']
        for purchase in purchases:
            record_id = purchase['record_id']
            item = self.purchase_record_repo.get_by_id(record_id=record_id)
            purchase_list.append(item)
        return purchase_list

    def generate_order(
            self,
            purchase_records: List[PurchaseRecord],
            instrument_id: Optional[str] = None,
    ) -> Order:
        try:
            incoming_invoice = self._generate_incoming_invoice(
                instrument_id=instrument_id,
                purchase_records=purchase_records
            )
            return Order(
                order_id=shortuuid.uuid(),
                user_id=purchase_records[0].user_id,
                entity=incoming_invoice.counterparty,
                status=ORDER_STATUS_CREATED,
                created_at=now_in_epoch_sec(),
                updated_at=now_in_epoch_sec(),
                purchase_record_ids=[record.record_id for record in purchase_records],
                incoming_invoice=incoming_invoice,
                outgoing_invoice=None
            )
        except Exception as e:
            raise InvoiceCreationError(str(e))

    def _generate_incoming_invoice(
            self,
            purchase_records: List[PurchaseRecord],
            instrument_id: Optional[str] = None,
    ) -> Invoice:
        try:
            invoice_name = ''
            total_amount = 0
            currency = 'USD'
            exponent = 2
            lin_items = []
            for record in purchase_records:
                invoice_name += f'{record.product_name()} x 1\n'
                lin_items += record.line_items
                for li in record.line_items:
                    total_amount += li.amount.amount
                    currency = li.amount.currency
                    exponent = li.amount.exponent

            return Invoice(
                invoice_name=invoice_name,
                counterparty=purchase_records[0].user_id,
                type=INVOICE_TYPE_INCOMING,
                status=INVOICE_STATUS_CREATED,
                amount=Money(
                    amount=total_amount,
                    currency=currency,
                    exponent=exponent
                ),
                instrument_id=instrument_id,
                line_items=lin_items
            )
        except Exception as e:
            raise InvoiceCreationError(str(e))

    def generate_auth_transaction_from_order(self, order: Order) -> Transaction:
        try:
            txn_id = shortuuid.uuid()
            return Transaction(
                transaction_id=txn_id,
                parent_transaction_id=txn_id,
                order_id=order.order_id,
                instrument_id=order.incoming_invoice.instrument_id,
                action=TRANSACTION_ACTION_AUTH,
                status=TRANSACTION_STATUS_CREATED,
                amount=order.incoming_invoice.amount,
            )
        except Exception as e:
            raise PaymentCreationError(str(e))

