import enum
from dataclasses import dataclass
from typing import Optional, List

from application.errors import InvalidUserData
from application.models.models_utility import MongoModels

LOGIN_METHOD_PASSWORD = 'PASSWORD'
LOGIN_METHOD_GOOGLE = 'GOOGLE'
ACCEPTABLE_LOGIN_METHODS = [LOGIN_METHOD_PASSWORD, LOGIN_METHOD_GOOGLE]

class UserAuthAction(enum.Enum):
    SIGNUP = 1
    LOGIN = 2
    LOGOUT = 3


@dataclass
class LoginUser:
    username: str
    password: str
    user_id: Optional[str] = None

    def __post_init__(self) -> None:
        # This is a hack. Password users have their username as user ID
        self.user_id = self.username

@dataclass
class LogoutUser:
    user_id: str


@dataclass
class User(MongoModels):
    # For now it is same as username, but may not always be. So, having another field
    user_id: str

    username: str

    preferences: dict

    login_method: str

    deactivated: bool = False

    country: Optional[str] = None

    email: Optional[str] = None

    password: Optional[str] = None

    first_name: Optional[str] = None

    last_name: Optional[str] = None

    def get_id(self) -> str:
        return self.user_id

    def validate_context(self) -> None:
        if self.login_method not in ACCEPTABLE_LOGIN_METHODS:
            raise InvalidUserData("Unacceptable login method")

    def uses_external_auth(self) -> bool:
        return self.login_method != LOGIN_METHOD_PASSWORD

