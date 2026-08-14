from django.urls import path

from .views import (
    MyReviewQueueView,
    ReviewProductDetailView,
    StartReviewView,
    ApproveProductView,
    RejectProductView,
    RequestChangesView,
)


urlpatterns = [

    path(
        "my-queue/",
        MyReviewQueueView.as_view(),
        name="my-review-queue"
    ),

    path(
        "<int:product_id>/",
        ReviewProductDetailView.as_view(),
        name="review-product-detail"
    ),

    path(
        "<int:product_id>/start/",
        StartReviewView.as_view(),
        name="start-review"
    ),

    path(
        "<int:product_id>/approve/",
        ApproveProductView.as_view(),
        name="approve-product"
    ),

    path(
        "<int:product_id>/reject/",
        RejectProductView.as_view(),
        name="reject-product"
    ),

    path(
        "<int:product_id>/request-changes/",
        RequestChangesView.as_view(),
        name="request-product-changes"
    ),
]