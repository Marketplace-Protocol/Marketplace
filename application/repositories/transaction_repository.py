from typing import List

from application.models.transactions import Transaction
from application.repositories.mongo_repository_base import MongoRepositoryBase


class TransactionRepository(MongoRepositoryBase):

    # test : 9mJWKfSjDNfehfVPWzLw8q
    # child: K4L2mttXfXaDkfVQ4awZmT

    def __init__(self) -> None:
        super().__init__()
        # Single txn table, 1 indexes
        self.transactions_collection = self.db.transactions
        # TODO: Consider persisting as part of transaction document itself
        self.parent_transaction_index = self.db.transaction_parent_transaction_index_collection

    def create_record(self, transaction: Transaction) -> Transaction:
        document = transaction.to_mongo_document()
        self.transactions_collection.insert_one(document)
        self._manage_indexes_write(transaction=transaction)
        return transaction

    def update_record(self, transaction: Transaction) -> Transaction:
        self.transactions_collection.update_one(
            {'_id': transaction.transaction_id},
            {"$set": transaction.to_mongo_document()}
        )
        return transaction

    def get_by_transaction_id(self, transaction_id: str) -> Transaction:
        document = self.transactions_collection.find_one(
            {'_id': transaction_id}
        )
        data_dict = Transaction.get_kwargs_from_mongo_document(document)
        return Transaction(**data_dict)

    def query_by_parent_transaction_id(self, transaction_id: str) -> List[Transaction]:
        child_transactions_doc = self.parent_transaction_index.find_one(
            {'_id': transaction_id}
        )
        if not child_transactions_doc:
            return []

        child_transactions = child_transactions_doc['data']
        return [self.get_by_transaction_id(txn_id) for txn_id in child_transactions]

    def _manage_indexes_write2(self, transaction: Transaction) -> None:
        pass

    def _manage_indexes_write(self, transaction: Transaction) -> None:
        child_transactions_doc = self.parent_transaction_index.find_one(
            {'_id': transaction.parent_transaction_id}
        )

        # New
        if not child_transactions_doc:
            child_transactions = [transaction.transaction_id]
            self.parent_transaction_index.insert_one(
                {
                    '_id': transaction.parent_transaction_id,
                    'data': child_transactions
                }
            )
        # Exists
        else:
            child_transactions = child_transactions_doc['data']
            child_transactions.append(transaction.transaction_id)
            self.parent_transaction_index.update_one(
                {'_id': transaction.parent_transaction_id},
                {"$set": {'data': child_transactions}}
            )

        return None
