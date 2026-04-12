from django.urls import path

from backend.views import LoginAPIView, ProductListAPIView, RegisterAPIView, api_status

urlpatterns = [
    path('status/', api_status, name='api-status'),
    path('auth/register/', RegisterAPIView.as_view(), name='api-register'),
    path('auth/login/', LoginAPIView.as_view(), name='api-login'),
    path('products/', ProductListAPIView.as_view(), name='api-products'),
]
