from typing import List

from application.controllers.orders.order_base_controller import OrderBaseController
from application.controllers.purchase_record_controller import PurchaseRecordController
from application.controllers.transactions.create_transaction_controller import CaptureAuthController, \
    VoidAuthController, CreateAuthController
from application.errors import PaymentCreationError, UserActionRequiredError, OrderProcessing, UnexpectedStatus, \
    OrderFulfilled
from application.models.money import Money
from application.models.order import Order, Invoice
from application.models.purchase_record import PurchaseRecord, PURCHASE_RECORD_FAILED
from application.models.transactions import Transaction, TRANSACTION_STATUS_CREATED, \
    TRANSACTION_ACTION_CAPTURE, TRANSACTION_ACTION_VOID
from application.repositories.order_repository import OrderRepository

from loguru import logger
import shortuuid

from application.repositories.purchase_record_repository import PurchaseRecordRepository
from application.services.task_queue import TaskQueueService


class FulfillOrderController(OrderBaseController):

    def __init__(self):
        self.order_repo = OrderRepository()
        self.purchase_record_repo = PurchaseRecordRepository()
        self.capture_auth_controller = CaptureAuthController()
        self.create_auth_controller = CreateAuthController()
        self.void_auth_controller = VoidAuthController()
        self.task_queue = TaskQueueService()
        super().__init__(
            order_repo=self.order_repo,
            purchase_record_controller=PurchaseRecordController()
        )

    def process(self, order_id: str) -> None:
        logger.info("Order Fulfillment triggered", kv={
            'order_id': order_id
        })
        order = self.order_repo.get_by_order_id(
            order_id=order_id
        )

        if order.is_terminal():
            logger.info("Order in terminal state", kv={
                'order_id': order.order_id
            })

        purchase_records = [
            self.purchase_record_repo.get_by_id(record_id=record_id) for record_id in order.purchase_record_ids
        ]

        logger.info("Retrieved order to fulfill", kv={
            'order_id': order.order_id,
            'record_ids': [record.record_id for record in purchase_records],
            'order_status': order.status,
            'parent_transaction_id': order.incoming_invoice.parent_transaction_id,
            'is_over_sla': order.is_over_sla()
        })

        if order.is_created():
            self.process_created_order(order=order, purchase_records=purchase_records)
            logger.info("Created order fulfillment executed", kv={
                'order_id': order.order_id,
                'order_status': order.status,
            })

        if order.is_booked():
            self.process_booked_order(order=order, purchase_records=purchase_records)
            logger.info("Booked order fulfillment executed", kv={
                'order_id': order.order_id,
                'order_status': order.status,
            })

        if order.is_fulfilled():
            self.process_fulfilled_order(order=order)
            logger.info("Fulfilled order fulfillment executed", kv={
                'order_id': order.order_id,
                'order_status': order.status,
            })

        if order.is_terminal():
            self.post_process_order(order=order)
            logger.info("Completed order fulfillment executed", kv={
                'order_id': order.order_id,
                'order_status': order.status,
            })

    def process_created_order(
            self,
            order: Order,
            purchase_records: List[PurchaseRecord]
    ) -> None:
        parent_txn_id = order.incoming_invoice.parent_transaction_id
        if order.is_over_sla() or not parent_txn_id:
            order.fail_incoming_invoice()
            self.order_repo.update_order(order=order)
        else:
            result_txn = self.create_auth_controller.reprocess(
                txn_id=parent_txn_id
            )
            result_order = self.post_payment_process(
                txn=result_txn, order=order
            )
            self.post_order_processing(
                order=result_order, purchase_records=purchase_records
            )

    def process_booked_order(
            self,
            order: Order,
            purchase_records: List[PurchaseRecord]
    ) -> None:
        if all([record.is_completed() for record in purchase_records]):
            logger.info("Processing purchase records success!", kv={
                'order_id': order.order_id,
                'record_ids': [record.record_id for record in purchase_records],
            })
            result_txn = self.capture_auth_controller.process(
                txn=self.generate_transaction_from_order(
                    action=TRANSACTION_ACTION_CAPTURE,
                    amount=order.incoming_invoice.amount,
                    order=order
                )
            )
            result_order = self.post_payment_process(
                txn=result_txn, order=order
            )
            self.post_order_processing(
                order=result_order, purchase_records=purchase_records
            )
        elif all([record.is_failed() for record in purchase_records]):
            logger.info("Processing purchase records failed", kv={
                'order_id': order.order_id,
                'record_ids': [record.record_id for record in purchase_records],
            })
            result_txn = self.void_auth_controller.process(
                txn=self.generate_transaction_from_order(
                    action=TRANSACTION_ACTION_VOID,
                    amount=order.incoming_invoice.amount,
                    order=order
                )
            )
            result_order = self.post_payment_process(
                txn=result_txn, order=order
            )
            self.post_order_processing(
                order=result_order, purchase_records=purchase_records
            )
        # SLA over
        elif order.is_over_sla():
            logger.info("Order over SLA", kv={
                'order_id': order.order_id,
                'record_ids': [record.record_id for record in purchase_records],
            })
            amount_to_capture = 0
            li_to_refund = []
            for record in purchase_records:
                if record.is_completed():
                    logger.info("Processing purchase records success!", kv={
                        'order_id': order.order_id,
                        'record_id': record.record_id,
                    })
                    record_amount = sum([li.amount.amount for li in record.line_items])
                    amount_to_capture += record_amount
                else:
                    logger.info("Processing order over SLA", kv={
                        'order_id': order.order_id,
                        'record_id': record.record_id,
                    })
                    self.task_queue.force_complete_purchase_record(
                        payload={
                            'record_id': record.record_id,
                            'status': PURCHASE_RECORD_FAILED
                        }
                    )
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

            result_order = self.post_payment_process(
                txn=result_txn, order=order
            )

            if result_txn.is_success():
                refunding_invoice = Invoice(
                    invoice_name='Refunds',
                    counterparty=result_order.incoming_invoice.counterparty,
                    type=result_order.incoming_invoice.type,
                    status=result_order.incoming_invoice.status,
                    amount=Money(
                        amount=result_order.incoming_invoice.amount.amount - amount_to_capture,
                        currency=result_order.incoming_invoice.amount.currency
                    ),
                    instrument_id=result_order.incoming_invoice.instrument_id,
                    line_items=li_to_refund,
                    parent_transaction_id=result_order.incoming_invoice.parent_transaction_id,
                )
                result_order.refunding_invoice = refunding_invoice
                self.order_repo.update_order(order=result_order)


    def process_fulfilled_order(self, order: Order) -> None:
        # Send user success msg
        self.order.complete_order()
        self.order_repo.update_order(order=order)

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

    def post_process_order(self, order: Order) -> None:
        if order.is_terminal():
            pass
        else:
            schedule = order.next_recovery_schedule()
            raise OrderProcessing(schedule=schedule)




fulfill_order_controller = FulfillOrderController()