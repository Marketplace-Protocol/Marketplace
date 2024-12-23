from flask import g
from loguru import logger
from app import celery_app  # Import your Celery app

from application.controllers.orders.fulfill_order_controller import fulfill_order_controller
from application.errors import DataNotFound, PaymentContextValidationError, UserActionRequiredError, OrderProcessing, \
    OrderFulfilled, UnexpectedStatus

ORDER_FULFILLMENT_AUTO_RETRY = [

]


@celery_app.task(name='workers.celery_tasks.fulfill_order')
def fulfill_order(data):
    try:
        logger.info("fulfill_order received")
        fulfill_order_controller.process(
            order_id=data['order_id']
        )
        logger.info("fulfill_order completed")
    except (DataNotFound, PaymentContextValidationError, UnexpectedStatus) as exc:
        # Permafail
        raise fulfill_order.retry(exc=exc, max_retries=0)
    except OrderProcessing as exc:
        schedule = exc.get_next_schedule()
        raise fulfill_order.retry(exc=exc, countdown=schedule)
    except Exception as exc:
        logger.info("fulfill_order failed")
        logger.info(str(exc))
        raise fulfill_order.retry(exc=exc, countdown=60 * 60)


@celery_app.task(name='workers.celery_tasks.force_complete_purchase_record')
def force_complete_purchase_record(data):
    logger.info("force_complete_purchase_record received", kv={
        'record_id': data['record_id']
    })
    return 200