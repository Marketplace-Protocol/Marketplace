import json
from typing import Any

from loguru import logger

from flask import Blueprint, request, render_template, redirect, url_for, session

from application.controllers.user_session_controller import UserSessionController
from application.decorators import authenticated_required, user_session_management_error_handler
from application.models.user import User, UserAuthAction, LOGIN_METHOD_GOOGLE, LOGIN_METHOD_PASSWORD, LoginUser

user_blueprint = Blueprint('user', __name__, url_prefix='/user')

# User registration
@user_blueprint.route('/signup', methods=['POST'])
@user_session_management_error_handler
def signup():
    data = request.get_json()
    user = User(
        user_id=data['username'],
        username=data['username'],
        email=data['email'],
        password=data['password'],
        first_name=data.get('first_name', None),
        last_name=data.get('last_name', None),
        login_method=LOGIN_METHOD_PASSWORD,
        preferences={}
    )
    result = UserSessionController().process(user=user, user_auth_action=UserAuthAction.SIGNUP)
    # return redirect(url_for('user_dashboard'))
    return json.dumps(result), 200

# User login
@user_blueprint.route('/login', methods=['POST'])
@user_session_management_error_handler
def login():
    data = request.get_json()
    user = LoginUser(
        username=data['username'],
        password=data['password'],
    )
    result = UserSessionController().process(user=user, user_auth_action=UserAuthAction.LOGIN)
    # return redirect(url_for('user_dashboard'))
    return json.dumps(result), 200

@user_blueprint.route('/is_authenticated', methods=['POST'])
@user_session_management_error_handler
@authenticated_required
def is_authenticated():
    return json.dumps({'result': True}), 200

# Logout
@user_blueprint.route('/logout', methods=['POST'])
@authenticated_required
def logout():
    session.pop('user_id', None)
    return json.dumps({'error_details': None}), 200


@user_blueprint.route("/update", methods=['POST'])
@authenticated_required
def update_user():
    res = {'hello': 'world'}
    return json.dumps(res), 200

@user_blueprint.route("/delete", methods=['POST'])
@authenticated_required
def delete_user():
    res = {'hello': 'world'}
    return json.dumps(res), 200


@user_blueprint.route('/login/google')
def google_login():
    from flask import current_app
    google_oauth = current_app.config['GOOGLE_OAUTH']
    redirect_uri = url_for('google_authorize', _external=True)
    return google_oauth.authorize_redirect(redirect_uri)

# Google authorize route
@user_blueprint.route('/login/google/authorize')
def google_authorize():
    from flask import current_app
    google_oauth = current_app.config['GOOGLE_OAUTH']
    token = google_oauth.authorize_access_token()
    resp = google_oauth.get('userinfo')
    user_info = resp.json()
    user = User(
        user_id=user_info['sub'],
        username=user_info['name'],
        email=user_info['email'],
        first_name=user_info['given_name'],
        last_name=user_info['family_name'],
        login_method=LOGIN_METHOD_GOOGLE,
        preferences={}
    )
    UserSessionController().process(user=user, user_auth_action=UserAuthAction.LOGIN)

    return redirect(url_for('user_dashboard'))


# User dashboard (example protected route)
@user_blueprint.route('/dashboard', methods=['POST'])
@authenticated_required
def user_dashboard():
    data = request.get_json()
    user_id = data['user_id']
    return json.dumps({}), 200