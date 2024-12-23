from typing import List

from application.controllers.purchase_record_controller import PurchaseRecordController
from application.models.order import Order
from application.models.purchase_record import PurchaseRecord, PURCHASE_RECORD_READY, PURCHASE_RECORD_CREATED, \
    PURCHASE_RECORD_FAILED
from application.models.transactions import Transaction
from application.repositories.order_repository import OrderRepository


class OrderBaseController:

    def __init__(
            self,
            order_repo: OrderRepository,
            purchase_record_controller: PurchaseRecordController
    ) -> None:
        self.order_repo = order_repo
        self.purchase_record_controller = purchase_record_controller

    def post_payment_process(
            self,
            txn: Transaction,
            order: Order,
    ) -> Order:
        if txn.is_auth():
            return self.post_auth_payment_processing(
                txn=txn, order=order
            )
        elif txn.is_capture_auth():
            return self.post_capture_payment_processing(
                txn=txn, order=order
            )
        elif txn.is_void_auth():
            return self.post_void_payment_processing(
                txn=txn, order=order
            )

    def post_capture_payment_processing(
            self,
            txn: Transaction,
            order: Order,
    ) -> Order:
        # Post payin
        if txn.is_success():
            # capture success
            order.complete_incoming_invoice()
            self.order_repo.update_order(order=order)
        elif txn.is_declined():
            order.fail_incoming_invoice()
            self.order_repo.update_order(order=order)
        elif txn.is_created():
            pass
        elif txn.is_processing():
            pass
        elif txn.is_processing_failed():
            order.fail_incoming_invoice()
            self.order_repo.update_order(order=order)

        return order

    def post_void_payment_processing(
            self,
            txn: Transaction,
            order: Order,
    ) -> Order:
        order.fail_incoming_invoice()
        self.order_repo.update_order(order=order)
        return order

    def post_auth_payment_processing(
            self,
            txn: Transaction,
            order: Order,
    ) -> Order:
        order.incoming_invoice.parent_transaction_id = txn.parent_transaction_id
        # Post payin
        if txn.is_success():
            # Auth success
            order.on_auth_success()
        elif txn.is_declined():
            order.fail_incoming_invoice()
        elif txn.is_created():
            pass
        elif txn.is_processing():
            pass
        elif txn.is_processing_failed():
            order.fail_incoming_invoice()
        self.order_repo.update_order(order=order)
        return order

    def post_order_processing(
            self,
            order: Order,
            purchase_records: List[PurchaseRecord]
    ) -> None:

        if order.is_created():
            for record in purchase_records:
                # If not already created?
                record.status = PURCHASE_RECORD_CREATED
                self.purchase_record_controller.process(record=record)

        elif order.is_booked():
            for record in purchase_records:
                # If not already booked?
                record.status = PURCHASE_RECORD_READY
                record.order_id = order.order_id
                self.purchase_record_controller.process(record=record)

        elif order.is_failed():
            pass
            # for record in purchase_records:
            #     # If not already failed?
            #     record.status = PURCHASE_RECORD_FAILED
            #     self.purchase_record_controller.process(record=record)

        elif order.is_completed():
            pass

        elif order.is_fulfilled():
            pass
