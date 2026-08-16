from django import forms
from django.contrib import admin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.html import format_html

from .models import (
    CustomUser,
    Seller,
    DeliveryPartner,
    Marketing,
    ProductReviewer,
)


# ==========================================================
# PRODUCT REVIEWER - CREATE FORM
# ==========================================================

class ProductReviewerCreationForm(forms.ModelForm):

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        min_length=8,
        help_text="Minimum 8 characters.",
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = ProductReviewer
        fields = (
            "name",
            "email",
            "phone_number",
            "account_status",
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if not email:
            raise forms.ValidationError(
                "Email is required."
            )

        return email.strip().lower()

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number")

        if not phone:
            raise forms.ValidationError(
                "Phone number is required."
            )

        return phone.strip()

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2:

            if password1 != password2:
                raise forms.ValidationError(
                    "Passwords do not match."
                )

        return cleaned_data

    def save(self, commit=True):

        user = super().save(commit=False)

        # Force Product Reviewer role
        user.role = "product_reviewer"

        # New reviewer is active
        user.account_status = "active"

        # Reviewer does NOT get Django Admin access
        user.is_staff = False
        user.is_superuser = False

        # Secure password hashing
        user.set_password(
            self.cleaned_data["password1"]
        )

        if commit:
            user.save()

        return user


# ==========================================================
# PRODUCT REVIEWER - EDIT FORM
# ==========================================================

class ProductReviewerChangeForm(forms.ModelForm):

    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text=(
            "Passwords are securely hashed and cannot "
            "be viewed here."
        ),
    )

    class Meta:
        model = ProductReviewer
        fields = (
            "name",
            "email",
            "phone_number",
            "account_status",
            "password",
        )


# ==========================================================
# PRODUCT REVIEW TEAM ADMIN
# ==========================================================

@admin.register(ProductReviewer)
class ProductReviewerAdmin(admin.ModelAdmin):

    # ------------------------------------------------------
    # FORMS
    # ------------------------------------------------------

    form = ProductReviewerChangeForm
    add_form = ProductReviewerCreationForm

    # ------------------------------------------------------
    # LIST PAGE
    # ------------------------------------------------------

    list_display = (
        "name",
        "email",
        "phone_number",
        "status_display",
        "created_at",
    )

    list_filter = (
        "account_status",
    )

    search_fields = (
        "name",
        "email",
        "phone_number",
    )

    ordering = (
        "-created_at",
    )

    # ------------------------------------------------------
    # ADD FORM
    # ------------------------------------------------------

    add_fieldsets = (
        (
            "Product Review Team Member",
            {
                "classes": ("wide",),
                "fields": (
                    "name",
                    "email",
                    "phone_number",
                    "password1",
                    "password2",
                    "account_status",
                ),
            },
        ),
    )

    # ------------------------------------------------------
    # EDIT FORM
    # ------------------------------------------------------

    fieldsets = (
        (
            "Product Review Team Member",
            {
                "fields": (
                    "name",
                    "email",
                    "phone_number",
                    "account_status",
                ),
            },
        ),

        (
            "Security",
            {
                "fields": (
                    "password",
                ),
            },
        ),

        (
            "Account Information",
            {
                "fields": (
                    "last_login",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    readonly_fields = (
        "password",
        "last_login",
        "created_at",
        "updated_at",
    )

    # ------------------------------------------------------
    # SELECT CORRECT FORM
    # ------------------------------------------------------

    def get_form(self, request, obj=None, **kwargs):

        if obj is None:
            kwargs["form"] = self.add_form
        else:
            kwargs["form"] = self.form

        return super().get_form(
            request,
            obj,
            **kwargs
        )

    # ------------------------------------------------------
    # ONLY SHOW PRODUCT REVIEWERS
    # ------------------------------------------------------

    def get_queryset(self, request):

        return super().get_queryset(request).filter(
            role="product_reviewer"
        )

    # ------------------------------------------------------
    # FORCE ROLE
    # ------------------------------------------------------

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):

        obj.role = "product_reviewer"

        obj.is_staff = False

        obj.is_superuser = False

        super().save_model(
            request,
            obj,
            form,
            change,
        )

    # ------------------------------------------------------
    # STATUS DISPLAY
    # ------------------------------------------------------

    @admin.display(
        description="Status",
        ordering="account_status",
    )
    def status_display(self, obj):

        if obj.account_status == "active":

            color = "#15803D"

        elif obj.account_status == "suspended":

            color = "#DC2626"

        else:

            color = "#F59E0B"

        return format_html(
            '<span style="'
            'background:{};'
            'color:white;'
            'padding:4px 10px;'
            'border-radius:12px;'
            'font-size:12px;'
            'font-weight:600;'
            '">'
            '{}'
            '</span>',
            color,
            obj.get_account_status_display(),
        )

    # ------------------------------------------------------
    # DON'T DELETE REVIEWERS
    # ------------------------------------------------------

    def has_delete_permission(
        self,
        request,
        obj=None,
    ):
        return False


# ==========================================================
# SELLER ADMIN
# ==========================================================
@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):

    list_display = (
        "user",
    )

    search_fields = (
        "user__email",
        "user__phone_number",
        "user__name",
    )

# ==========================================================
# DELIVERY PARTNER ADMIN
# ==========================================================

@admin.register(DeliveryPartner)
class DeliveryPartnerAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "vehicle_type",
        "vehicle_number",
        "is_available",
        "created_at",
    )

    search_fields = (
        "user__name",
        "user__phone_number",
        "vehicle_number",
        "license_number",
    )

    list_filter = (
        "vehicle_type",
        "is_available",
    )


# ==========================================================
# MARKETING ADMIN
# ==========================================================

@admin.register(Marketing)
class MarketingAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "department",
        "employee_id",
        "joined_at",
    )

    search_fields = (
        "user__name",
        "user__email",
        "employee_id",
    )


# ==========================================================
# CUSTOM USER
# ==========================================================
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser,
    Seller,
    DeliveryPartner,
    Marketing,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):

    model = CustomUser

    list_display = (
        "email",
        "phone_number",
        "name",
        "role",
        "account_status",
        "is_staff",
    )

    list_filter = (
        "role",
        "account_status",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "email",
        "phone_number",
        "name",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("Login Information", {
            "fields": (
                "email",
                "password",
            )
        }),

        ("Personal Information", {
            "fields": (
                "name",
                "phone_number",
                "profile_image",
            )
        }),

        ("ClayWare Role", {
            "fields": (
                "role",
                "account_status",
            )
        }),

        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),

        ("Important Dates", {
            "fields": (
                "last_login",
                "date_joined",
                "created_at",
                "updated_at",
            )
        }),
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "last_login",
        "date_joined",
    )