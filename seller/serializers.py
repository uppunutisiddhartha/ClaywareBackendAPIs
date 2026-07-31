from rest_framework import serializers
from .models import Product, ProductVariant, ProductImage


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            "capacity",
            "price",
            "discount_price",
            "stock_quantity",
        ]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]


class ProductSerializer(serializers.ModelSerializer):

    variants = ProductVariantSerializer(many=True, required=False)

    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    product_images = ProductImageSerializer(
        many=True,
        read_only=True,
        source="images"
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "productname",
            "description",
            "price",
            "discount_price",
            "stock_quantity",
            "weight",
            "variants",
            "images",
            "product_images",
        ]

    def create(self, validated_data):
        variants_data = validated_data.pop("variants", [])
        images_data = validated_data.pop("images", [])

        product = Product.objects.create(**validated_data)

        for variant in variants_data:
            ProductVariant.objects.create(product=product, **variant)

        # 🔥 IMPORTANT FIX: force list conversion
        if images_data:
            for image in list(images_data):
                ProductImage.objects.create(product=product, image=image)

        return product