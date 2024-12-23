import json
from flask import Blueprint

chargeaccount_blueprint = Blueprint('chargeaccount', __name__, url_prefix='/chargeaccount')

@chargeaccount_blueprint.route("/get", methods=['POST'])
def get_charge_account():
    """
    requires
    user_id or [order_id]
    Returns
    -------
    order, status of processing, expected time, delivery method
    """
    res = {'hello': 'world'}
    return json.dumps(res), 200


@chargeaccount_blueprint.route("/create", methods=['POST'])
def create_charge_account():
    """
    requires
    user_id or [order_id]
    Returns
    -------
    order, status of processing, expected time, delivery method
    """
    res = {'hello': 'world'}
    return json.dumps(res), 200


@chargeaccount_blueprint.route("/get_api_key", methods=['POST'])
def get_api_key():
    """
    requires
    user_id or [order_id]
    Returns
    -------
    order, status of processing, expected time, delivery method
    """
    res = {'hello': 'world'}
    return json.dumps(res), 200

@chargeaccount_blueprint.route("/test_create", methods=['POST'])
def test_create_charge_account():
    """
    requires
    user_id or [order_id]
    Returns
    -------
    order, status of processing, expected time, delivery method
    """
    res = {'hello': 'world'}
    return json.dumps(res), 200