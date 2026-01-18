import json
import logging
import urllib.parse
from collections import OrderedDict
from decimal import Decimal

import requests
from django import forms
from django.contrib import messages
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _
from pretix.base.decimal import round_decimal
from pretix.base.forms import SecretKeySettingsField
from pretix.base.models import Order, OrderPayment, Quota
from pretix.base.payment import BasePaymentProvider, PaymentException
from pretix.base.settings import SettingsSandbox
from pretix.helpers.http import redirect_to_url
from pretix.multidomain.urlreverse import build_absolute_uri, eventreverse
from requests import RequestException

from .opencollective import (
    CONFIRMED_ORDER_STATUSES,
    OC_BASEURL,
    OC_GRAPHQL_BASEURL,
    OC_GRAPHQL_STAGING_BASEURL,
    OC_LEGACY_API_BASEURL,
    OC_LEGACY_API_STAGING_BASEURL,
    OC_STAGING_BASEURL,
    ORDER_QUERY,
    PENDING_ORDER_STATUSES,
    TRANSACTION_QUERY,
)

logger = logging.getLogger("pretix_opencollective_payment")


class OpenCollectivePaymentProvider(BasePaymentProvider):
    identifier = "opencollective"
    verbose_name = "Open Collective"
    public_name = "Open Collective"

    def __init__(self, event):
        super().__init__(event)
        self.settings = SettingsSandbox("payment", self.identifier, event)

    @property
    def test_mode_message(self):
        if self.settings.get("use_staging", as_type=bool):
            return _("The Open Collective staging environment is enabled.")
        return None

    @property
    def settings_form_fields(self):
        fields = list(super().settings_form_fields.items()) + [
            (
                "collective_slug",
                forms.CharField(
                    label=_("Collective slug"),
                    required=True,
                    help_text=_("Slug for the Open Collective page."),
                ),
            ),
            (
                "event_slug",
                forms.CharField(
                    label=_("Event slug"),
                    required=False,
                    help_text=_("Optional event slug under the collective."),
                ),
            ),
            (
                "token",
                SecretKeySettingsField(
                    label=_("Personal token"),
                    required=True,
                    help_text=_("Personal token used for Open Collective API calls."),
                ),
            ),
            (
                "use_staging",
                forms.BooleanField(
                    label=_("Use staging"),
                    required=False,
                    help_text=_("Use the Open Collective staging environment."),
                ),
            ),
            (
                "recipient_email",
                forms.EmailField(
                    label=_("Recipient email"),
                    required=False,
                    help_text=_("Contact address shown in payment guidance."),
                ),
            ),
        ]
        return OrderedDict(fields)

    def settings_form_clean(self, cleaned_data):
        cleaned_data = super().settings_form_clean(cleaned_data)
        for key in ("collective_slug", "event_slug", "token"):
            if not cleaned_data.get(key):
                cleaned_data[key] = ""
        return cleaned_data

    def is_allowed(self, request, total=None):
        return super().is_allowed(request, total=total)

    def payment_form_render(self, request, total, order=None):
        return _(
            "You will be redirected to Open Collective to complete payment. After completing your payment, Open Collective will show you redirect warning. Please Click 'Continue' button to get back to us. So that we can confirm your payment."
        )

    def checkout_confirm_render(self, request, order=None, info_data=None):
        template = get_template(
            "pretixplugins/opencollective/checkout_payment_confirm.html"
        )
        ctx = {"request": request, "event": self.event, "settings": self.settings}
        return template.render(ctx)

    def checkout_prepare(self, request, cart):
        amount = cart.get("total")
        if amount is None:
            raise PaymentException(_("Invalid cart total."))
        request.session["payment_opencollective_payment"] = None
        request.session["payment_opencollective_expected"] = {
            "amount": str(amount),
            "currency": self.event.currency,
        }
        return self._build_donation_url(request, amount, None)

    def payment_prepare(self, request, payment):
        request.session["payment_opencollective_payment"] = payment.pk
        request.session["payment_opencollective_expected"] = {
            "amount": str(payment.amount),
            "currency": payment.order.event.currency,
            "order": payment.order.code,
        }
        return self._build_donation_url(request, payment.amount, payment.order)

    def payment_is_valid_session(self, request):
        return bool(request.session.get("payment_opencollective_order"))

    def execute_payment(self, request, payment):
        order_data = request.session.get("payment_opencollective_order")
        redirect_data = request.session.get("payment_opencollective_redirect", {})
        if not order_data:
            raise PaymentException(
                _("We could not verify your payment with Open Collective.")
            )

        status = self._validate_order(payment, order_data)
        info_payload = {
            "order_id": order_data.get("legacyId") or order_data.get("id"),
            "status": status,
            "order": order_data,
            "redirect": redirect_data,
        }
        payment.info = json.dumps(info_payload)
        payment.save(update_fields=["info"])

        if status in CONFIRMED_ORDER_STATUSES:
            if payment.state == OrderPayment.PAYMENT_STATE_CONFIRMED:
                logger.warning(
                    "Open Collective order already confirmed for payment %s",
                    payment.id,
                )
                return None
            try:
                payment.confirm()
            except Quota.QuotaExceededException as exc:
                raise PaymentException(str(exc))
            return None

        if status in PENDING_ORDER_STATUSES:
            payment.state = OrderPayment.PAYMENT_STATE_PENDING
            payment.save(update_fields=["state"])
            messages.warning(
                request,
                _(
                    "Open Collective has not yet confirmed the payment. We will "
                    "update your order once it clears."
                ),
            )
            return None

        payment.fail(info=info_payload)
        raise PaymentException(
            _("The Open Collective payment was not completed successfully.")
        )

    def payment_pending_render(self, request, payment):
        recipient_email = self.settings.get("recipient_email")
        if recipient_email:
            return _(
                "Your payment is still pending with Open Collective. If it does "
                "not complete soon, contact {email}."
            ).format(email=recipient_email)
        return _(
            "Your payment is still pending with Open Collective. If it does not "
            "complete soon, contact the organizer."
        )

    def payment_control_render(self, request, payment):
        order_id = payment.info_data.get("order_id") if payment.info else None
        status = payment.info_data.get("status") if payment.info else None
        summary = _("Open Collective order {id} ({status}).").format(
            id=order_id or "-",
            status=status or _("unknown"),
        )
        note = _("Refunds and cancellations must be handled in Open Collective.")
        return f"{summary}<br>{note}"

    def payment_control_render_short(self, payment):
        return str(payment.info_data.get("order_id", "")) if payment.info else ""

    def payment_refund_supported(self, payment):
        return False

    def payment_partial_refund_supported(self, payment):
        return False

    def _build_donation_url(self, request, amount, order):
        expected_slug = self._primary_slug()
        if not expected_slug:
            raise PaymentException(_("Open Collective settings are incomplete."))
        if amount <= 0:
            raise PaymentException(_("Invalid payment amount."))

        base_url = OC_BASEURL
        use_staging = self.settings.get("use_staging", as_type=bool)
        if use_staging:
            base_url = OC_STAGING_BASEURL

        url_kwargs = {}
        if request.resolver_match and "cart_namespace" in request.resolver_match.kwargs:
            url_kwargs["cart_namespace"] = request.resolver_match.kwargs[
                "cart_namespace"
            ]
        redirect_url = build_absolute_uri(
            request.event,
            "plugins:pretix_opencollective_payment:return",
            kwargs=url_kwargs,
        )
        amount_str = self._format_amount(amount, request.event.currency)
        donate_path = "/".join(
            [base_url.rstrip("/"), expected_slug, "donate", amount_str]
        )

        final_url = (
            f"{donate_path}?{urllib.parse.urlencode({'redirect': redirect_url})}"
        )

        return final_url

    def _format_amount(self, amount, currency):
        rounded = round_decimal(amount, currency)
        return str(int(rounded))

    def _primary_slug(self):
        return self.settings.get("event_slug") or self.settings.get("collective_slug")

    def _valid_slugs(self):
        slugs = [self.settings.get("event_slug"), self.settings.get("collective_slug")]
        return {slug for slug in slugs if slug}

    def _validate_order(self, payment, order_data):
        to_account = order_data.get("toAccount") or {}
        valid_slugs = self._valid_slugs()
        if valid_slugs and to_account.get("slug") not in valid_slugs:
            raise PaymentException(
                _("The Open Collective order does not match this event.")
            )

        amount_data = order_data.get("totalAmount") or order_data.get("amount")
        if not amount_data:
            raise PaymentException(_("Open Collective order amount missing."))
        oc_amount = Decimal(str(amount_data.get("value")))
        if oc_amount != payment.amount:
            raise PaymentException(_("The Open Collective payment amount differs."))
        if amount_data.get("currency") != payment.order.event.currency:
            raise PaymentException(_("The Open Collective payment currency differs."))

        frequency = order_data.get("frequency")
        if frequency and frequency != "ONETIME":
            raise PaymentException(
                _("Recurring Open Collective contributions are not supported.")
            )

        status = order_data.get("status")
        if not status:
            raise PaymentException(_("Open Collective order status missing."))
        return status

    def fetch_order_data(self, redirect_data):
        if redirect_data.get("orderIdV2"):
            return self._fetch_order_by_reference({"id": redirect_data["orderIdV2"]})
        if redirect_data.get("orderId"):
            try:
                legacy_id = int(redirect_data["orderId"])
                return self._fetch_order_by_reference({"legacyId": legacy_id})
            except (TypeError, ValueError):
                return self._fetch_order_by_reference({"id": redirect_data["orderId"]})
        if redirect_data.get("transactionid"):
            return self._fetch_order_by_transaction(redirect_data["transactionid"])
        raise PaymentException(_("Open Collective did not return order details."))

    def _fetch_order_by_reference(self, reference):
        payload = {"order": reference}
        data = self._graphql_request(ORDER_QUERY, payload)
        order_data = data.get("order")
        if not order_data:
            raise PaymentException(_("Open Collective order could not be found."))
        return order_data

    def _fetch_order_by_transaction(self, transaction_id):
        data = self._graphql_request(
            TRANSACTION_QUERY, {"transaction": {"id": transaction_id}}
        )
        transaction = data.get("transaction") or {}
        order_data = transaction.get("order")
        if order_data:
            return order_data

        try:
            legacy_id = int(transaction_id)
        except (TypeError, ValueError):
            legacy_id = None

        if legacy_id is not None:
            data = self._graphql_request(
                TRANSACTION_QUERY, {"transaction": {"legacyId": legacy_id}}
            )
            transaction = data.get("transaction") or {}
            order_data = transaction.get("order")
            if order_data:
                return order_data

        legacy_order = self._fetch_order_via_legacy(transaction_id)
        if legacy_order:
            return legacy_order

        raise PaymentException(_("Open Collective order could not be found."))

    def _fetch_order_via_legacy(self, transaction_id):
        expected_slug = self.settings.get("collective_slug")
        if not expected_slug:
            return None
        api_key = self.settings.get("token")
        if not api_key:
            return None

        base_url = (
            OC_LEGACY_API_STAGING_BASEURL
            if self.settings.get("use_staging", as_type=bool)
            else OC_LEGACY_API_BASEURL
        )
        url = f"{base_url}/collectives/{expected_slug}/transactions/{transaction_id}"
        try:
            response = requests.get(url, params={"apiKey": api_key}, timeout=15)
            response.raise_for_status()
        except RequestException as exc:
            logger.warning("Legacy OC lookup failed: %s", exc)
            return None

        payload = response.json().get("result") or {}
        order = payload.get("order")
        if order and order.get("id"):
            try:
                return self._fetch_order_by_reference({"legacyId": int(order["id"])})
            except (ValueError, PaymentException):
                return None

        amount_value = payload.get("amount")
        currency = payload.get("currency")
        status = None
        if order:
            status = order.get("status")
        if amount_value is None or not currency or not status:
            return None

        amount_decimal = (Decimal(str(amount_value)) / Decimal("100")).quantize(
            Decimal("0.01")
        )
        return {
            "id": None,
            "legacyId": None,
            "status": status,
            "frequency": payload.get("order", {})
            .get("subscription", {})
            .get("interval", "ONETIME"),
            "totalAmount": {"value": str(amount_decimal), "currency": currency},
            "amount": {"value": str(amount_decimal), "currency": currency},
            "toAccount": {"slug": expected_slug},
            "fromAccount": {
                "slug": payload.get("fromCollective", {}).get("slug"),
                "name": payload.get("fromCollective", {}).get("name"),
            },
        }

    def _graphql_request(self, query, variables):
        api_key = self.settings.get("token")
        if not api_key:
            raise PaymentException(_("Open Collective API token is missing."))
        endpoint = (
            OC_GRAPHQL_STAGING_BASEURL
            if self.settings.get("use_staging", as_type=bool)
            else OC_GRAPHQL_BASEURL
        )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                endpoint,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.exception("Open Collective API request failed")
            raise PaymentException(
                _("We had trouble communicating with Open Collective.")
            ) from exc
        payload = response.json()
        if payload.get("errors"):
            logger.error("Open Collective API error: %s", payload["errors"])
            raise PaymentException(
                _("Open Collective did not return a valid response.")
            )
        return payload.get("data") or {}

    def handle_callback(self, request, redirect_data):
        try:
            order_data = self.fetch_order_data(redirect_data)
        except PaymentException:
            raise

        request.session["payment_opencollective_order"] = order_data
        request.session["payment_opencollective_redirect"] = redirect_data

        payment_id = request.session.get("payment_opencollective_payment")
        if payment_id:
            try:
                payment = OrderPayment.objects.get(pk=payment_id)
            except OrderPayment.DoesNotExist:
                payment = None
            if payment:
                response = self.execute_payment(request, payment)
                if response:
                    return response
                return redirect_to_url(
                    eventreverse(
                        request.event,
                        "presale:event.order",
                        kwargs={
                            "order": payment.order.code,
                            "secret": payment.order.secret,
                        },
                    )
                    + ("?paid=yes" if payment.order.status == Order.STATUS_PAID else "")
                )

        return redirect_to_url(
            eventreverse(
                request.event, "presale:event.checkout", kwargs={"step": "confirm"}
            )
        )
