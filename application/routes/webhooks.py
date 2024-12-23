import json

from flask import Blueprint
from flask import request

from application.decorators import stripe_webhook_error_handler
from application.providers.stripe.stripe_webhook_provider import stripe_webhook_provider

webhooks_blueprint = Blueprint('webhooks', __name__, url_prefix='/webhooks')

@webhooks_blueprint.route("/stripe", methods=['POST'])
@stripe_webhook_error_handler
def handle_stripe_webhooks():
    """
    requires
    user_id or [order_id]
    Returns
    -------
    order, status of processing, expected time, delivery method
    """
    stripe_webhook_provider.process(webhook=request)
    res = {'status': 'success'}
    return json.dumps(res), 200
