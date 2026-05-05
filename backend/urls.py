from django.urls import path

from backend.views import (
    BasketAPIView,
    ContactAPIView,
    LoginAPIView,
    OrderConfirmAPIView,
    OrderDetailAPIView,
    OrderListAPIView,
    OrderStatusUpdateAPIView,
    ProductDetailAPIView,
    ProductListAPIView,
    RegisterAPIView,
    SocialSessionTokenAPIView,
    api_status,
)

urlpatterns = [
    path('status/', api_status, name='api-status'),
    path('auth/register/', RegisterAPIView.as_view(), name='api-register'),
    path('auth/login/', LoginAPIView.as_view(), name='api-login'),
    path('auth/social/token/', SocialSessionTokenAPIView.as_view(), name='api-social-token'),
    path('products/', ProductListAPIView.as_view(), name='api-products'),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='api-product-detail'),
    path('basket/', BasketAPIView.as_view(), name='api-basket'),
    path('contacts/', ContactAPIView.as_view(), name='api-contacts'),
    path('order/confirm/', OrderConfirmAPIView.as_view(), name='api-order-confirm'),
    path('orders/', OrderListAPIView.as_view(), name='api-orders'),
    path('orders/<int:pk>/status/', OrderStatusUpdateAPIView.as_view(), name='api-order-status'),
    path('orders/<int:pk>/', OrderDetailAPIView.as_view(), name='api-order-detail'),
]
