from django.urls import include, re_path

from .views import return_view

app_name = "pretix_opencollective_payment"


event_patterns = [
    re_path(
        r"^payment/opencollective/",
        include(
            [
                re_path(r"^return/$", return_view, name="return"),
                re_path(
                    r"w/(?P<cart_namespace>[a-zA-Z0-9]{16})/return/$",
                    return_view,
                    name="return",
                ),
            ]
        ),
    )
]
