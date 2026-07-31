from django.urls import path

from .views import (
    OfferBannerCreateAPI,
    OfferBannerListAPI,
    ActiveOfferBannerAPI
)

urlpatterns = [
    path('banner/create/', OfferBannerCreateAPI.as_view()),
    path('banner/all/', OfferBannerListAPI.as_view()),
    path('banner/home/', ActiveOfferBannerAPI.as_view()),
]