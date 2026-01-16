from django.utils.translation import gettext_lazy

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2025.7 or above to run this plugin!")


class PretixPluginMeta(PluginConfig):
    name = "pretix_opencollective"
    verbose_name = "Open Collective"
    description = gettext_lazy("Accept payments via Open Collective.")
    version = "0.1.0"
    category = "PAYMENT"
    author = ""

    def ready(self):
        from . import signals

        signals  # noqa: B018
