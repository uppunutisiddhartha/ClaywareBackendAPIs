from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


# ==========================================================
# USER MANAGER
# ==========================================================

class CustomUserManager(BaseUserManager):

    def create_user(self, email, phone_number, password=None, **extra_fields):

        if not phone_number:
            raise ValueError("Phone number is required")

        if email:
            email = self.normalize_email(email)

        user = self.model(
            email=email,
            phone_number=phone_number,
            **extra_fields
        )

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email,
        phone_number,
        password=None,
        **extra_fields
    ):

        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("account_status", "active")

        return self.create_user(
            email=email,
            phone_number=phone_number,
            password=password,
            **extra_fields
        )


# ==========================================================
# CUSTOM USER
# ==========================================================

class CustomUser(AbstractUser):

    ROLE_CHOICES = (

        ("admin", "Admin"),

        ("user", "User"),

        ("seller", "Seller"),

        ("delivery_partner", "Delivery Partner"),

        ("marketing", "Marketing"),

        ("product_reviewer", "Product Reviewer"),

    )

    STATUS_CHOICES = (

        ("pending", "Pending"),

        ("active", "Active"),

        ("suspended", "Suspended"),

    )

    username = None

    name = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        unique=True,
        blank=True,
        null=True
    )

    phone_number = models.CharField(
        max_length=15,
        unique=True
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default="user"
    )

    account_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active"
    )

    profile_image = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["phone_number"]

    objects = CustomUserManager()

    def __str__(self):

        return self.email or self.phone_number


# ==========================================================
# SELLER PROFILE
# ==========================================================

class Seller(models.Model):

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="seller_profile"
    )

    shop_name = models.CharField(
        max_length=200
    )

    shop_address = models.TextField()

    gst_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True
    )

    id_proof = models.ImageField(
        upload_to="seller_proofs/"
    )

    is_verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.shop_name


# ==========================================================
# DELIVERY PARTNER PROFILE
# ==========================================================

class DeliveryPartner(models.Model):

    VEHICLE_CHOICES = (

        ("bike", "Bike"),

        ("car", "Car"),

        ("van", "Van"),

    )

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="delivery_profile"
    )

    vehicle_type = models.CharField(
        max_length=20
    )

    vehicle_number = models.CharField(
        max_length=50,
        unique=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    license_number = models.CharField(
        max_length=100,
        unique=True
    )

    RcImage = models.ImageField(
        upload_to="delivery_rc/",
        blank=True,
        null=True
    )

    licenseImage = models.ImageField(
        upload_to="delivery_dl/",
        blank=True,
        null=True
    )

    is_available = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.user.phone_number


# ==========================================================
# MARKETING PROFILE
# ==========================================================

class Marketing(models.Model):

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="marketing_profile"
    )

    department = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    employee_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.user.name


# ==========================================================
# PRODUCT REVIEWER MANAGER
# ==========================================================

class ProductReviewerManager(models.Manager):

    def get_queryset(self):

        return (
            super()
            .get_queryset()
            .filter(
                role="product_reviewer"
            )
        )


# ==========================================================
# PRODUCT REVIEW TEAM MEMBER
# ==========================================================

class ProductReviewer(CustomUser):

    objects = ProductReviewerManager()

    class Meta:

        proxy = True

        verbose_name = "Product Review Team Member"

        verbose_name_plural = "Product Review Team"