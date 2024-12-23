import json

from flask import Blueprint, request

from loguru import logger

from application.controllers.generate_offer_controller import GenerateOfferController
from application.decorators import offer_generation_error_handler

offers_blueprint = Blueprint('offer', __name__, url_prefix='/offer')

@offers_blueprint.route("/generate", methods=['POST'])
@offer_generation_error_handler
def generate_offers():
    """
    requires
    user_id or [order_id]
    Returns
    -------
    order, status of processing, expected time, delivery method
    """
    data = request.get_json()
    logger.info(data)
    result = GenerateOfferController().process(request=data)
    return json.dumps(result), 200




