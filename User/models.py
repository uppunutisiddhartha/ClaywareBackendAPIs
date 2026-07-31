from django.db import models

# Create your models here.
"""class DelivaryAddress(models.Model):
    user = models.OneToOneField('accounts.CustomUser', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, null=False)
    pinCode = models.IntegerField(blank=False)
    landmark = models.CharField(max_length=50, null=False)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=30)
    mobile = models.IntegerField(null=False)
    Alternate_mobile = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Address of {self.user.name}"
    
"""




#----------------cart model-----------------
class Cart(models.Model):
    user = models.OneToOneField('accounts.CustomUser', on_delete=models.CASCADE, related_name="cart")

    def __str__(self):
        return f"Cart of {self.user.email}"
    

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        'seller.Product',
        on_delete=models.CASCADE
    )

    variant = models.ForeignKey(
        'seller.ProductVariant',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        if self.variant:
            return f"{self.product.productname} ({self.variant.capacity}) x {self.quantity}"
        return f"{self.product.productname} (Standard) x {self.quantity}"


# models.py


class Address(models.Model):

    user = models.ForeignKey('accounts.CustomUser',on_delete=models.CASCADE,related_name='addresses')

    full_name = models.CharField(max_length=200)

    phone_number = models.CharField(max_length=15)

    address_line = models.TextField()

    city = models.CharField(max_length=100)

    state = models.CharField(max_length=100)

    pincode = models.CharField(max_length=10)

    address_type= models.CharField(max_length=50)

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.city}"