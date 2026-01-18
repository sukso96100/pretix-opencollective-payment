from decimal import Decimal
from decimal import Decimal
from types import SimpleNamespace
import urllib.parse

from pretix_opencollective_payment import payment as payment_module


class SettingsStub:
    def __init__(self, values):
        self._values = values

    def get(self, key, as_type=None):
        value = self._values.get(key)
        if as_type is bool and value is not None:
            return bool(value)
        return value


def build_provider(settings_values, currency="USD"):
    provider = payment_module.OpenCollectivePaymentProvider.__new__(
        payment_module.OpenCollectivePaymentProvider
    )
    provider.event = SimpleNamespace(currency=currency)
    provider.settings = SettingsStub(settings_values)
    return provider


def build_request(event):
    return SimpleNamespace(event=event, resolver_match=None)


def test_build_donation_url_uses_production_and_no_memo(monkeypatch):
    provider = build_provider(
        {"collective_slug": "my-collective", "use_staging": False}
    )
    redirect_url = "https://pretix.example.com/return/"
    monkeypatch.setattr(
        payment_module,
        "build_absolute_uri",
        lambda event, url, kwargs=None: redirect_url,
    )

    url = provider._build_donation_url(
        build_request(provider.event), Decimal("10.00"), None
    )

    expected = (
        "https://opencollective.com/my-collective/donate/10?"
        + urllib.parse.urlencode({"redirect": redirect_url})
    )
    assert url == expected
    assert "pretix_order" not in url


def test_build_donation_url_uses_staging_when_enabled(monkeypatch):
    provider = build_provider({"collective_slug": "my-collective", "use_staging": True})
    redirect_url = "https://pretix.example.com/return/"
    monkeypatch.setattr(
        payment_module,
        "build_absolute_uri",
        lambda event, url, kwargs=None: redirect_url,
    )

    url = provider._build_donation_url(
        build_request(provider.event), Decimal("10.00"), None
    )

    expected = (
        "https://staging.opencollective.com/my-collective/donate/10?"
        + urllib.parse.urlencode({"redirect": redirect_url})
    )
    assert url == expected


def test_format_amount_returns_major_units():
    provider = build_provider({"collective_slug": "my-collective"})
    assert provider._format_amount(Decimal("5.00"), "USD") == "5"


def test_payment_control_render_refund_url_production():
    provider = build_provider({"collective_slug": "ubucon-asia"})
    payment = SimpleNamespace(
        info="payload",
        info_data={
            "order_id": 919699,
            "transaction_id": 11503420,
            "status": "PAID",
            "collective_slug": "ubucon-asia",
            "use_staging": False,
        },
    )

    result = provider.payment_control_render(None, payment)

    assert "https://opencollective.com/dashboard/ubucon-asia/" in result
    assert "openTransactionId=11503420" in result


def test_payment_control_render_refund_url_staging():
    provider = build_provider({"collective_slug": "ubucon-asia"})
    payment = SimpleNamespace(
        info="payload",
        info_data={
            "order_id": 919699,
            "transaction_id": 11503420,
            "status": "PAID",
            "collective_slug": "ubucon-asia",
            "use_staging": True,
        },
    )

    result = provider.payment_control_render(None, payment)

    assert "https://staging.opencollective.com/dashboard/ubucon-asia/" in result
    assert "openTransactionId=11503420" in result


def test_payment_control_render_without_transaction_id():
    provider = build_provider({"collective_slug": "ubucon-asia"})
    payment = SimpleNamespace(
        info="payload",
        info_data={
            "order_id": 919699,
            "status": "PAID",
            "collective_slug": "ubucon-asia",
            "use_staging": False,
        },
    )

    result = provider.payment_control_render(None, payment)

    assert "openTransactionId=" not in result
