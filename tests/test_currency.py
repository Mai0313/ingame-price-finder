from src.currency_core import CurrencyCore


def test_get_avali_currency():
    currency_rate = CurrencyCore(country_name="usd")
    all_currency = currency_rate.get_avali_currency()
    for currency in all_currency:
        assert isinstance(currency, dict)
        for key, value in currency.items():
            assert isinstance(key, str)
            assert isinstance(value, str)


def test_fetch_currency_rates():
    # This testing do not need an assertion, it will check by pydantic.
    currency_rate = CurrencyCore(country_name="usd")
    currency_rate.fetch_currency_rates()
