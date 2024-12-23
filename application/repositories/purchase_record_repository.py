from typing import List

from application.errors import DataNotFound
from application.models.purchase_record import PurchaseRecord
from application.repositories.mongo_repository_base import MongoRepositoryBase
from application.utils import now_in_epoch_sec


class PurchaseRecordRepository(MongoRepositoryBase):
    def __init__(self) -> None:
        super().__init__()
        self.purchase_records_collection = self.db.purchase_records
        self.user_id_index = self.db.purchase_records_user_id_index

    def create_record(self, record: PurchaseRecord) -> PurchaseRecord:
        document = record.to_mongo_document()
        self.purchase_records_collection.insert_one(document)
        self._manage_indexes_write(record=record)
        return record

    def update_record(self, record: PurchaseRecord) -> PurchaseRecord:
        record.updated_at = now_in_epoch_sec()
        self.purchase_records_collection.update_one(
            {'_id': record.record_id},
            {"$set": record.to_mongo_document()}
        )
        return record

    def get_by_id(self, record_id: str) -> PurchaseRecord:
        document = self.purchase_records_collection.find_one(
            {'_id': record_id}
        )
        if not document:
            raise DataNotFound()
        data_dict = PurchaseRecord.get_kwargs_from_mongo_document(document)
        return PurchaseRecord(**data_dict)

    def query_by_user_id(self, user_id: str) -> List[PurchaseRecord]:
        purchase_record_index_doc = self.user_id_index.find_one(
            {'_id': user_id}
        )
        if not purchase_record_index_doc:
            return []

        purchase_record_ids = purchase_record_index_doc['data']
        return [self.get_by_id(purchase_record_id) for purchase_record_id in purchase_record_ids]

    def _manage_indexes_write(self, record: PurchaseRecord) -> None:
        user_record_doc = self.user_id_index.find_one(
            {'_id': record.user_id}
        )

        # New
        if not user_record_doc:
            user_purchase_records = [record.record_id]
            self.user_id_index.insert_one(
                {
                    '_id': record.user_id,
                    'data': user_purchase_records
                }
            )
        # Exists
        else:
            user_purchase_records = user_record_doc['data']
            user_purchase_records.append(record.record_id)
            self.user_id_index.update_one(
                {'_id': record.user_id},
                {"$set": {'data': user_purchase_records}}
            )

        return None