from rest_framework import serializers

from .models import (
    VerificationRequest,
    ReviewAssignment,
    ProductReview,
    ReviewIssue,
)

from seller.models import (
    Product,
    ProductVariant,
    ProductImage,
)


# ==========================================================
# PRODUCT IMAGE
# ==========================================================

class ProductImageReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductImage
        fields = [
            "id",
            "image",
        ]


# ==========================================================
# PRODUCT VARIANT
# ==========================================================

class ProductVariantReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "capacity",
            "price",
            "discount_price",
            "stock_quantity",
        ]


# ==========================================================
# PRODUCT DETAILS FOR REVIEW TEAM
# ==========================================================

class ProductReviewDetailSerializer(serializers.ModelSerializer):

    images = ProductImageReviewSerializer(
        many=True,
        read_only=True
    )

    variants = ProductVariantReviewSerializer(
        many=True,
        read_only=True
    )

    seller_id = serializers.IntegerField(
        source="seller.id",
        read_only=True
    )

    seller_name = serializers.CharField(
        source="seller.user.name",
        read_only=True
    )

    shop_name = serializers.CharField(
        source="seller.shop_name",
        read_only=True
    )

    class Meta:
        model = Product

        fields = [
            "id",
            "seller_id",
            "seller_name",
            "shop_name",

            "productname",
            "description",

            "price",
            "discount_price",

            "stock_quantity",

            "capacity",
            "weight",
            "category",

            "status",

            "images",
            "variants",

            "created_at",
            "updated_at",
        ]

        read_only_fields = fields


class ReviewIssueSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReviewIssue

        fields = [
            "id",
            "field",
            "comment",
        ]

        read_only_fields = [
            "id",
        ]

class ProductReviewSerializer(serializers.ModelSerializer):

    issues = ReviewIssueSerializer(
        many=True,
        read_only=True
    )

    reviewer_name = serializers.CharField(
        source="reviewer.name",
        read_only=True
    )

    class Meta:
        model = ProductReview

        fields = [
            "id",
            "verification_request",
            "reviewer",
            "reviewer_name",
            "decision",
            "reason",
            "issues",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "reviewer",
            "reviewer_name",
            "created_at",
        ]

class ReviewAssignmentSerializer(serializers.ModelSerializer):

    reviewer_name = serializers.CharField(
        source="reviewer.name",
        read_only=True
    )

    product_name = serializers.CharField(
        source="verification_request.product.productname",
        read_only=True
    )

    class Meta:
        model = ReviewAssignment

        fields = [
            "id",
            "verification_request",
            "reviewer",
            "reviewer_name",
            "product_name",
            "status",
            "assigned_at",
            "started_at",
            "completed_at",
        ]

        read_only_fields = [
            "id",
            "assigned_at",
            "started_at",
            "completed_at",
        ]
class VerificationRequestSerializer(serializers.ModelSerializer):

    product = ProductReviewDetailSerializer(
        read_only=True
    )

    class Meta:
        model = VerificationRequest

        fields = [
            "id",
            "product",
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields