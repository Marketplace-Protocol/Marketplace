from application.providers.stripe_charge_provider import StripeChargeProvider
from tests.objects.instrument import generate_mock_instrument_object
from tests.objects.transaction import generate_mock_auth_transaction_object


def test_create_auth():
    provider = StripeChargeProvider()
    res = provider.create_auth(
        txt=generate_mock_auth_transaction_object(),
        instrument=generate_mock_instrument_object()
    )
    print(res)