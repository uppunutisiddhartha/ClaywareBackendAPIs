from django.contrib import admin
from .models import (
    VerificationRequest,
    ReviewAssignment,
    ProductReview,
    ReviewIssue
)


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "product__productname",
    )


@admin.register(ReviewAssignment)
class ReviewAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "verification_request",
        "reviewer",
        "status",
        "assigned_at",
        "completed_at",
    )

    list_filter = (
        "status",
        "assigned_at",
    )

    search_fields = (
        "verification_request__product__productname",
        "reviewer__name",
        "reviewer__email",
    )


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "verification_request",
        "reviewer",
        "decision",
        "created_at",
    )

    list_filter = (
        "decision",
        "created_at",
    )

    search_fields = (
        "verification_request__product__productname",
        "reviewer__name",
    )


@admin.register(ReviewIssue)
class ReviewIssueAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "review",
        "field",
        "comment",
    )

    list_filter = (
        "field",
    )

    search_fields = (
        "review__verification_request__product__productname",
        "comment",
    )