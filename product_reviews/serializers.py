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

        read_only_fields = fields


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

        read_only_fields = fields


# ==========================================================
# PRODUCT DETAILS
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
        read_only=True,
        default=""
    )

    shop_name = serializers.CharField(
        source="seller.shop_name",
        read_only=True,
        default=""
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


# ==========================================================
# REVIEW ISSUE
# ==========================================================

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


# ==========================================================
# PRODUCT REVIEW
# ==========================================================

class ProductReviewSerializer(serializers.ModelSerializer):

    issues = ReviewIssueSerializer(
        many=True,
        read_only=True
    )

    reviewer_name = serializers.CharField(
        source="reviewer.name",
        read_only=True,
        default=""
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


# ==========================================================
# REVIEW ASSIGNMENT
# ==========================================================

class ReviewAssignmentSerializer(serializers.ModelSerializer):

    reviewer_name = serializers.CharField(
        source="reviewer.name",
        read_only=True,
        default=""
    )

    product_name = serializers.CharField(
        source="verification_request.product.productname",
        read_only=True,
        default=""
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


# ==========================================================
# VERIFICATION REQUEST
# ==========================================================

class VerificationRequestSerializer(serializers.ModelSerializer):

    product = ProductReviewDetailSerializer(
        read_only=True
    )

    # ------------------------------------------------------
    # ASSIGNMENT INFORMATION
    # ------------------------------------------------------

    assignment_id = serializers.SerializerMethodField()

    assignment_status = serializers.SerializerMethodField()

    assigned_at = serializers.SerializerMethodField()

    started_at = serializers.SerializerMethodField()

    completed_at = serializers.SerializerMethodField()

    # ------------------------------------------------------
    # REVIEW INFORMATION
    # ------------------------------------------------------

    review_id = serializers.SerializerMethodField()

    review_decision = serializers.SerializerMethodField()

    review_reason = serializers.SerializerMethodField()

    reviewer_name = serializers.SerializerMethodField()

    issues = serializers.SerializerMethodField()

    class Meta:
        model = VerificationRequest

        fields = [
            "id",

            "product",

            # Verification
            "status",

            # Assignment
            "assignment_id",
            "assignment_status",
            "assigned_at",
            "started_at",
            "completed_at",

            # Review
            "review_id",
            "review_decision",
            "review_reason",
            "reviewer_name",
            "issues",

            # Dates
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields

    # ======================================================
    # ASSIGNMENT
    # ======================================================

    def _get_assignment(self, obj):

        return getattr(
            obj,
            "assignment",
            None
        )

    def get_assignment_id(self, obj):

        assignment = self._get_assignment(obj)

        return (
            assignment.id
            if assignment
            else None
        )

    def get_assignment_status(self, obj):

        assignment = self._get_assignment(obj)

        return (
            assignment.status
            if assignment
            else None
        )

    def get_assigned_at(self, obj):

        assignment = self._get_assignment(obj)

        return (
            assignment.assigned_at
            if assignment
            else None
        )

    def get_started_at(self, obj):

        assignment = self._get_assignment(obj)

        return (
            assignment.started_at
            if assignment
            else None
        )

    def get_completed_at(self, obj):

        assignment = self._get_assignment(obj)

        return (
            assignment.completed_at
            if assignment
            else None
        )

    # ======================================================
    # LATEST REVIEW
    # ======================================================

    def _get_latest_review(self, obj):

        return (
            obj.reviews
            .select_related("reviewer")
            .prefetch_related("issues")
            .order_by("-created_at")
            .first()
        )

    def get_review_id(self, obj):

        review = self._get_latest_review(obj)

        return (
            review.id
            if review
            else None
        )

    def get_review_decision(self, obj):

        review = self._get_latest_review(obj)

        return (
            review.decision
            if review
            else None
        )

    def get_review_reason(self, obj):

        review = self._get_latest_review(obj)

        return (
            review.reason
            if review
            else ""
        )

    def get_reviewer_name(self, obj):

        review = self._get_latest_review(obj)

        if review and review.reviewer:

            return review.reviewer.name

        assignment = self._get_assignment(obj)

        if assignment and assignment.reviewer:

            return assignment.reviewer.name

        return ""

    def get_issues(self, obj):

        review = self._get_latest_review(obj)

        if not review:
            return []

        return ReviewIssueSerializer(
            review.issues.all(),
            many=True
        ).data