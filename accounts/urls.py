from django.urls import path
from .views import *
#from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [


    
    path('home-page/', HomePageView.as_view()),

    path('product/<int:id>/', ProductDetailsAPI.as_view(), name='product-details'),

    path('admin-register/',AdminRegisterAPIView.as_view()),

    #path('user-register/', UserRegisterAPIView.as_view()),

    path('seller-register/', SellerRegisterAPIView.as_view()),

    path('delivery-register/', DeliveryPartnerRegisterAPIView.as_view()),

    path('login/', LoginAPIView.as_view()),

    path(
    "check-phone/",
    CheckPhoneAPIView.as_view(),
    name="check-phone"
),

path(
    "send-otp/",
    SendOTPAPIView.as_view(),
    name="send-otp"
),


path("verify-otp/", VerifyOTPAPIView.as_view()),


]