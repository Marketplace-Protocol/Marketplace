import json
from dataclasses import asdict

from flask import Blueprint
from flask import request

from application.models.instrument import Instrument, ProviderToken
from application.repositories.wallet_repository import WalletRepository

wallet_blueprint = Blueprint('instrument', __name__, url_prefix='/instrument')

@wallet_blueprint.route("/create_charge_account", methods=['POST'])
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

@wallet_blueprint.route("/test_create_charge_account", methods=['POST'])
def test_create_charge_account():
    """
    requires
    user_id or [order_id]
    Returns
    -------
    order, status of processing, expected time, delivery method
    """
    data = request.get_json()
    res = {'hello': data}
    instrument = Instrument(
        instrument_id='test1',
        user_id='test',
        usage='payin',
        payment_method='card',
        tokens=[
            ProviderToken(
                provider='stripe',
                token='pm_1QRNHGP3V4jaay2EQFSrlWTS',
                customer_id="cus_RK1JvgMevvSKVu"
            )
        ]
    )
    wallet_repo = WalletRepository()
    instrument = wallet_repo.create_record(instrument)
    return json.dumps(asdict(instrument)), 200

@wallet_blueprint.route("/delete_charge_account", methods=['POST'])
def delete_charge_account():
    res = {'hello': 'world'}
    return json.dumps(res), 200
