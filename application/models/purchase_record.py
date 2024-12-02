import time

from dataclasses import dataclass
from typing import Optional, Union, Dict, List

from application.models.mongo_models import MongoModels
from application.models.order import LineItem
from application.utils import now_in_epoch_sec

PURCHASE_RECORD_CREATED = 'CREATED'
PURCHASE_RECORD_READY = 'READY'
PURCHASE_RECORD_PROCESSING = 'PROCESSING'
PURCHASE_RECORD_COMPLETED = 'COMPLETED'
PURCHASE_RECORD_FAILED = 'FAILED'

PURCHASE_RECORD_STATUSES = [
    PURCHASE_RECORD_CREATED,
    PURCHASE_RECORD_READY,
    PURCHASE_RECORD_PROCESSING,
    PURCHASE_RECORD_COMPLETED,
    PURCHASE_RECORD_FAILED
]

# Created -> ready: by payment update
# ready -> processing: network / load balance availability
# processing -> completed: queued call to/from service
# processing -> failed: queued call to service or sla

@dataclass
class PurchaseRecord(MongoModels):
    record_id: str
    created_at: int
    last_updated_at: int
    description: str
    user_id: str
    entity: str
    status: str
    attempt_count: int
    line_items: List[LineItem]
    progress_note: List[str]
    order_id: Optional[str] = None

    def __post_init__(self) -> None:
        line_items = []
        for li in self.line_items:
            if isinstance(li, dict):
                line_items.append(LineItem(**li))
        if line_items:
            self.line_items = line_items

    def get_id(self) -> Union[str, int]:
        return self.record_id

    def is_terminal(self):
        return self.status in [
            PURCHASE_RECORD_COMPLETED,
            PURCHASE_RECORD_FAILED
        ]

    def is_created(self):
        return self.status == PURCHASE_RECORD_CREATED

    def is_ready(self):
        return self.status == PURCHASE_RECORD_READY

    def is_processing(self):
        return self.status == PURCHASE_RECORD_PROCESSING

    def is_completed(self):
        return self.status == PURCHASE_RECORD_COMPLETED

    def is_failed(self):
        return self.status == PURCHASE_RECORD_FAILED

    def is_over_sla(self) -> bool:
        if self.is_terminal():
            return False
        elif self.is_created():
            # Auth to be acquired in 0 hrs. change to 3 once webhook is ready on pay stack
            return now_in_epoch_sec() - self.last_updated_at > 60 * 60 * 0
        elif self.is_ready():
            # Queue to be cleared in 3 hrs
            return now_in_epoch_sec() - self.last_updated_at > 60 * 60 * 3
        elif self.is_processing():
            # 17 hrs for processing
            return now_in_epoch_sec() - self.last_updated_at > 60 * 60 * 17

    def current_progress_note_update(self) -> str:
        if self.is_created():
            return "Your order is created. We are processing your payments..."
        elif self.is_ready():
            return ("Payment has been completed. We started processing your order.... \n"
                    "In the case of execution failure, we will immediately refund in full.")
        elif self.is_processing():
            return "Execution in progress....."
        elif self.is_completed():
            return ("Execution succeeded! You should have received your output. \n"
                    "Please reach out if you still do not see the result.")
        else:
            return "Processing failed. Money will be returned to your account immediately."

    def generate_line_items(self) -> List[LineItem]:
        # TODO Should come from runtime that maps product details to line item
        if not self.product_details:
            return []

    def product_name(self) -> str:
        name = ''
        has_add_on = False
        for li in self.line_items:
            if li.is_base_product():
                name = li.product_name
            elif li.is_add_on_product():
                has_add_on = True

        if has_add_on:
            name += ' with add-ons'

        return name






