from typing import List

from application.models.instrument import Instrument
from application.repositories.mongo_repository_base import MongoRepositoryBase

from loguru import logger


class WalletRepository(MongoRepositoryBase):

    def __init__(self) -> None:
        super().__init__()
        self.wallet_collection = self.db.wallet
        self.user_id_index = self.db.wallet_user_id_index_collection

    def create_record(self, instrument: Instrument) -> Instrument:
        document = instrument.to_mongo_document()
        logger.info(document)
        self.wallet_collection.insert_one(document)
        self._manage_indexes_write(instrument=instrument)
        return instrument

    def update_record(self, instrument: Instrument) -> Instrument:
        self.wallet_collection.update_one(
            {'_id': instrument.instrument_id},
            {"$set": instrument.to_mongo_document()}
        )
        return instrument

    def get_by_instrument_id(self, instrument_id: str) -> Instrument:
        document = self.wallet_collection.find_one(
            {'_id': instrument_id}
        )
        data_dict = Instrument.get_kwargs_from_mongo_document(document)
        return Instrument(**data_dict)

    def query_by_user_id(self, user_id: str) -> List[Instrument]:
        document = self.user_id_index.find_one(
            {'_id': user_id}
        )
        if not document:
            return []

        user_instrument_ids = document['data']
        return [self.get_by_instrument_id(instrument_id) for instrument_id in user_instrument_ids]

    def _manage_indexes_write(self, instrument: Instrument) -> None:
        user_instruments_document = self.user_id_index.find_one(
            {'_id': instrument.user_id}
        )

        # New
        if not user_instruments_document:
            user_instruments = [instrument.instrument_id]
            self.user_id_index.insert_one(
                {
                    '_id': instrument.user_id,
                    'data': user_instruments
                }
            )
        # Exists
        else:
            user_instruments = user_instruments_document['data']
            user_instruments.append(instrument.instrument_id)
            self.user_id_index.update_one(
                {'_id': instrument.user_id},
                {"$set": {'data': user_instruments}}
            )

        return None
