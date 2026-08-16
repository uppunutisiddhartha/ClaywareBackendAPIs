from django.db import transaction
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from seller.models import Product
from accounts.models import Seller

from .models import (
    VerificationRequest,
    ReviewAssignment,
    ProductReview,
    ReviewIssue,
)

from .serializers import VerificationRequestSerializer
from .permissions import IsProductReviewer


User = get_user_model()


# ==========================================================
# ASSIGN PRODUCT TO REVIEWER
# ==========================================================

@transaction.atomic
def assign_product_to_reviewer(
    product,
    preferred_reviewer=None,
):
    """
    Create a new VerificationRequest and assign the product.

    Priority:
        1. Preferred reviewer
        2. Least-loaded active reviewer
        3. No reviewer -> request remains pending

    IMPORTANT:
    A completed request is NEVER reused.

    Every seller resubmission creates a NEW
    VerificationRequest + ReviewAssignment.
    """

    # ------------------------------------------------------
    # CHECK ACTIVE REQUEST
    # ------------------------------------------------------

    existing_request = (
        VerificationRequest.objects
        .filter(
            product=product,
            status__in=[
                "pending",
                "assigned",
                "in_review",
            ],
        )
        .order_by("-created_at", "-id")
        .first()
    )

    if existing_request:

        assignment = (
            ReviewAssignment.objects
            .filter(
                verification_request=existing_request,
                status__in=[
                    "assigned",
                    "in_review",
                ],
            )
            .select_related("reviewer")
            .order_by("-assigned_at", "-id")
            .first()
        )

        return existing_request, assignment

    # ------------------------------------------------------
    # CREATE NEW VERIFICATION REQUEST
    # ------------------------------------------------------

    verification_request = (
        VerificationRequest.objects.create(
            product=product,
            status="pending",
        )
    )

    # ------------------------------------------------------
    # FIND REVIEWER
    # ------------------------------------------------------

    reviewer = None

    # ------------------------------------------------------
    # 1. PREFERRED REVIEWER
    # ------------------------------------------------------

    if preferred_reviewer:

        reviewer = (
            User.objects
            .filter(
                id=preferred_reviewer.id,
                role="product_reviewer",
                account_status="active",
            )
            .first()
        )

    # ------------------------------------------------------
    # 2. LEAST LOADED REVIEWER
    # ------------------------------------------------------

    if reviewer is None:

        reviewer = (
            User.objects
            .filter(
                role="product_reviewer",
                account_status="active",
            )
            .annotate(
                pending_reviews=Count(
                    "review_assignments",
                    filter=Q(
                        review_assignments__status__in=[
                            "assigned",
                            "in_review",
                        ]
                    ),
                )
            )
            .order_by(
                "pending_reviews",
                "id",
            )
            .first()
        )

    # ------------------------------------------------------
    # NO REVIEWER
    # ------------------------------------------------------

    if reviewer is None:

        return verification_request, None

    # ------------------------------------------------------
    # CREATE ASSIGNMENT
    # ------------------------------------------------------

    assignment = (
        ReviewAssignment.objects.create(
            verification_request=verification_request,
            reviewer=reviewer,
            status="assigned",
        )
    )

    # ------------------------------------------------------
    # UPDATE REQUEST
    # ------------------------------------------------------

    verification_request.status = "assigned"

    verification_request.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return verification_request, assignment


# ==========================================================
# SELLER SUBMITS PRODUCT FOR VERIFICATION
# ==========================================================

