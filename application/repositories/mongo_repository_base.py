from application.settings import MONGODB_CONNECT_URL

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class MongoRepositoryBase:
    def __init__(self) -> None:
        self.client = MongoClient(
            MONGODB_CONNECT_URL,
            server_api=ServerApi('1'),
            ssl = True
        )
        self.db = self.client.db_marketplace_protocol