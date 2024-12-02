from dataclasses import dataclass
from typing import List, Optional, Union

from application.models.money import Money
from application.models.mongo_models import MongoModels
from application.utils import now_in_epoch_sec

# INCOMING
LINE_ITEM_TYPE_BASE_PRODUCT = 'base-product'
LINE_ITEM_TYPE_ADD_ON_PRODUCT = 'add-on-product'
LINE_ITEM_TYPE_SALES_TAX = 'sales-tax'

# OUTOGING
LINE_ITEM_TYPE_USER_PURCHASES = 'user-purchases'

INCOMING_LINE_ITEM_TYPES = [LINE_ITEM_TYPE_BASE_PRODUCT, LINE_ITEM_TYPE_ADD_ON_PRODUCT,
                            LINE_ITEM_TYPE_SALES_TAX]
OUTGOING_LINE_ITEM_TYPES = [LINE_ITEM_TYPE_USER_PURCHASES]
LINE_ITEM_TYPES = INCOMING_LINE_ITEM_TYPES + OUTGOING_LINE_ITEM_TYPES


INVOICE_TYPE_INCOMING = 'incoming'
INVOICE_TYPE_OUTGOING = 'outoing'
INVOICE_TYPES = [INVOICE_TYPE_INCOMING, INVOICE_TYPE_OUTGOING]

INVOICE_STATUS_CREATED = 'CREATED'      # invoice created
INVOICE_STATUS_PENDING = 'PENDING'      # process complete, start capturing
INVOICE_STATUS_COMPLETED = 'COMPLETED'
INVOICE_STATUS_FAILED = 'FAILED'
INVOICE_STATUSES = [INVOICE_STATUS_CREATED, INVOICE_STATUS_PENDING,
                    INVOICE_STATUS_COMPLETED, INVOICE_STATUS_FAILED]

ORDER_STATUS_CREATED = 'CREATED'        # order created
ORDER_STATUS_BOOKED = 'BOOKED'          # order authorized & record should be processing
ORDER_STATUS_FULFILLED = 'FULFILLED'    # Payin completes, should start payout if applicable
ORDER_STATUS_COMPLETED = 'COMPLETED'    # everything done
ORDER_STATUS_FAILED = 'FAILED'          # failed

@dataclass
class LineItem:
    product_code: str
    product_name: str
    amount: Money
    type: str
    description: Optional[str] = None

    def __post_init__(self) -> None:
        if isinstance(self.amount, dict):
            self.amount = Money(**self.amount)

    def is_base_product(self):
        return self.type == LINE_ITEM_TYPE_BASE_PRODUCT

    def is_add_on_product(self):
        return self.type == LINE_ITEM_TYPE_ADD_ON_PRODUCT

    def is_tax(self):
        return self.type == LINE_ITEM_TYPE_SALES_TAX


@dataclass
class Invoice:
    invoice_name: str
    counterparty: str
    type: str
    status: str
    amount: Money
    instrument_id: str
    line_items: List[LineItem]
    parent_transaction_id: Optional[str] = None

    def __post_init__(self) -> None:
        line_items = []
        for li in self.line_items:
            if isinstance(li, dict):
                line_items.append(LineItem(**li))
        if line_items:
            self.line_items = line_items
        if isinstance(self.amount, dict):
            self.amount = Money(**self.amount)


@dataclass
class Order(MongoModels):
    order_id: str
    user_id: str
    entity: str
    status: str
    created_at: int
    purchase_record_ids: List[str]
    incoming_invoice: Invoice
    outgoing_invoice: Optional[Invoice] = None
    refunding_invoice: Optional[Invoice] = None

    def __post_init__(self) -> None:
        if isinstance(self.incoming_invoice, dict):
            self.incoming_invoice = Invoice(**self.incoming_invoice)
        if self.outgoing_invoice and isinstance(self.outgoing_invoice, dict):
            self.outgoing_invoice = Invoice(**self.outgoing_invoice)

    def get_id(self) -> Union[str, int]:
        return self.order_id

    def is_created(self) -> bool:
        return self.status == ORDER_STATUS_CREATED

    def is_booked(self) -> bool:
        return self.status == ORDER_STATUS_BOOKED

    def is_fulfilled(self) -> bool:
        return self.status == ORDER_STATUS_FULFILLED

    def is_completed(self) -> bool:
        return self.status == ORDER_STATUS_COMPLETED

    def is_failed(self) -> bool:
        return self.status == ORDER_STATUS_FAILED

    def is_terminal(self) -> bool:
        return self.status in [ORDER_STATUS_COMPLETED, ORDER_STATUS_FAILED]

    def is_over_sla(self) -> bool:
        if self.is_terminal():
            return False
        elif self.is_created():
            # No async txn recovery today
            return True
        elif self.is_booked():
            # 24 hrs
            return now_in_epoch_sec() - self.last_updated_at > 60 * 60 * 24

    def fail_incoming_invoice(self) -> None:
        self.incoming_invoice.status = INVOICE_STATUS_FAILED
        self.status = ORDER_STATUS_FAILED

    def complete_incoming_invoice(self) -> None:
        self.incoming_invoice.status = INVOICE_STATUS_COMPLETED
        self.status = ORDER_STATUS_FULFILLED

    def complete_order(self) -> None:
        self.status = ORDER_STATUS_COMPLETED
