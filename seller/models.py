from django.db import models


class Product(models.Model):

    ITEM_CHOICE = (
        ("cookware", "Cookware"),
        ("water_bottles", "Water Bottles"),
        ("tea_cups", "Tea Cups"),
        ("water_glasses", "Water Glasses"),
        ("decors", "Decors"),
        ("kitchen_accessories", "Kitchen Accessories"),
        ("gifts", "Gift Items"),
    )

    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("pending_verification", "Pending Verification"),
        ("changes_required", "Changes Required"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("suspended", "Suspended"),
    )

    seller = models.ForeignKey(
        "accounts.Seller",
        on_delete=models.CASCADE,
        related_name="products",
    )

    productname = models.CharField(max_length=200)

    sku = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    description = models.TextField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # IMPORTANT:
    # Stock is NOT stored here anymore.

    capacity = models.CharField(
        max_length=50,
    )

    weight = models.CharField(
        max_length=100,
        default="Light Weight",
        null=True,
        blank=True,
    )

    category = models.CharField(
        max_length=50,
        choices=ITEM_CHOICE,
        default="cookware",
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="draft",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.productname


class ProductVariant(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )

    capacity = models.CharField(
        max_length=50,
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.product.productname} - {self.capacity}"


class Inventory(models.Model):

    # One inventory record per variant
    variant = models.OneToOneField(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="inventory",
        null=True,
        blank=True,
    )

    # For products that don't have variants
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="inventory",
        null=True,
        blank=True,
    )

    quantity = models.PositiveIntegerField(
        default=0,
    )

    low_stock_threshold = models.PositiveIntegerField(
        default=10,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):

        if self.variant:
            return (
                f"{self.variant.product.productname} "
                f"- {self.variant.capacity} "
                f"- {self.quantity}"
            )

        if self.product:
            return (
                f"{self.product.productname} "
                f"- {self.quantity}"
            )

        return f"Inventory #{self.id}"

    @property
    def is_out_of_stock(self):
        return self.quantity == 0

    @property
    def is_low_stock(self):
        return (
            self.quantity > 0
            and self.quantity <= self.low_stock_threshold
        )


class ProductImage(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(
        upload_to="products/",
    )