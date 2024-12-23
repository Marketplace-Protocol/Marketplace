import re
import time


def now_in_epoch_sec():
    return int(time.time())


def _convert_from_camel_to_snake(s: str) -> str:
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def enforce_type_check(obj):
    """Function to enforce type checking for dataclass fields."""
    for field_name, field_obj in obj.__dataclass_fields__.items():
        actual_type = type(getattr(obj, field_name))
        expected_type = field_obj.type
        if actual_type != expected_type:
            raise TypeError(f"Invalid type for field '{field_name}'. "
                            f"Expected {expected_type.__name__}, got {actual_type.__name__}")