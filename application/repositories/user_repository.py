from application.errors import DataNotFound
from application.models.user import User
from application.repositories.mongo_repository_base import MongoRepositoryBase



class UserRepository(MongoRepositoryBase):

    def __init__(self) -> None:
        super().__init__()
        self.user_collection = self.db.users

    def create(self, user: User) -> User:
        document = user.to_mongo_document()
        self.user_collection.insert_one(document)
        return user

    def update_record(self, user: User) -> User:
        self.user_collection.update_one(
            {'_id': user.user_id},
            {"$set": user.to_mongo_document()}
        )
        return user

    def get_by_id(self, user_id: str) -> User:
        document = self.user_collection.find_one(
            {'_id': user_id}
        )
        if not document:
            raise DataNotFound()
        data_dict = User.get_kwargs_from_mongo_document(document)
        return User(**data_dict)