from typing import Optional, List

from application.models.order import LineItem
from application.models.purchase_record import PurchaseRecord
from application.utils import now_in_epoch_sec


def generate_mock_purchase_record(
        record_id: str = 'test_record_id',
        created_at: int = now_in_epoch_sec(),
        last_updated_at: int = now_in_epoch_sec(),
        description: str = 'description',
        user_id: str = 'user_id',
        entity: str = 'PrivatEdit',
        status: str = 'CREATED',
        attempt_count: int = 1,
        order_id: Optional[str] = None,
        line_items: List[LineItem] = [],
        progress_note: List[str] = []
) -> PurchaseRecord:

    return PurchaseRecord(
        record_id=record_id,
        created_at=created_at,
        last_updated_at=last_updated_at,
        description=description,
        user_id=user_id,
        entity=entity,
        status=status,
        attempt_count=attempt_count,
        order_id=order_id,
        line_items=line_items,
        progress_note=progress_note
    )
