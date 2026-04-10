from django.urls import path

from backend.views import api_status

urlpatterns = [
    path('status/', api_status, name='api-status'),
]
