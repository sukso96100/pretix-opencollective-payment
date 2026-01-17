from decimal import Decimal
from types import SimpleNamespace
import urllib.parse

import sys
import types


def _install_pretix_stubs():
    pretix_module = types.ModuleType("pretix")
    base_module = types.ModuleType("pretix.base")
    decimal_module = types.ModuleType("pretix.base.decimal")
    forms_module = types.ModuleType("pretix.base.forms")
    models_module = types.ModuleType("pretix.base.models")
    payment_module = types.ModuleType("pretix.base.payment")
    settings_module = types.ModuleType("pretix.base.settings")
    helpers_module = types.ModuleType("pretix.helpers")
    http_module = types.ModuleType("pretix.helpers.http")
    multidomain_module = types.ModuleType("pretix.multidomain")
    urlreverse_module = types.ModuleType("pretix.multidomain.urlreverse")

    def round_decimal(amount, currency=None):
        return amount.quantize(Decimal("0.01"))

    class BasePaymentProvider:
        settings_form_fields = {}

        def __init__(self, event=None):
            self.event = event

    class PaymentException(Exception):
        pass

    class DummyField:
        pass

    class Order:
        STATUS_PAID = "paid"

    class OrderPayment:
        PAYMENT_STATE_CONFIRMED = "confirmed"
        PAYMENT_STATE_PENDING = "pending"

    class Quota:
        class QuotaExceededException(Exception):
            pass

    class SettingsSandbox:
        def __init__(self, *args, **kwargs):
            pass

        def get(self, key, as_type=None):
            return None

    def redirect_to_url(url):
        return url

    def eventreverse(*args, **kwargs):
        return ""

    decimal_module.round_decimal = round_decimal
    forms_module.SecretKeySettingsField = DummyField
    models_module.Order = Order
    models_module.OrderPayment = OrderPayment
    models_module.Quota = Quota
    payment_module.BasePaymentProvider = BasePaymentProvider
    payment_module.PaymentException = PaymentException
    settings_module.SettingsSandbox = SettingsSandbox
    http_module.redirect_to_url = redirect_to_url
    urlreverse_module.build_absolute_uri = lambda *args, **kwargs: ""
    urlreverse_module.eventreverse = eventreverse

    sys.modules.update(
        {
            "pretix": pretix_module,
            "pretix.base": base_module,
            "pretix.base.decimal": decimal_module,
            "pretix.base.forms": forms_module,
            "pretix.base.models": models_module,
            "pretix.base.payment": payment_module,
            "pretix.base.settings": settings_module,
            "pretix.helpers": helpers_module,
            "pretix.helpers.http": http_module,
            "pretix.multidomain": multidomain_module,
            "pretix.multidomain.urlreverse": urlreverse_module,
        }
    )


_install_pretix_stubs()

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
