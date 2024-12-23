from typing import Any, Dict


class TaskQueueService:

    def queue_order_fulfillment(
            self,
            payload: Dict[str, Any],
            delay: int = 30,
    ) -> None:
        from application.workers.celery_tasks import fulfill_order
        fulfill_order.apply_async(args=[payload], countdown=delay)


    def force_complete_purchase_record(
            self,
            payload: Dict[str, Any],
            delay: int = 5,
    ) -> None:
        from application.workers.celery_tasks import force_complete_purchase_record
        force_complete_purchase_record.apply_async(args=[payload], countdown=delay)

task_queue_service = TaskQueueService()


