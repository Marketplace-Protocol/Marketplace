from typing import Optional

import shortuuid

from application.models.money import Money
from application.models.transactions import Transaction, TRANSACTION_STATUS_CREATED, TRANSACTION_ACTION_AUTH, \
    TRANSACTION_ACTION_CAPTURE


def generate_mock_auth_transaction_object() -> Transaction:
    test_txn_id = shortuuid.uuid()
    return Transaction(
        transaction_id=test_txn_id,
        parent_transaction_id=test_txn_id,
        order_id=shortuuid.uuid(),
        instrument_id=shortuuid.uuid(),
        action=TRANSACTION_ACTION_AUTH,
        status=TRANSACTION_STATUS_CREATED,
        amount=Money(
            amount=2000,
            currency='USD',
            exponent=2
        )
    )

def generate_mock_capture_transaction_object(
        transaction_id: str = shortuuid.uuid(),
        parent_transaction_id: str = shortuuid.uuid(),
        status: str = TRANSACTION_STATUS_CREATED
) -> Transaction:
    return Transaction(
        transaction_id=transaction_id,
        parent_transaction_id=parent_transaction_id,
        order_id=shortuuid.uuid(),
        instrument_id=shortuuid.uuid(),
        action=TRANSACTION_ACTION_CAPTURE,
        status=status,
        amount=Money(
            amount=2000,
            currency='USD',
            exponent=2
        )
    )