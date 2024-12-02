from typing import List

from application.models.instrument import Instrument, ProviderToken


def generate_mock_instrument_object(
        instrument_id: str = 'test_instrument_id',
        user_id: str = 'test_user_id',
        usage: str = 'payin',
        payment_method: str = 'card',
        tokens: List[ProviderToken] = []
):
    return Instrument(
        instrument_id=instrument_id,
        user_id=user_id,
        usage=usage,
        iin=None,
        last_four=None,
        payment_method=payment_method,
        tokens=tokens
    )