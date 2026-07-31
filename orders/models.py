from django.db import models
from seller.models import Product
from accounts.models import CustomUser

class Order(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'PENDING'),
        ('PLACED', 'PLACED'),
        ('PACKED', 'PACKED'),
        ('OUT_FOR_DELIVERY', 'OUT_FOR_DELIVERY'),
        ('DELIVERED', 'DELIVERED'),
        ('CANCELLED', 'CANCELLED'),
    )
    REFUND_STATUS = (
        ('NOT_REQUIRED', 'Not Required'),
        ('INITIATED', 'Refund Initiated'),
        ('PROCESSING', 'Refund Processing'),
        ('SUCCESS', 'Refund Completed'),
        ('FAILED', 'Refund Failed'),
    )

    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='orders'
    )

    address = models.ForeignKey(
        'User.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    refund_status = models.CharField(
        max_length=30,
        choices=REFUND_STATUS,
        default='NOT_REQUIRED'
    )
    is_buy_now = models.BooleanField(default=False)
    
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')

    payment_status = models.CharField(max_length=20, default='PENDING')

    payment_method = models.CharField(max_length=30)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    #order_id= models.CharField(max_length=10)

    def __str__(self):
        return f"Order {self.id} - {self.user.name}"
 

class OrderItem(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    product = models.ForeignKey("seller.Product", on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField()
    
    variant = models.ForeignKey("seller.ProductVariant",on_delete=models.SET_NULL, null=True,blank=True)    

    price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.productname} x {self.quantity}"
    



class Review(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    rating = models.PositiveSmallIntegerField()

    review = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.productname} - {self.user.email}"


class ReviewImage(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(
        upload_to="review_images/"
    )

    def __str__(self):
        return f"Image - Review {self.review.id}"