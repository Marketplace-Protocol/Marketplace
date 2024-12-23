from dataclasses import dataclass, asdict, fields
from typing import Dict, Any, Union

from application.utils import enforce_type_check

@dataclass
class StrictTypeModels:
    def __post_init__(self):
        """Enforce type check after initialization."""
        enforce_type_check(self)


@dataclass
class MongoModels:

    def get_id(self) -> Union[str, int]:
        raise NotImplemented()

    def to_mongo_document(self) -> Dict[str, Any]:
        d = asdict(self)
        d['_id'] = self.get_id()
        return d

    @classmethod
    def get_kwargs_from_mongo_document(cls, doc: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in doc.items() if k in {f.name for f in fields(cls)}}
