from typing import List

from application.errors import DataNotFound
from application.models.order import Order
from application.repositories.mongo_repository_base import MongoRepositoryBase
from application.utils import now_in_epoch_sec


class OrderRepository(MongoRepositoryBase):
    def __init__(self) -> None:
        super().__init__()
        self.order_collection = self.db.orders
        self.user_id_index = self.db.order_user_index

    def create_order(self, order: Order) -> Order:
        document = order.to_mongo_document()
        self.order_collection.insert_one(document)
        self._manage_indexes_write(order=order)
        return order

    def update_order(self, order: Order) -> Order:
        order.updated_at = now_in_epoch_sec()
        self.order_collection.update_one(
            {'_id': order.order_id},
            {"$set": order.to_mongo_document()}
        )
        return order

    def get_by_order_id(self, order_id: str) -> Order:
        document = self.order_collection.find_one(
            {'_id': order_id}
        )
        if not document:
            raise DataNotFound()
        data_dict = Order.get_kwargs_from_mongo_document(document)
        return Order(**data_dict)

    def query_by_user_id(self, user_id: str) -> List[Order]:
        user_index_doc = self.user_id_index.find_one(
            {'_id': user_id}
        )
        if not user_index_doc:
            return []

        user_order_ids = user_index_doc['data']
        return [self.get_by_order_id(order_id) for order_id in user_order_ids]

    def _manage_indexes_write(self, order: Order) -> None:
        user_index_doc = self.user_id_index.find_one(
            {'_id': order.user_id}
        )

        # New
        if not user_index_doc:
            user_orders = [order.order_id]
            self.user_id_index.insert_one(
                {
                    '_id': order.user_id,
                    'data': user_orders
                }
            )
        # Exists
        else:
            user_orders = user_index_doc['data']
            user_orders.append(order.order_id)
            self.user_id_index.update_one(
                {'_id': order.user_id},
                {"$set": {'data': user_orders}}
            )

        return None