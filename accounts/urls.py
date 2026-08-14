from django.urls import path
from .views import *
#from .views import CurrentUserView
#from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [


    
    path('home-page/', HomePageView.as_view()),

    path('product/<int:id>/', ProductDetailsAPI.as_view(), name='product-details'),

    path('admin-register/',AdminRegisterAPIView.as_view()),

   # path("me/", CurrentUserView.as_view(), name="current-user"),



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



#  path(
#         "review-team/login/",
#         ReviewTeamLoginAPIView.as_view(),
#         name="review-team-login"
#     ),


]