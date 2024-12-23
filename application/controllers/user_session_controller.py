import copy
from dataclasses import asdict
from typing import Any, Union

from loguru import logger

from flask import session
from application.errors import DataNotFound, DataAlreadyExists, UserAuthenticationFailure
from application.models.user import User, UserAuthAction, LoginUser, LogoutUser
from werkzeug.security import generate_password_hash, check_password_hash

from application.repositories.user_repository import UserRepository


class UserSessionController:

    def __init__(self):
        self.user_repo = UserRepository()

    def process(self, user: Union[User, LoginUser, LogoutUser], user_auth_action: UserAuthAction) -> dict[str, Any]:

        if user_auth_action == UserAuthAction.SIGNUP and not user.uses_external_auth():
            user = self.execute_sign_up(user=user)
        user = self.authenticate_user(user=user)

        return self.generate_response(user=user)

    def generate_response(self, user: User) -> dict[str, Any]:
        if user.password:
            user.password = None
        dict_user = asdict(user)
        return {
            'error_details': None,
            'user': dict_user
        }

    def load_user(self, user_id: str) -> User:
        return self.user_repo.get_by_id(user_id=user_id)

    def execute_sign_up(self, user: User) -> User:
        try:
            existing_user = self.user_repo.get_by_id(user_id=user.user_id)
            if existing_user:
                raise DataAlreadyExists()
        except DataNotFound:
            copied_user = copy.deepcopy(user)
            hashed_password = generate_password_hash(user.password, method='pbkdf2:sha256')
            copied_user.password = hashed_password
            self.user_repo.create(user=copied_user)
            return user

    def authenticate_user(self, user: Union[User, LoginUser]) -> User:
        try:
            existing_user = self.user_repo.get_by_id(user_id=user.user_id)
            if not existing_user.uses_external_auth() and not check_password_hash(existing_user.password, user.password):
                    raise UserAuthenticationFailure()

            session['user_id'] = existing_user.user_id
            return existing_user
        except DataNotFound:
            if user.uses_external_auth():
                self.user_repo.create(user=user)
                session['user_id'] = user.user_id
                return user
            else:
                raise UserAuthenticationFailure()

