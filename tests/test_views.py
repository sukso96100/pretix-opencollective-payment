from types import SimpleNamespace

from pretix_opencollective_payment import views as views_module


def test_return_view_requires_order_reference(monkeypatch):
    event = SimpleNamespace()
    request = SimpleNamespace(event=event, GET={"status": "PAID"})
    views_module.messages._calls.clear()
    monkeypatch.setattr(
        views_module, "eventreverse", lambda *args, **kwargs: "/checkout/"
    )
    monkeypatch.setattr(views_module, "redirect_to_url", lambda url: url)

    result = views_module.return_view(request)

    assert result == "/checkout/"
    assert views_module.messages._calls == [
        (request, "Missing Open Collective order reference.")
    ]


def test_return_view_passes_redirect_data(monkeypatch):
    event = SimpleNamespace()
    request = SimpleNamespace(
        event=event,
        GET={"orderIdV2": "ord_123", "status": "PAID"},
    )
    captured = {}

    class ProviderStub:
        def __init__(self, event):
            self.event = event

        def handle_callback(self, request, redirect_data):
            captured["request"] = request
            captured["redirect_data"] = redirect_data
            return "handled"

    monkeypatch.setattr(views_module, "OpenCollectivePaymentProvider", ProviderStub)

    result = views_module.return_view(request)

    assert result == "handled"
    assert captured["request"] is request
    assert captured["redirect_data"] == {
        "orderId": None,
        "orderIdV2": "ord_123",
        "status": "PAID",
        "transactionid": None,
    }
