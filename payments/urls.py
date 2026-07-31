from django.urls import path

from .views import (
    CreateRazorpayOrderAPIView,
    VerifyRazorpayPaymentAPIView,
    PaymentFailedAPIView,

)

urlpatterns = [

    path(
        "create-order/",
        CreateRazorpayOrderAPIView.as_view(),
        name="create-order"
    ),

    path(
        "verify/",
        VerifyRazorpayPaymentAPIView.as_view(),
        name="verify-payment"
    ),
    path(
    "payment-failed/",
    PaymentFailedAPIView.as_view(),
),
]