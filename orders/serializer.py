from rest_framework import serializers

from .models import Order, Review


class OrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "payment_status",
            "refund_status",
            "payment_method",
            "total_price",
        ]


class ReviewSerializer(serializers.ModelSerializer):

    user_name = serializers.CharField(
        source="user.first_name",
        read_only=True
    )

    profile_image = serializers.ImageField(
        source="user.profile_image",
        read_only=True
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "user_name",
            "profile_image",
            "rating",
            "review",
            "created_at",
        ]