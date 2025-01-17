import json
from flask import Blueprint
from flask import request

from application.controllers.orders.create_order_controller import CreateOrderController

purchase_intent_blueprint = Blueprint('purchase_intent', __name__, url_prefix='/purchase_intent')

@purchase_intent_blueprint.route("/get", methods=['POST'])
def get_purchase_intent():
    res = {'hello': 'world'}
    return json.dumps(res), 200

@purchase_intent_blueprint.route("/create", methods=['POST'])
def create_purchase_intent():
    # validate purchase intent and contents
    # hash ID
    # persist purchase record - created
    # pre-signed URL for uploading to storage

    data = request.get_json()
    controller = CreateOrderController()
    res = controller.process(data)
    return json.dumps(res), 200