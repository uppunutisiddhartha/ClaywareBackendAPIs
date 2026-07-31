from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import OfferBanner
from .serializers import OfferBannerSerializer


# CREATE BANNER (ADMIN POST)
class OfferBannerCreateAPI(APIView):

    def post(self, request):
        serializer = OfferBannerSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Banner created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# GET ALL BANNERS (ADMIN VIEW)
class OfferBannerListAPI(APIView):

    def get(self, request):
        banners = OfferBanner.objects.all().order_by('-posted_on')
        serializer = OfferBannerSerializer(banners, many=True)
        return Response(serializer.data)
    

class ActiveOfferBannerAPI(APIView):

    def get(self, request):
        banners=OfferBanner.objects.filter(offerBannerStatus='active')

        serializer = OfferBannerSerializer(banners, many=True)

        return Response(
            {
                "banners": serializer.data
            },
            status=status.HTTP_200_OK
        )