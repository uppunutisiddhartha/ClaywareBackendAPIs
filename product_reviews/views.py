from django.shortcuts import render

# Create your views here.

from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from seller.models import Product

from .models import (
    VerificationRequest,
    ReviewAssignment,
    ProductReview,
    ReviewIssue,
)

from .serializers import (
    VerificationRequestSerializer,
    ProductReviewSerializer,
)

from .permissions import IsProductReviewer


# ==========================================================
# MY REVIEW QUEUE
# ==========================================================

class MyReviewQueueView(APIView):

    permission_classes = [IsProductReviewer]

    def get(self, request):

        assignments = (
            ReviewAssignment.objects
            .filter(
                reviewer=request.user,
                status__in=["assigned", "in_review"]
            )
            .select_related(
                "verification_request__product"
            )
        )

        serializer = VerificationRequestSerializer(
            [
                assignment.verification_request
                for assignment in assignments
            ],
            many=True
        )

        return Response({
            "count": len(serializer.data),
            "results": serializer.data
        })


# ==========================================================
# PRODUCT DETAILS
# ==========================================================

class ReviewProductDetailView(APIView):

    permission_classes = [IsProductReviewer]

    def get(self, request, product_id):

        try:

            assignment = (
                ReviewAssignment.objects
                .select_related(
                    "verification_request__product"
                )
                .get(
                    reviewer=request.user,
                    verification_request__product_id=product_id,
                    status__in=["assigned", "in_review"]
                )
            )

        except ReviewAssignment.DoesNotExist:

            return Response(
                {
                    "message":
                    "This product is not assigned to you."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = VerificationRequestSerializer(
            assignment.verification_request
        )

        return Response(serializer.data)


# ==========================================================
# START REVIEW
# ==========================================================

class StartReviewView(APIView):

    permission_classes = [IsProductReviewer]

    def post(self, request, product_id):

        try:

            assignment = (
                ReviewAssignment.objects
                .select_related(
                    "verification_request__product"
                )
                .get(
                    reviewer=request.user,
                    verification_request__product_id=product_id,
                    status="assigned"
                )
            )

        except ReviewAssignment.DoesNotExist:

            return Response(
                {
                    "message":
                    "This product is not assigned to you."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        assignment.status = "in_review"
        assignment.started_at = timezone.now()
        assignment.save(
            update_fields=[
                "status",
                "started_at"
            ]
        )

        assignment.verification_request.status = "in_review"
        assignment.verification_request.save(
            update_fields=["status", "updated_at"]
        )

        return Response({
            "message": "Review started.",
            "product_id": product_id,
            "status": "in_review"
        })


# ==========================================================
# APPROVE
# ==========================================================

class ApproveProductView(APIView):

    permission_classes = [IsProductReviewer]

    def post(self, request, product_id):

        try:

            assignment = (
                ReviewAssignment.objects
                .select_related(
                    "verification_request__product"
                )
                .get(
                    reviewer=request.user,
                    verification_request__product_id=product_id,
                    status="in_review"
                )
            )

        except ReviewAssignment.DoesNotExist:

            return Response(
                {
                    "message":
                    "You are not reviewing this product."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        product = assignment.verification_request.product

        product.status = "approved"

        product.save(
            update_fields=[
                "status",
                "updated_at"
            ]
        )

        review = ProductReview.objects.create(
            verification_request=assignment.verification_request,
            reviewer=request.user,
            decision="approved",
            reason=request.data.get(
                "reason",
                ""
            )
        )

        assignment.status = "completed"
        assignment.completed_at = timezone.now()

        assignment.save(
            update_fields=[
                "status",
                "completed_at"
            ]
        )

        assignment.verification_request.status = "completed"

        assignment.verification_request.save(
            update_fields=[
                "status",
                "updated_at"
            ]
        )

        return Response({
            "message": "Product approved successfully.",
            "product_id": product.id,
            "status": product.status,
            "review_id": review.id
        })


class RejectProductView(APIView):

    permission_classes = [IsProductReviewer]

    def post(self, request, product_id):

        try:

            assignment = (
                ReviewAssignment.objects
                .select_related(
                    "verification_request__product"
                )
                .get(
                    reviewer=request.user,
                    verification_request__product_id=product_id,
                    status="in_review"
                )
            )

        except ReviewAssignment.DoesNotExist:

            return Response(
                {
                    "message":
                    "You are not reviewing this product."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        reason = request.data.get(
            "reason",
            ""
        ).strip()

        if not reason:

            return Response(
                {
                    "message":
                    "Rejection reason is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        product = assignment.verification_request.product

        product.status = "rejected"

        product.save(
            update_fields=[
                "status",
                "updated_at"
            ]
        )

        review = ProductReview.objects.create(
            verification_request=assignment.verification_request,
            reviewer=request.user,
            decision="rejected",
            reason=reason
        )

        assignment.status = "completed"
        assignment.completed_at = timezone.now()

        assignment.save(
            update_fields=[
                "status",
                "completed_at"
            ]
        )

        assignment.verification_request.status = "completed"

        assignment.verification_request.save(
            update_fields=[
                "status",
                "updated_at"
            ]
        )

        return Response({
            "message": "Product rejected.",
            "product_id": product.id,
            "status": product.status,
            "review_id": review.id
        })

class RequestChangesView(APIView):

    permission_classes = [IsProductReviewer]

    def post(self, request, product_id):

        try:

            assignment = (
                ReviewAssignment.objects
                .select_related(
                    "verification_request__product"
                )
                .get(
                    reviewer=request.user,
                    verification_request__product_id=product_id,
                    status="in_review"
                )
            )

        except ReviewAssignment.DoesNotExist:

            return Response(
                {
                    "message":
                    "You are not reviewing this product."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        reason = request.data.get(
            "reason",
            ""
        ).strip()

        issues = request.data.get(
            "issues",
            []
        )

        if not reason and not issues:

            return Response(
                {
                    "message":
                    "Provide reason or specific issues."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        product = assignment.verification_request.product

        product.status = "changes_required"

        product.save(
            update_fields=[
                "status",
                "updated_at"
            ]
        )

        review = ProductReview.objects.create(
            verification_request=assignment.verification_request,
            reviewer=request.user,
            decision="changes_required",
            reason=reason
        )

        for issue in issues:

            field = issue.get("field")
            comment = issue.get("comment")

            if field and comment:

                ReviewIssue.objects.create(
                    review=review,
                    field=field,
                    comment=comment
                )

        assignment.status = "completed"
        assignment.completed_at = timezone.now()

        assignment.save(
            update_fields=[
                "status",
                "completed_at"
            ]
        )

        assignment.verification_request.status = "completed"

        assignment.verification_request.save(
            update_fields=[
                "status",
                "updated_at"
            ]
        )

        return Response({
            "message":
            "Changes requested from seller.",

            "product_id":
            product.id,

            "status":
            product.status,

            "review_id":
            review.id
        })