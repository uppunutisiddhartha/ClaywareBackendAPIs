from django.urls import path
from .views import *

urlpatterns = [

    path('add-product/', AddProductAPI.as_view()),
   path(
        "edit-product/<int:id>/",
        EditProductApi.as_view(),
        name="edit-product"
    ),
    path('delete-product/<int:id>/', DeleteProductAPI.as_view()),
    path('seller-products/', SellerProductListAPI.as_view()),
    path('seller-orders/',SellerOrdersListAPI.as_view(),name='seller-orders'),
     path(
        "products/",
        SellerProductsView.as_view(),
        name="seller-products",
    ),


    path(
    "inventory/",
    SellerInventoryAPI.as_view(),
    name="seller-inventory"
),

path(
    "inventory/<int:product_id>/",
    UpdateInventoryAPI.as_view(),
    name="update-inventory"
),
]