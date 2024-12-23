from locale import currency
from typing import List, Optional

from application.models.money import Money
from application.models.order import Order, LineItem, Invoice
from application.utils import now_in_epoch_sec


def generate_mock_line_items(
        product_code: str = 'product_code',
        product_name: str = 'product_name',
        amount: Money = Money(
            amount=2000,
            currency='USD',
            exponent=2
        ),
        type: str = 'user_purchase',
        description: str = 'description'
) -> LineItem:
    return LineItem(
        product_code=product_code,
        product_name=product_name,
        amount=amount,
        type=type,
        description=description,
    )

def generate_mock_invoice(
        invoice_name: str = 'invoice_name',
        counterparty: str = 'counterparty',
        type: str = 'incoming',
        status: str = 'CREATED',
        amount: Money = Money(
            amount=2000,
            currency='USD',
            exponent=2
        ),
        instrument_id: str = 'instrument_id',
        line_items: List[LineItem] = [generate_mock_line_items()],
        parent_transaction_id: Optional[int] = 'parent_transaction_id'
) -> Invoice:
    return Invoice(
        invoice_name=invoice_name,
        counterparty=counterparty,
        type=type,
        status=status,
        amount=amount,
        instrument_id=instrument_id,
        line_items=line_items,
        parent_transaction_id=parent_transaction_id
    )

def generate_mock_order_object(
        order_id: str = 'test_order_id',
        user_id: str = 'test_order_id',
        entity: str = 'test_order_id',
        status: str = 'CREATED',
        created_at: int = now_in_epoch_sec(),
        purchase_record_ids: List[str] = [],
        incoming_invoice: Invoice = generate_mock_invoice(),
        outgoing_invoice: Optional[Invoice] = None
) -> Order:
    return Order(
        order_id=order_id,
        user_id=user_id,
        entity=entity,
        status=status,
        created_at=created_at,
        purchase_record_ids=purchase_record_ids,
        incoming_invoice=incoming_invoice,
        outgoing_invoice=outgoing_invoice,
    )