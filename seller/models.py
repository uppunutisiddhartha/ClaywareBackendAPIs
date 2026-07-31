from django.db import models


class Product(models.Model):

    ITEM_CHOICE = (
        ('cookware', 'Cookware'),
        ('water_bottles', 'Water Bottles'),
        ('tea_cups', 'Tea Cups'),
        ('water_glasses', 'Water Glasses'),
        ('decors', 'Decors'),
        ('kitchen_accessories', 'Kitchen Accessories'),
        ('gifts', 'Gift Items'),
    )

    seller = models.ForeignKey(
        'accounts.Seller',
        on_delete=models.CASCADE,
        related_name="products"
    )

    productname = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField()
    capacity = models.CharField(max_length=50)
    weight = models.CharField(max_length=100, default="Light Weight", null=True, blank=True)

    category = models.CharField(max_length=50, choices=ITEM_CHOICE, default='cookware')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.productname


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")

    capacity = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField()

    def __str__(self):
        return f"{self.product.productname} - {self.capacity}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="products/")