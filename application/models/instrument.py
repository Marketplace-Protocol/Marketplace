from dataclasses import dataclass
from typing import Optional, Union

from application.models.models_utility import MongoModels


@dataclass
class ProviderToken:
    token: str
    provider: str
    customer_id: Optional[str] = None


@dataclass
class Instrument(MongoModels):
    instrument_id: str

    user_id: str

    usage: str

    payment_method: str

    tokens: list[ProviderToken]

    iin: Optional[int] = None

    last_four: Optional[int] = None

    def __post_init__(self) -> None:
        tokens = []
        for token in self.tokens:
            if isinstance(token, dict):
                tokens.append(ProviderToken(**token))
        if tokens:
            self.tokens = tokens


    def get_id(self) -> Union[str, int]:
        return self.instrument_id

