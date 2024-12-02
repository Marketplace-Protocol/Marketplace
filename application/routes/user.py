import json
from flask import Blueprint

user_blueprint = Blueprint('user', __name__, url_prefix='/user')

@user_blueprint.route("/get", methods=['POST'])
def get_user():
    """
    """
    res = {'hello': 'world'}
    return json.dumps(res), 200

@user_blueprint.route("/create", methods=['POST'])
def create_user():
    res = {'hello': 'world'}
    return json.dumps(res), 200

@user_blueprint.route("/update", methods=['POST'])
def update_user():
    res = {'hello': 'world'}
    return json.dumps(res), 200

@user_blueprint.route("/update", methods=['POST'])
def delete_user():
    res = {'hello': 'world'}
    return json.dumps(res), 200
