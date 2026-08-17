from django.db import transaction
from django.db.models import Count, Q
from django.contrib.auth import get_user_model

from .models import VerificationRequest, ReviewAssignment


User = get_user_model()


@transaction.atomic
def assign_product_to_reviewer(
    product,
    preferred_reviewer=None,
):
    """
    Automatically assign a product to a Product Reviewer.

    Priority:
    1. Previous reviewer, if supplied and still active
    2. Least-loaded active Product Reviewer
    3. If no reviewer exists -> request remains pending
    """

    # ======================================================
    # CHECK FOR EXISTING ACTIVE REQUEST
    # ======================================================

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
        .order_by(
            "-created_at",
            "-id",
        )
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
            .order_by(
                "-assigned_at",
                "-id",
            )
            .first()
        )

        return existing_request, assignment

    # ======================================================
    # CREATE NEW VERIFICATION REQUEST
    # ======================================================

    verification_request = (
        VerificationRequest.objects.create(
            product=product,
            status="pending",
        )
    )

    # ======================================================
    # FIND REVIEWER
    # ======================================================

    reviewer = None

    # ======================================================
    # 1. TRY PREVIOUS REVIEWER
    # ======================================================

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

    # ======================================================
    # 2. FIND LEAST LOADED REVIEWER
    # ======================================================

    if reviewer is None:

        reviewer = (
            User.objects
            .filter(
                role="product_reviewer",
                account_status="active",
            )
            .annotate(
                active_review_count=Count(
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
                "active_review_count",
                "id",
            )
            .first()
        )

    # ======================================================
    # NO REVIEWER
    # ======================================================

    if reviewer is None:

        print(
            "❌ NO ACTIVE PRODUCT REVIEWER FOUND"
        )

        print(
            "Available users:"
        )

        for user in User.objects.all():
            print(
                user.id,
                user.name,
                user.role,
                user.account_status,
            )

        return verification_request, None

    # ======================================================
    # CREATE ASSIGNMENT IMMEDIATELY
    # ======================================================

    assignment = (
        ReviewAssignment.objects.create(
            verification_request=verification_request,
            reviewer=reviewer,
            status="assigned",
        )
    )

    # ======================================================
    # UPDATE VERIFICATION REQUEST
    # ======================================================

    verification_request.status = "assigned"

    verification_request.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    print(
        f"✅ PRODUCT {product.id} "
        f"ASSIGNED TO REVIEWER "
        f"{reviewer.id} - {reviewer.name}"
    )

    return verification_request, assignment