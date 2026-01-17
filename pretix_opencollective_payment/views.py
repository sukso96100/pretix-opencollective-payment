from django.contrib import messages
from django.utils.translation import gettext as _

from pretix.base.payment import PaymentException
from pretix.helpers.http import redirect_to_url
from pretix.multidomain.urlreverse import eventreverse

from .payment import OpenCollectivePaymentProvider


def return_view(request, *args, **kwargs):
    provider = OpenCollectivePaymentProvider(request.event)
    redirect_data = {
        "orderId": request.GET.get("orderId"),
        "orderIdV2": request.GET.get("orderIdV2"),
        "status": request.GET.get("status"),
        "transactionid": request.GET.get("transactionid"),
    }

    if not any(redirect_data.values()):
        messages.error(request, _("Missing Open Collective redirect parameters."))
        urlkwargs = {"step": "payment"}
        if "cart_namespace" in kwargs:
            urlkwargs["cart_namespace"] = kwargs["cart_namespace"]
        return redirect_to_url(
            eventreverse(request.event, "presale:event.checkout", kwargs=urlkwargs)
        )

    try:
        return provider.handle_callback(request, redirect_data)
    except PaymentException as exc:
        messages.error(request, str(exc))
        urlkwargs = {"step": "payment"}
        if "cart_namespace" in kwargs:
            urlkwargs["cart_namespace"] = kwargs["cart_namespace"]
        return redirect_to_url(
            eventreverse(request.event, "presale:event.checkout", kwargs=urlkwargs)
        )
