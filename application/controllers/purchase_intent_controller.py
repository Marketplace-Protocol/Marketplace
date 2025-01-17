import shortuuid
from typing import Any, List

from loguru import logger

from application.errors import ValidationError
from application.models.order import LineItem
from application.models.purchase_record import PurchaseRecord, PURCHASE_RECORD_CREATED
from application.utils import now_in_epoch_sec


class PurchaseIntentController:
    def create_intent(self, request: Any) -> Any:
        """
        Create intent of purchase. This function generates record ID, persist the intent of purchase,
        pre-sign url for storage provider, etc

        Args: userID (Optional), entity, line items, product details (json dumped)

        Returns
        -------

        """
        try:
            purchase_records = self.generate_purchase_records(request=request)
            [self.validate_context(purchase_record=purchase_record) for purchase_record in purchase_records]
            logger.info('Purchase Record generated', kv={
                'record_ids': [record.record_id for record in purchase_records],
                'user_id': request['user_id'],
            })
        except Exception:
            pass

    def generate_purchase_records(self, request: Any) -> List[PurchaseRecord]:
        try:
            purchase_list = []
            purchases = request['purchases']
            for purchase in purchases:
                item = PurchaseRecord(
                    record_id=shortuuid.uuid(),
                    created_at=now_in_epoch_sec(),
                    last_updated_at=now_in_epoch_sec(),
                    description=purchase['description'],
                    user_id=request['user_id'],
                    entity=purchase['entity'],
                    status=PURCHASE_RECORD_CREATED,
                    attempt_count=1,
                    order_id=None,
                    line_items=[LineItem(**line_item) for line_item in purchase.get('line_items')],
                    progress_note=[]
                )
                purchase_list.append(item)
            return purchase_list
        except Exception as e:
            raise ValidationError(str(e))
