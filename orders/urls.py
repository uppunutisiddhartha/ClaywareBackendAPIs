from django.urls import path
from orders.views import *

urlpatterns = [

    # =========================
    # CART + BUY NOW CHECKOUT
    # =========================
    path(
        "checkout/",
        CheckoutAPI.as_view(),
        name="checkout",
    ),

    # =========================
    # CANCEL ORDER
    # =========================
    path(
        "cancel-order/",
        CancelOrderAPIView.as_view(),
        name="cancel-order",
    ),

    path(
        "success/<int:order_id>/",
        OrderSuccessAPIView.as_view(),
        name="order-success"
    ),
    path(
        "products/<int:product_id>/review/",
        AddReviewAPIView.as_view(),
        name="add-review"
    ),

    path(
        "products/<int:product_id>/reviews/",
        ProductReviewsAPIView.as_view(),
        name="product-reviews"
    ),

   

]