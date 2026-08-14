from django.db import models
from django.conf import settings


class VerificationRequest(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("assigned", "Assigned"),
        ("in_review", "In Review"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    product = models.ForeignKey(
        "seller.Product",
        on_delete=models.CASCADE,
        related_name="verification_requests"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Verification #{self.id} - {self.product.productname}"


class ReviewAssignment(models.Model):

    STATUS_CHOICES = (
        ("assigned", "Assigned"),
        ("in_review", "In Review"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    )

    verification_request = models.OneToOneField(
        VerificationRequest,
        on_delete=models.CASCADE,
        related_name="assignment"
    )

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_assignments"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="assigned"
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return (
            f"{self.verification_request.product.productname} "
            f"- {self.reviewer.name}"
        )


class ProductReview(models.Model):

    DECISION_CHOICES = (
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("changes_required", "Changes Required"),
    )

    verification_request = models.ForeignKey(
        VerificationRequest,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="product_reviews"
    )

    decision = models.CharField(
        max_length=30,
        choices=DECISION_CHOICES
    )

    reason = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.verification_request.product.productname} "
            f"- {self.decision}"
        )


class ReviewIssue(models.Model):

    FIELD_CHOICES = (
        ("product_name", "Product Name"),
        ("description", "Description"),
        ("price", "Price"),
        ("discount_price", "Discount Price"),
        ("category", "Category"),
        ("capacity", "Capacity"),
        ("weight", "Weight"),
        ("stock", "Stock"),
        ("variant", "Variant"),
        ("image", "Image"),
    )

    review = models.ForeignKey(
        ProductReview,
        on_delete=models.CASCADE,
        related_name="issues"
    )

    field = models.CharField(
        max_length=50,
        choices=FIELD_CHOICES
    )

    comment = models.TextField()

    def __str__(self):
        return f"{self.field} - Review {self.review.id}"