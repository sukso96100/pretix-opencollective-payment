from django.dispatch import receiver

from pretix.base.signals import register_payment_providers

from .payment import OpenCollectivePaymentProvider


@receiver(register_payment_providers, dispatch_uid="payment_opencollective")
def register_payment_provider(sender, **kwargs):
    return OpenCollectivePaymentProvider
