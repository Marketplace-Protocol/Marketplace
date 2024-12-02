import json
from flask import Blueprint

offers_blueprint = Blueprint('offers', __name__, url_prefix='/offers')

@offers_blueprint.route("/get", methods=['POST'])
def get_offers():
    """
    requires
    user_id or [order_id]
    Returns
    -------
    order, status of processing, expected time, delivery method
    """
    res = {'hello': 'world'}
    return json.dumps(res), 200