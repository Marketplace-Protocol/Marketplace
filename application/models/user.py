from dataclasses import dataclass
from typing import Optional, List


@dataclass
class User:
    user_id: str

    username: str

    country: str

    preferences: dict

    login_method: List[str]

    email: Optional[str] = None

    first_name: Optional[str] = None

    last_name: Optional[str] = None

