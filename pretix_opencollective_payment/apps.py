from django.utils.translation import gettext_lazy

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2025.7 or above to run this plugin!")


class OpenCollectivePaymentApp(PluginConfig):
    name = "pretix_opencollective_payment"
    verbose_name = "Open Collective"

    class PretixPluginMeta:
        name = gettext_lazy("Open Collective")
        author = ""
        description = gettext_lazy("Accept payments via Open Collective.")
        visible = True
        version = "0.1.0"
        category = "PAYMENT"

    def ready(self):
        from . import signals

        signals  # noqa: B018
