from django.urls import path
from .views import RegisterIoTDevice

urlpatterns = [
    path('register/', RegisterIoTDevice.as_view(), name='registrar-dispositivo-iot'),
]
