from dataclasses import dataclass


@dataclass
class Money:
    amount: int
    currency: str
    exponent: int