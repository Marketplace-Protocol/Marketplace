from typing import Any, Dict

from mongotq import get_task_queue

from application.settings import MONGODB_CONNECT_URL

class TaskQueueService:
    DB_NAME = 'db_marketplace_protocol'
    COLLECTION_NAME = 'TaskQueue'
    HOST = MONGODB_CONNECT_URL

    def __init__(self):
        self.permanent_queue = get_task_queue(
            database_name=self.DB_NAME,
            collection_name=self.COLLECTION_NAME,
            host=self.HOST,
            ttl=-1  # permanent queue
        )

    def queue_task(
            self,
            message: Dict[str, Any],
            ttl: int = -1,
    ) -> None:
        if ttl != -1:
            raise NotImplemented()
        self.permanent_queue.append(message)
        return None

task_queue_service = TaskQueueService()


