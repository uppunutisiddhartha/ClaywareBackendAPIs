from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError

from .models import Product, ProductVariant, ProductImage


# ✅ SAFE IMAGE LIMIT VALIDATION
class ProductImageFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        count = 0

        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                if form.cleaned_data.get("image"):
                    count += 1

        if count > 5:
            raise ValidationError("Maximum 5 images allowed per product.")


# ✅ IMAGE INLINE
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    formset = ProductImageFormSet
    extra = 1
    max_num = 5


# ✅ VARIANT INLINE
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


# ✅ PRODUCT ADMIN
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductVariantInline, ProductImageInline]
    list_display = ("id", "productname", "category")


# (optional)
admin.site.register(ProductVariant)

#admin.site.register(Product)