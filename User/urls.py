from django.urls import path
from .views import *

urlpatterns = [

    # =========================
    # CART APIs
    # =========================

    path('addtocart/<int:id>/', AddToCartAPI.as_view()),
    path('viewcart/', ViewCartAPI.as_view()),
    path('remove-cart-item/<int:id>/', RemoveCartItemAPI.as_view()),


    # =========================
    # ADDRESS APIs
    # =========================

    path('add-address/', AddAddressAPI.as_view(), name='add-address'),
    path('user-addresses/', UserAddressesAPI.as_view(), name='user-addresses'),


    # =========================
    # ORDER APIs
    # =========================

    #path('order-product/<int:id>/', OrderProductAPI.as_view(), name='order-product'),
    path('user-order-history/', UserOrderHistoryAPI.as_view(), name='user-order-history'),
    #path('seller-orders/', SellerOrdersAPI.as_view(), name='seller-orders'),
    #path('update-order-status/<int:order_id>/', UpdateOrderStatusAPI.as_view(), name='update-order-status'),


     path(
    "order-details/<int:order_id>/",
    OrderDetailsAPIView.as_view(),
    name="order-details",
),

]