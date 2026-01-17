from collections import OrderedDict

from django import forms
from django.utils.translation import gettext_lazy as _

from pretix.base.payment import BasePaymentProvider, PaymentException


class OpenCollectivePaymentProvider(BasePaymentProvider):
    identifier = "opencollective"
    verbose_name = "Open Collective"
    public_name = "Open Collective"
    execute_payment_needs_user = False

    @property
    def settings_form_fields(self):
        fields = list(super().settings_form_fields.items()) + [
            (
                "collective_slug",
                forms.CharField(
                    label=_("Collective slug"),
                    required=False,
                    help_text=_("Open Collective slug used to create contributions."),
                ),
            ),
            (
                "recipient_email",
                forms.EmailField(
                    label=_("Recipient email"),
                    required=False,
                    help_text=_("Contact address shown in instructions."),
                ),
            ),
        ]
        return OrderedDict(fields)

    def settings_form_clean(self, cleaned_data):
        cleaned_data = super().settings_form_clean(cleaned_data)
        if not cleaned_data.get("collective_slug"):
            cleaned_data["collective_slug"] = ""
        return cleaned_data

    def is_allowed(self, request, total=None):
        if not super().is_allowed(request, total=total):
            return False
        return True

    def payment_form_render(self, request, total, order=None):
        return _("You will be redirected to Open Collective to complete payment.")

    def checkout_confirm_render(self, request, order=None, info_data=None):
        return _("You will be redirected to Open Collective to complete payment.")

    def execute_payment(self, request, payment):
        raise PaymentException(_("Open Collective payment flow not implemented yet."))

    def payment_pending_render(self, request, payment):
        recipient_email = self.settings.get("recipient_email")
        if recipient_email:
            return _(
                "We will contact you at {email} if we need further details."
            ).format(email=recipient_email)
        return _("We will contact you if we need further details.")
