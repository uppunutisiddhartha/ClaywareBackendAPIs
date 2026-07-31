from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),
    path('api/seller/', include('seller.urls')),
    path('api/user/', include('User.urls')),
    path('api/adminmain/', include('adminMain.urls')),
    path('api/deliverypatner/', include('deliverypatner.urls')),
    path('api/order/',include('orders.urls')),
    path('api/marketing/',include('Marketing.urls')),
    path("api/payments/", include("payments.urls")),


    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)