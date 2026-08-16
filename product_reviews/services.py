from django.db import transaction
from django.db.models import Count, Q

from accounts.models import CustomUser

from .models import (
    VerificationRequest,
    ReviewAssignment,
)


@transaction.atomic
def assign_product_for_review(product):

    # ======================================================
    # 1. CHECK EXISTING VERIFICATION REQUEST
    # ======================================================

    verification_request = (
        VerificationRequest.objects
        .filter(product=product)
        .first()
    )

    # ======================================================
    # 2. CREATE VERIFICATION REQUEST IF NOT EXISTS
    # ======================================================

    if not verification_request:

        verification_request = (
            VerificationRequest.objects.create(
                product=product,
                status="pending",
            )
        )

    # ======================================================
    # 3. CHECK IF ALREADY ASSIGNED
    # ======================================================

    existing_assignment = (
        ReviewAssignment.objects
        .filter(
            verification_request=verification_request,
            status__in=[
                "assigned",
                "in_review",
            ],
        )
        .first()
    )

    if existing_assignment:

        return existing_assignment

    # ======================================================
    # 4. FIND REVIEWER WITH SMALLEST ACTIVE QUEUE
    # ======================================================

    reviewer = (
        CustomUser.objects
        .filter(
            role="product_reviewer",
            account_status="active",
            is_active=True,
        )
        .annotate(
            active_queue=Count(
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
            "active_queue",
            "id",
        )
        .first()
    )

    # ======================================================
    # 5. NO REVIEWER AVAILABLE
    # ======================================================

    if not reviewer:

        verification_request.status = "pending"

        verification_request.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return None

    # ======================================================
    # 6. CREATE ASSIGNMENT
    # ======================================================

    assignment = ReviewAssignment.objects.create(
        verification_request=verification_request,
        reviewer=reviewer,
        status="assigned",
    )

    # ======================================================
    # 7. UPDATE VERIFICATION REQUEST
    # ======================================================

    verification_request.status = "assigned"

    verification_request.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return assignment