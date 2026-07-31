from django.db import models
from .models import *

# Create your models here.
class Payment(models.Model):

    PAYMENT_METHODS = (
    ("COD", "Cash On Delivery"),
    ("RAZORPAY", "Razorpay"),
)

    
    PAYMENT_STATUS = (
    ("PENDING", "Pending"),
    ("SUCCESS", "Success"),
    ("FAILED", "Failed"),
)

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name='payment'
    )

    payment_method = models.CharField(
    max_length=20,
    choices=PAYMENT_METHODS,
    default="COD"
)

    payment_status = models.CharField(
        max_length=30,
        choices=PAYMENT_STATUS,
        default='PENDING'
    )

    # Existing
    transaction_id = models.CharField(max_length=200, blank=True, null=True)

    # Razorpay Fields
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True,db_index=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True,db_index=True)
    razorpay_signature = models.TextField(blank=True,null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.id} - {self.payment_status}"