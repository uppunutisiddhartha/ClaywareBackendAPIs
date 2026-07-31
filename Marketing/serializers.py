from rest_framework import serializers
from .models import OfferBanner


class OfferBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferBanner
        fields = '__all__'