class SubmitProductForVerificationView(APIView):

    @transaction.atomic
    def post(self, request, product_id):

        # --------------------------------------------------
        # SELLER
        # --------------------------------------------------

        try:

            seller = (
                Seller.objects
                .select_related("user")
                .get(
                    user=request.user
                )
            )

        except Seller.DoesNotExist:

            return Response(
                {
                    "message":
                    "Seller profile not found for this account."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # --------------------------------------------------
        # PRODUCT
        # --------------------------------------------------

        try:

            product = (
                Product.objects
                .select_related("seller")
                .get(
                    id=product_id,
                    seller=seller,
                )
            )

        except Product.DoesNotExist:

            return Response(
                {
                    "message":
                    "Product not found or you are not the seller."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # --------------------------------------------------
        # VALID PRODUCT STATUS
        # --------------------------------------------------

        if product.status not in [
            "draft",
            "changes_required",
        ]:

            return Response(
                {
                    "message":
                    "This product cannot be submitted "
                    "for verification in its current status.",

                    "product_id":
                    product.id,

                    "status":
                    product.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------
        # FIND PREVIOUS REVIEWER
        #
        # If previous review requested changes,
        # assign the same reviewer again.
        # --------------------------------------------------

        previous_reviewer = None

        previous_request = (
            VerificationRequest.objects
            .filter(
                product=product,
                status="completed",
            )
            .order_by(
                "-created_at",
                "-id",
            )
            .first()
        )

        if previous_request:

            previous_review = (
                previous_request
                .reviews
                .filter(
                    decision="changes_required",
                    reviewer__isnull=False,
                )
                .select_related("reviewer")
                .order_by(
                    "-created_at",
                    "-id",
                )
                .first()
            )

            if previous_review:

                previous_reviewer = (
                    previous_review.reviewer
                )

        # --------------------------------------------------
        # CHANGE PRODUCT STATUS
        # --------------------------------------------------

        product.status = "pending_verification"

        product.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # --------------------------------------------------
        # CREATE NEW REQUEST + ASSIGN
        # --------------------------------------------------

        verification_request, assignment = (
            assign_product_to_reviewer(
                product=product,
                preferred_reviewer=previous_reviewer,
            )
        )

        # --------------------------------------------------
        # NO REVIEWER AVAILABLE
        # --------------------------------------------------

        if assignment is None:

            return Response(
                {
                    "message":
                    "Product submitted successfully, "
                    "but no active Product Reviewer is available.",

                    "product_id":
                    product.id,

                    "status":
                    product.status,

                    "verification_request_id":
                    verification_request.id,

                    "verification_status":
                    verification_request.status,

                    "assignment_id":
                    None,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        # --------------------------------------------------
        # SUCCESS
        # --------------------------------------------------

        return Response(
            {
                "message":
                "Product submitted and automatically "
                "assigned to a Product Reviewer.",

                "product_id":
                product.id,

                "status":
                product.status,

                "verification_request_id":
                verification_request.id,

                "verification_status":
                verification_request.status,

                "assignment_id":
                assignment.id,

                "assignment_status":
                assignment.status,

                "reviewer_id":
                assignment.reviewer.id,

                "reviewer_name":
                assignment.reviewer.name,

                "same_reviewer":
                (
                    previous_reviewer is not None
                    and
                    previous_reviewer.id ==
                    assignment.reviewer.id
                ),
            },
            status=status.HTTP_201_CREATED,
        )


# ==========================================================
# MY REVIEW QUEUE
#
# IMPORTANT:
#
# Shows ALL assignments belonging to the logged-in reviewer.
#
# This includes:
#
# assigned
# in_review
# completed
#
# Therefore:
#
# APPROVED
# REJECTED
# CHANGES_REQUIRED
#
# history remains visible.
# ==========================================================

class MyReviewQueueView(APIView):

    permission_classes = [IsProductReviewer]

    def get(self, request):

        assignments = (
            ReviewAssignment.objects
            .filter(
                reviewer=request.user
            )
            .select_related(
                "reviewer",
                "verification_request",
                "verification_request__product",
                "verification_request__product__seller",
                "verification_request__product__seller__user",
            )
            .prefetch_related(
                "verification_request__product__images",
                "verification_request__product__variants",
                "verification_request__reviews",
            )
            .order_by(
                "-assigned_at",
                "-id",
            )
        )

        results = []

        for assignment in assignments:

            verification_request = (
                assignment.verification_request
            )

            product = (
                verification_request.product
            )

            # --------------------------------------------------
            # LATEST REVIEW
            # --------------------------------------------------

            latest_review = (
                verification_request
                .reviews
                .select_related("reviewer")
                .prefetch_related("issues")
                .order_by(
                    "-created_at",
                    "-id",
                )
                .first()
            )

            # --------------------------------------------------
            # IMAGES
            # --------------------------------------------------

            images = []

            for image in product.images.all():

                image_url = None

                if image.image:

                    try:
                        image_url = image.image.url

                    except Exception:

                        image_url = str(
                            image.image
                        )

                images.append(
                    {
                        "id":
                        image.id,

                        "image":
                        image_url,
                    }
                )

            # --------------------------------------------------
            # VARIANTS
            # --------------------------------------------------

            variants = []

            for variant in product.variants.all():

                variants.append(
                    {
                        "id":
                        variant.id,

                        "capacity":
                        variant.capacity,

                        "price":
                        variant.price,

                        "discount_price":
                        variant.discount_price,

                        "stock_quantity":
                        variant.stock_quantity,
                    }
                )

            # --------------------------------------------------
            # ISSUES
            # --------------------------------------------------

            issues = []

            if latest_review:

                for issue in latest_review.issues.all():

                    issues.append(
                        {
                            "id":
                            issue.id,

                            "field":
                            issue.field,

                            "comment":
                            issue.comment,
                        }
                    )

            # --------------------------------------------------
            # PRODUCT DATA
            # --------------------------------------------------

            product_data = {

                "id":
                product.id,

                "productname":
                product.productname,

                "description":
                product.description,

                "price":
                product.price,

                "discount_price":
                product.discount_price,

                "stock_quantity":
                product.stock_quantity,

                "capacity":
                product.capacity,

                "weight":
                product.weight,

                "category":
                product.category,

                "status":
                product.status,

                # ------------------------------------------
                # SELLER
                # ------------------------------------------

                "seller_id":
                product.seller.id
                if product.seller
                else None,

                "seller_name":
                product.seller.user.name
                if product.seller
                and product.seller.user
                else "",

                "shop_name":
                product.seller.shop_name
                if product.seller
                else "",

                # ------------------------------------------
                # IMAGES
                # ------------------------------------------

                "images":
                images,

                # ------------------------------------------
                # VARIANTS
                # ------------------------------------------

                "variants":
                variants,

                # ------------------------------------------
                # DATES
                # ------------------------------------------

                "created_at":
                product.created_at,

                "updated_at":
                product.updated_at,
            }

            # --------------------------------------------------
            # IS ACTIVE?
            # --------------------------------------------------

            is_active = (
                assignment.status
                in [
                    "assigned",
                    "in_review",
                ]
            )

            # --------------------------------------------------
            # ACTION AVAILABLE?
            # --------------------------------------------------

            can_start_review = (
                assignment.status ==
                "assigned"
            )

            can_take_action = (
                assignment.status ==
                "in_review"
            )

            # --------------------------------------------------
            # RESULT
            # --------------------------------------------------

            results.append(
                {

                    # --------------------------------------
                    # ASSIGNMENT
                    # --------------------------------------

                    "assignment_id":
                    assignment.id,

                    "assignment_status":
                    assignment.status,

                    "assigned_at":
                    assignment.assigned_at,

                    "started_at":
                    assignment.started_at,

                    "completed_at":
                    assignment.completed_at,

                    # --------------------------------------
                    # IMPORTANT FRONTEND FLAGS
                    # --------------------------------------

                    "is_active":
                    is_active,

                    "can_start_review":
                    can_start_review,

                    "can_take_action":
                    can_take_action,

                    # --------------------------------------
                    # VERIFICATION
                    # --------------------------------------

                    "verification_request_id":
                    verification_request.id,

                    "verification_status":
                    verification_request.status,

                    # --------------------------------------
                    # REVIEWER
                    # --------------------------------------

                    "reviewer_id":
                    assignment.reviewer.id,

                    "reviewer_name":
                    assignment.reviewer.name,

                    # --------------------------------------
                    # PRODUCT
                    # --------------------------------------

                    "product":
                    product_data,

                    # --------------------------------------
                    # REVIEW
                    # --------------------------------------

                    "decision":
                    (
                        latest_review.decision
                        if latest_review
                        else None
                    ),

                    "reason":
                    (
                        latest_review.reason
                        if latest_review
                        else ""
                    ),

                    "review_id":
                    (
                        latest_review.id
                        if latest_review
                        else None
                    ),

                    # --------------------------------------
                    # ISSUES
                    # --------------------------------------

                    "issues":
                    issues,
                }
            )

        return Response(
            {
                "count":
                len(results),

                "results":
                results,
            }
        )


# ==========================================================
# PRODUCT REVIEW DETAILS
#
# IMPORTANT:
#
# This endpoint can now open BOTH:
#
# 1. ACTIVE assignment
# 2. COMPLETED assignment/history
#
# But action permissions are returned separately.
#
# A completed review is READ-ONLY.
# ==========================================================
# ==========================================================
# PRODUCT DETAILS
#
# Supports:
#
# 1. ACTIVE REVIEW
#    assigned
#    in_review
#
# 2. COMPLETED HISTORY
#    completed
#
# Completed reviews are READ ONLY.
# They cannot be started again.
# ==========================================================

class ReviewProductDetailView(APIView):

    permission_classes = [IsProductReviewer]

    def get(self, request, product_id):

        # --------------------------------------------------
        # FIND LATEST ASSIGNMENT
        #
        # IMPORTANT:
        # We intentionally DO NOT filter by assignment status
        # here because completed reviews must also be visible.
        # --------------------------------------------------

        assignment = (
            ReviewAssignment.objects
            .filter(
                reviewer=request.user,
                verification_request__product_id=product_id,
            )
            .select_related(
                "reviewer",
                "verification_request",
                "verification_request__product",
                "verification_request__product__seller",
                "verification_request__product__seller__user",
            )
            .prefetch_related(
                "verification_request__product__images",
                "verification_request__product__variants",
                "verification_request__reviews",
                "verification_request__reviews__issues",
            )
            .order_by(
                "-assigned_at",
                "-id",
            )
            .first()
        )

        # --------------------------------------------------
        # NO ASSIGNMENT
        # --------------------------------------------------

        if assignment is None:

            return Response(
                {
                    "message":
                    "This product has never been assigned "
                    "to you for review."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # --------------------------------------------------
        # SERIALIZE VERIFICATION REQUEST
        # --------------------------------------------------

        serializer = VerificationRequestSerializer(
            assignment.verification_request
        )

        data = serializer.data

        # --------------------------------------------------
        # ASSIGNMENT INFORMATION
        # --------------------------------------------------

        data["assignment_id"] = assignment.id

        data["assignment_status"] = (
            assignment.status
        )

        data["assigned_at"] = (
            assignment.assigned_at
        )

        data["started_at"] = (
            assignment.started_at
        )

        data["completed_at"] = (
            assignment.completed_at
        )

        # --------------------------------------------------
        # REVIEWER
        # --------------------------------------------------

        data["reviewer_id"] = (
            assignment.reviewer.id
        )

        data["reviewer_name"] = (
            assignment.reviewer.name
        )

        # --------------------------------------------------
        # PRODUCT
        # --------------------------------------------------

        product = (
            assignment
            .verification_request
            .product
        )

        data["product_status"] = (
            product.status
        )

        # --------------------------------------------------
        # DETERMINE ACTIVE / HISTORY
        # --------------------------------------------------

        data["is_active"] = (
            assignment.status
            in [
                "assigned",
                "in_review",
            ]
        )

        data["is_completed"] = (
            assignment.status == "completed"
        )

        # --------------------------------------------------
        # LATEST REVIEW
        # --------------------------------------------------

        latest_review = (
            assignment
            .verification_request
            .reviews
            .select_related("reviewer")
            .prefetch_related("issues")
            .order_by("-created_at")
            .first()
        )

        # --------------------------------------------------
        # REVIEW DATA
        # --------------------------------------------------

        if latest_review:

            data["review"] = {
                "id": latest_review.id,

                "decision": (
                    latest_review.decision
                ),

                "reason": (
                    latest_review.reason
                    or ""
                ),

                "reviewer_id": (
                    latest_review.reviewer.id
                    if latest_review.reviewer
                    else None
                ),

                "reviewer_name": (
                    latest_review.reviewer.name
                    if latest_review.reviewer
                    else ""
                ),

                "created_at": (
                    latest_review.created_at
                ),

                "issues": [
                    {
                        "id": issue.id,
                        "field": issue.field,
                        "comment": issue.comment,
                    }
                    for issue
                    in latest_review.issues.all()
                ],
            }

        else:

            data["review"] = None

        # --------------------------------------------------
        # RETURN
        # --------------------------------------------------

        return Response(data)


    
# ==========================================================
# START REVIEW
# ==========================================================

class StartReviewView(APIView):

    permission_classes = [IsProductReviewer]

    @transaction.atomic
    def post(self, request, product_id):

        # --------------------------------------------------
        # FIND ACTIVE ASSIGNMENT
        # --------------------------------------------------

        assignment = (
            ReviewAssignment.objects
            .select_for_update()
            .select_related(
                "verification_request",
                "verification_request__product",
            )
            .filter(
                reviewer=request.user,
                verification_request__product_id=product_id,
                status="assigned",
            )
            .order_by(
                "-assigned_at",
                "-id",
            )
            .first()
        )

        # --------------------------------------------------
        # NOT FOUND
        # --------------------------------------------------

        if assignment is None:

            return Response(
                {
                    "message":
                    "This product is not currently "
                    "assigned to you."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # --------------------------------------------------
        # START ASSIGNMENT
        # --------------------------------------------------

        assignment.status = "in_review"

        assignment.started_at = timezone.now()

        assignment.save(
            update_fields=[
                "status",
                "started_at",
            ]
        )

        # --------------------------------------------------
        # START VERIFICATION REQUEST
        # --------------------------------------------------

        verification_request = (
            assignment.verification_request
        )

        verification_request.status = "in_review"

        verification_request.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # --------------------------------------------------
        # PRODUCT
        # --------------------------------------------------

        product = (
            verification_request.product
        )

        product.status = "in_review"

        product.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            {
                "message":
                "Review started.",

                "product_id":
                product.id,

                "verification_request_id":
                verification_request.id,

                "assignment_id":
                assignment.id,

                "status":
                "in_review",

                "can_take_action":
                True,
            }
        )


# ==========================================================
# APPROVE PRODUCT
# ==========================================================

class ApproveProductView(APIView):

    permission_classes = [IsProductReviewer]

    @transaction.atomic
    def post(self, request, product_id):

        # --------------------------------------------------
        # ACTIVE REVIEW ONLY
        # --------------------------------------------------

        assignment = (
            ReviewAssignment.objects
            .select_for_update()
            .select_related(
                "verification_request",
                "verification_request__product",
            )
            .filter(
                reviewer=request.user,
                verification_request__product_id=product_id,
                status="in_review",
            )
            .order_by(
                "-assigned_at",
                "-id",
            )
            .first()
        )

        if assignment is None:

            return Response(
                {
                    "message":
                    "You are not currently reviewing this product."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # --------------------------------------------------
        # PRODUCT
        # --------------------------------------------------

        verification_request = (
            assignment.verification_request
        )

        product = (
            verification_request.product
        )

        # --------------------------------------------------
        # APPROVE
        # --------------------------------------------------

        product.status = "approved"

        product.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # --------------------------------------------------
        # CREATE REVIEW
        # --------------------------------------------------

        reason = request.data.get(
            "reason",
            "",
        )

        if reason is None:
            reason = ""

        reason = str(reason).strip()

        review = ProductReview.objects.create(
            verification_request=verification_request,
            reviewer=request.user,
            decision="approved",
            reason=reason,
        )

        # --------------------------------------------------
        # COMPLETE ASSIGNMENT
        # --------------------------------------------------

        assignment.status = "completed"

        assignment.completed_at = timezone.now()

        assignment.save(
            update_fields=[
                "status",
                "completed_at",
            ]
        )

        # --------------------------------------------------
        # COMPLETE REQUEST
        # --------------------------------------------------

        verification_request.status = "completed"

        verification_request.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            {
                "message":
                "Product approved successfully.",

                "product_id":
                product.id,

                "status":
                product.status,

                "verification_request_id":
                verification_request.id,

                "assignment_id":
                assignment.id,

                "review_id":
                review.id,

                "decision":
                "approved",

                "assignment_status":
                "completed",

                "can_take_action":
                False,
            }
        )


# ==========================================================
# REJECT PRODUCT
# ==========================================================

class RejectProductView(APIView):

    permission_classes = [IsProductReviewer]

    @transaction.atomic
    def post(self, request, product_id):

        # --------------------------------------------------
        # ACTIVE REVIEW ONLY
        # --------------------------------------------------

        assignment = (
            ReviewAssignment.objects
            .select_for_update()
            .select_related(
                "verification_request",
                "verification_request__product",
            )
            .filter(
                reviewer=request.user,
                verification_request__product_id=product_id,
                status="in_review",
            )
            .order_by(
                "-assigned_at",
                "-id",
            )
            .first()
        )

        if assignment is None:

            return Response(
                {
                    "message":
                    "You are not currently reviewing this product."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # --------------------------------------------------
        # REASON
        # --------------------------------------------------

        reason = request.data.get(
            "reason",
            "",
        )

        if reason is None:
            reason = ""

        reason = str(reason).strip()

        if not reason:

            return Response(
                {
                    "message":
                    "Rejection reason is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------
        # PRODUCT
        # --------------------------------------------------

        verification_request = (
            assignment.verification_request
        )

        product = (
            verification_request.product
        )

        # --------------------------------------------------
        # REJECT
        # --------------------------------------------------

        product.status = "rejected"

        product.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # --------------------------------------------------
        # CREATE REVIEW
        # --------------------------------------------------

        review = ProductReview.objects.create(
            verification_request=verification_request,
            reviewer=request.user,
            decision="rejected",
            reason=reason,
        )

        # --------------------------------------------------
        # COMPLETE ASSIGNMENT
        # --------------------------------------------------

        assignment.status = "completed"

        assignment.completed_at = timezone.now()

        assignment.save(
            update_fields=[
                "status",
                "completed_at",
            ]
        )

        # --------------------------------------------------
        # COMPLETE REQUEST
        # --------------------------------------------------

        verification_request.status = "completed"

        verification_request.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            {
                "message":
                "Product rejected.",

                "product_id":
                product.id,

                "status":
                product.status,

                "verification_request_id":
                verification_request.id,

                "assignment_id":
                assignment.id,

                "review_id":
                review.id,

                "decision":
                "rejected",

                "assignment_status":
                "completed",

                "can_take_action":
                False,
            }
        )


# ==========================================================
# REQUEST CHANGES
# ==========================================================

class RequestChangesView(APIView):

    permission_classes = [IsProductReviewer]

    @transaction.atomic
    def post(self, request, product_id):

        # --------------------------------------------------
        # ACTIVE REVIEW ONLY
        # --------------------------------------------------

        assignment = (
            ReviewAssignment.objects
            .select_for_update()
            .select_related(
                "verification_request",
                "verification_request__product",
            )
            .filter(
                reviewer=request.user,
                verification_request__product_id=product_id,
                status="in_review",
            )
            .order_by(
                "-assigned_at",
                "-id",
            )
            .first()
        )

        if assignment is None:

            return Response(
                {
                    "message":
                    "You are not currently reviewing this product."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # --------------------------------------------------
        # REASON
        # --------------------------------------------------

        reason = request.data.get(
            "reason",
            "",
        )

        if reason is None:
            reason = ""

        reason = str(reason).strip()

        # --------------------------------------------------
        # ISSUES
        # --------------------------------------------------

        issues = request.data.get(
            "issues",
            [],
        )

        if not isinstance(
            issues,
            list,
        ):

            return Response(
                {
                    "message":
                    "Issues must be a list."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not reason and not issues:

            return Response(
                {
                    "message":
                    "Provide a reason or specific issues."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --------------------------------------------------
        # PRODUCT
        # --------------------------------------------------

        verification_request = (
            assignment.verification_request
        )

        product = (
            verification_request.product
        )

        # --------------------------------------------------
        # CHANGE REQUIRED
        # --------------------------------------------------

        product.status = "changes_required"

        product.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        # --------------------------------------------------
        # CREATE REVIEW
        # --------------------------------------------------

        review = ProductReview.objects.create(
            verification_request=verification_request,
            reviewer=request.user,
            decision="changes_required",
            reason=reason,
        )

        # --------------------------------------------------
        # VALID FIELDS
        # --------------------------------------------------

        valid_fields = {
            choice[0]
            for choice
            in ReviewIssue.FIELD_CHOICES
        }

        # --------------------------------------------------
        # CREATE ISSUES
        # --------------------------------------------------

        created_issues = []

        for issue in issues:

            if not isinstance(
                issue,
                dict,
            ):
                continue

            field = issue.get(
                "field"
            )

            comment = issue.get(
                "comment"
            )

            if not field or not comment:
                continue

            if field not in valid_fields:
                continue

            comment = str(
                comment
            ).strip()

            if not comment:
                continue

            review_issue = (
                ReviewIssue.objects.create(
                    review=review,
                    field=field,
                    comment=comment,
                )
            )

            created_issues.append(
                {
                    "id":
                    review_issue.id,

                    "field":
                    review_issue.field,

                    "comment":
                    review_issue.comment,
                }
            )

        # --------------------------------------------------
        # COMPLETE ASSIGNMENT
        # --------------------------------------------------

        assignment.status = "completed"

        assignment.completed_at = timezone.now()

        assignment.save(
            update_fields=[
                "status",
                "completed_at",
            ]
        )

        # --------------------------------------------------
        # COMPLETE REQUEST
        # --------------------------------------------------

        verification_request.status = "completed"

        verification_request.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            {
                "message":
                "Changes requested from seller.",

                "product_id":
                product.id,

                "status":
                product.status,

                "verification_request_id":
                verification_request.id,

                "assignment_id":
                assignment.id,

                "review_id":
                review.id,

                "decision":
                "changes_required",

                "issues":
                created_issues,

                "assignment_status":
                "completed",

                "can_take_action":
                False,

                "next_step":
                "Seller must update the product and resubmit it "
                "for verification.",
            }
        )