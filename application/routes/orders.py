import json
from flask import Blueprint
from flask import request

from application.controllers.orders.create_order_controller import CreateOrderController

orders_blueprint = Blueprint('orders', __name__, url_prefix='/orders')

@orders_blueprint.route("/get", methods=['POST'])
def get_orders():
    """
    requires
    user_id or [order_id]
    Returns
    -------
    order, status of processing, expected time, delivery method
    """
    res = {'hello': 'world'}
    return json.dumps(res), 200

@orders_blueprint.route("/create", methods=['POST'])
def create_order():
    data = request.get_json()
    controller = CreateOrderController()
    res = controller.process(data)
    return json.dumps(res), 200

@orders_blueprint.route("/complete", methods=['POST'])
def complete_order():
    from application.workers.celery_tasks import my_task
    res = {'hello': 'world'}
    data = request.get_json()
    my_task.apply_async(args=[data], countdown=5)
    return json.dumps(res), 200
