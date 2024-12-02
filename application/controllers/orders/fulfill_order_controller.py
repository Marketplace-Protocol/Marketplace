from application.controllers.transactions.create_transaction_controller import CaptureAuthController, VoidAuthController
from application.errors import PaymentCreationError
from application.models.money import Money
from application.models.order import Order, Invoice
from application.models.transactions import Transaction, TRANSACTION_STATUS_CREATED, \
    TRANSACTION_ACTION_CAPTURE, TRANSACTION_ACTION_VOID
from application.repositories.order_repository import OrderRepository

from loguru import logger
import shortuuid

from application.repositories.purchase_record_repository import PurchaseRecordRepository
from application.services.task_queue import TaskQueueService


class FulfillOrderController:

    def __init__(self):
        self.order_repo = OrderRepository()
        self.purchase_record_repo = PurchaseRecordRepository()
        self.capture_auth_controller = CaptureAuthController()
        self.void_auth_controller = VoidAuthController()
        self.task_queue = TaskQueueService()

    def process(self, order_id: str) -> None:
        order = self.order_repo.get_by_order_id(
            order_id=order_id
        )

        if order.is_terminal():
            return None
        else:
            self.task_queue.queue_task(message={
                'topic': 'order_fulfillment',
                'data': {
                    'order_id': order.order_id
                }
            })

        if order.is_created():
            self.process_created_order(order=order)
        elif order.is_booked():
            self.process_booked_order(order=order)
        elif order.is_fulfilled():
            self.process_fulfilled_order(order=order)

    def process_created_order(self, order: Order) -> None:
        logger.info("Created order found. Failing the order and void the auth")
        if order.is_over_sla():
            order.fail_incoming_invoice()
            self.order_repo.update_order(order=order)
            self.post_process(order=order)


    def process_booked_order(self, order: Order) -> None:
        purchase_records = [
            self.purchase_record_repo.get_by_id(record_id=record_id) for record_id in order.purchase_record_ids
        ]
        if all([record.is_completed() for record in purchase_records]):
            result_txn = self.capture_auth_controller.process(
                txn=self.generate_transaction_from_order(
                    action=TRANSACTION_ACTION_CAPTURE,
                    amount=order.incoming_invoice.amount,
                    order=order
                )
            )
            if result_txn.is_success():
                order.complete_incoming_invoice()
                self.order_repo.update_order(order=order)
                self.post_process(order=order)
            else:
                order.fail_incoming_invoice()
                self.order_repo.update_order(order=order)
                self.post_process(order=order)
        elif all([record.is_failed() for record in purchase_records]):
            self.void_auth_controller.process(
                txn=self.generate_transaction_from_order(
                    action=TRANSACTION_ACTION_VOID,
                    amount=order.incoming_invoice.amount,
                    order=order
                )
            )
            order.fail_incoming_invoice()
            self.order_repo.update_order(order=order)
            self.post_process(order=order)

        elif order.is_over_sla():
            amount_to_capture = 0
            li_to_refund = []
            for record in purchase_records:
                if record.is_completed():
                    record_amount = sum([li.amount.amount for li in record.line_items])
                    amount_to_capture += record_amount
                else:
                    self.task_queue.queue_task(message={
                        'topic': 'force_fail_purchase_record',
                        'data': {
                            'record_id': record.record_id
                        }
                    })
                    li_to_refund += record.line_items

            result_txn = self.capture_auth_controller.process(
                txn=self.generate_transaction_from_order(
                    action=TRANSACTION_ACTION_CAPTURE,
                    amount=Money(
                        amount=amount_to_capture,
                        currency=order.incoming_invoice.amount.currency
                    ),
                    order=order
                )
            )

            if result_txn.is_success():
                refunding_invoice = Invoice(
                    invoice_name='Refunds',
                    counterparty=order.incoming_invoice.counterparty,
                    type=order.incoming_invoice.type,
                    status=order.incoming_invoice.status,
                    amount=Money(
                        amount=order.incoming_invoice.amount.amount - amount_to_capture,
                        currency=order.incoming_invoice.amount.currency
                    ),
                    instrument_id=order.incoming_invoice.instrument_id,
                    line_items=li_to_refund,
                    parent_transaction_id=order.incoming_invoice.parent_transaction_id,
                )
                order.complete_incoming_invoice()
                order.refunding_invoice = refunding_invoice
                self.order_repo.update_order(order=order)
                self.post_process(order=order)
            else:
                order.fail_incoming_invoice()
                self.order_repo.update_order(order=order)
                self.post_process(order=order)


    def process_fulfilled_order(self, order: Order) -> None:
        self.order.complete_order()
        self.order_repo.update_order(order=order)
        self.post_process(order=order)

    def generate_transaction_from_order(self, action: str, amount: Money, order: Order) -> Transaction:
        try:
            txn_id = shortuuid.uuid()
            return Transaction(
                transaction_id=txn_id,
                parent_transaction_id=order.incoming_invoice.parent_transaction_id,
                order_id=order.order_id,
                instrument_id=order.incoming_invoice.instrument_id,
                action=action,
                status=TRANSACTION_STATUS_CREATED,
                amount=amount,
            )
        except Exception as e:
            raise PaymentCreationError(str(e))

    def post_process(self, order: Order) -> None:
        pass



