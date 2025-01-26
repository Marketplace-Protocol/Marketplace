import json
from flask import Blueprint
from flask import request

from application.controllers.purchase_intent_controller import PurchaseIntentController
from application.decorators import purchase_intent_error_handler
from application.repositories.digitalocean_spaces import DigitalOceanSpaces
from application.repositories.purchase_record_repository import PurchaseRecordRepository


purchase_intent_blueprint = Blueprint('purchase_intent', __name__, url_prefix='/purchase_intent')


@purchase_intent_blueprint.route("/get", methods=['POST'])
@purchase_intent_error_handler
def get():
    data = request.get_json()
    result = PurchaseIntentController(
        digitalocean_spaces=DigitalOceanSpaces(),
        purchase_record_repo=PurchaseRecordRepository()
    ).get(request=data)
    return json.dumps(result), 200


@purchase_intent_blueprint.route("/create", methods=['POST'])
@purchase_intent_error_handler
def create():
    data = request.get_json()
    result = PurchaseIntentController(
        digitalocean_spaces=DigitalOceanSpaces(),
        purchase_record_repo=PurchaseRecordRepository()
    ).create(request=data)
    return json.dumps(result), 200