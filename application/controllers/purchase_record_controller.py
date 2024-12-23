import time

from application.errors import DataNotFound
from application.models.purchase_record import PurchaseRecord, PURCHASE_RECORD_FAILED
from application.repositories.purchase_record_repository import PurchaseRecordRepository
# from application.services.task_queue import TaskQueueService


class PurchaseRecordController:

    def __init__(self):
        self.purchase_record_repo = PurchaseRecordRepository()
        # self.task_queue_service = TaskQueueService()

    def process(self, record: PurchaseRecord) -> PurchaseRecord:
        try:
            stale_record = self.purchase_record_repo.get_by_id(record_id=record.record_id)
            if record.status != stale_record.status:
                self.purchase_record_repo.update_record(record=record)
        except DataNotFound:
            self.purchase_record_repo.create_record(record=record)

        if record.is_created() or record.is_terminal():
            return record
        return self._fulfill_purchase_record(
            current_record=record
        )

    def reprocess(self, record_id: str) -> None:
        record = self.purchase_record_repo.get_by_id(record_id=record_id)
        self._fulfill_purchase_record(
            current_record=record
        )

    def _fulfill_purchase_record(self, current_record: PurchaseRecord) -> PurchaseRecord:
        try:
            # self.task_queue_service.queue_task()
            # Update with latest progress if applicable
            updated_record = self._update_with_latest(current_record=current_record)

            # If over sla, fail the record
            if not updated_record.is_terminal() and updated_record.is_over_sla():
                updated_record.status = PURCHASE_RECORD_FAILED
                updated_record.last_updated_at = int(time.time())

            # Call the product service here

            # Save
            self.purchase_record_repo.update_record(record=updated_record)

            # Send user notification
            if updated_record.is_terminal():
                self._post_prcess(record=updated_record)
            else:
                self._queue_recovery_task(record_id=updated_record.record_id)

            return updated_record
        except Exception:
            self._queue_recovery_task(record_id=current_record.record_id)

    def _post_prcess(self, record: PurchaseRecord) -> None:
        pass

    def _queue_recovery_task(self, record_id: str) -> None:
        pass

    def _update_with_latest(self, current_record: PurchaseRecord) -> PurchaseRecord:
        current_note = current_record.progress_note
        # If no update, then noop
        if current_note and current_note[len(current_note) - 1] == current_record.current_progress_note_update():
            return current_record
        else:
            current_note.append(
                current_record.current_progress_note_update()
            )
            return current_record