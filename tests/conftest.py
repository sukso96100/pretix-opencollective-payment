from decimal import Decimal
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
        def __init__(self, *args, **kwargs):
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


def _install_django_stubs():
    django_module = types.ModuleType("django")
    contrib_module = types.ModuleType("django.contrib")
    messages_module = types.ModuleType("django.contrib.messages")
    forms_module = types.ModuleType("django.forms")
    template_module = types.ModuleType("django.template")
    loader_module = types.ModuleType("django.template.loader")
    utils_module = types.ModuleType("django.utils")
    translation_module = types.ModuleType("django.utils.translation")

    messages_module._calls = []

    def error(request, message):
        messages_module._calls.append((request, message))

    def gettext(value):
        return value

    class DummyField:
        def __init__(self, *args, **kwargs):
            pass

    class DummyTemplate:
        def render(self, *args, **kwargs):
            return ""

    def get_template(*args, **kwargs):
        return DummyTemplate()

    messages_module.error = error
    translation_module.gettext = gettext
    translation_module.gettext_lazy = gettext
    forms_module.CharField = DummyField
    forms_module.BooleanField = DummyField
    forms_module.EmailField = DummyField
    loader_module.get_template = get_template
    django_module.forms = forms_module

    sys.modules.update(
        {
            "django": django_module,
            "django.contrib": contrib_module,
            "django.contrib.messages": messages_module,
            "django.forms": forms_module,
            "django.template": template_module,
            "django.template.loader": loader_module,
            "django.utils": utils_module,
            "django.utils.translation": translation_module,
        }
    )


_install_pretix_stubs()
_install_django_stubs()
