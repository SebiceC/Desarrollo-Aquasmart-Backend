from django.urls import path
from .views import DeviceUpdateView

urlpatterns = [
    path('devices/<int:pk>/', DeviceUpdateView.as_view(), name='device-update'),
]