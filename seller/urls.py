from django.urls import path
from .views import *

urlpatterns = [

    path('add-product/', AddProductAPI.as_view()),
    path('edit-product/<int:id>/', EditProductApi.as_view()),
    path('delete-product/<int:id>/', DeleteProductAPI.as_view()),
    path('seller-products/', SellerProductListAPI.as_view()),
    path('seller-orders/',SellerOrdersListAPI.as_view(),name='seller-orders'),
]