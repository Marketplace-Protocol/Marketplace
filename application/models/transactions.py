from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Union

from application.models.money import Money
from application.models.mongo_models import MongoModels

TRANSACTION_ACTION_AUTH = 'AUTH'
TRANSACTION_ACTION_CAPTURE = 'CAPTURE_AUTH'
TRANSACTION_ACTION_VOID = 'VOID_AUTH'
TRANSACTION_ACTION_REFUND = 'REFUND'
TRANSACTION_ACTION_PAYOUT = 'PAYOUT'

TRANSACTION_STATUS_CREATED = 'CREATED'
TRANSACTION_STATUS_PROCESSING = 'PROCESSING'
TRANSACTION_STATUS_COMPLETED = 'COMPLETED'
TRANSACTION_STATUS_FAILED = 'FAILED'
TRANSACTION_STATUS_PROCESSING_FAILED = 'PROCESSING_FAILED'

# actions
TRANSACTION_ACTIONS = [TRANSACTION_ACTION_AUTH, TRANSACTION_ACTION_CAPTURE, TRANSACTION_ACTION_VOID,
                       TRANSACTION_ACTION_REFUND, TRANSACTION_ACTION_PAYOUT]

# statuses
TRANSACTION_STATUSES = [TRANSACTION_STATUS_CREATED, TRANSACTION_STATUS_PROCESSING,
                        TRANSACTION_STATUS_COMPLETED, TRANSACTION_STATUS_FAILED, TRANSACTION_STATUS_PROCESSING_FAILED]

@dataclass
class Transaction(MongoModels):
    transaction_id: str
    parent_transaction_id: str
    order_id: str
    instrument_id: str
    action: str
    status: str
    amount: Money
    provider: Optional[str] = None
    provider_transaction_id: Optional[str] = None
    provider_request: Optional[str] = None
    provider_response: Optional[str] = None
    provider_error_details: Optional[str] = None

    def __post_init__(self) -> None:
        if isinstance(self.amount, dict):
            self.amount = Money(**self.amount)

    def get_id(self) -> Union[str, int]:
        return self.transaction_id

    def has_error(self) -> bool:
        return self.provider_error_details != None

    def is_success(self) -> bool:
        return self.status == TRANSACTION_STATUS_COMPLETED

    def is_declined(self) -> bool:
        return self.status == TRANSACTION_STATUS_FAILED


