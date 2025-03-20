from django.urls import path
from .views import RegisterIoTDevice, IoTDeviceListView, IoTDeviceDetailView

urlpatterns = [
    path('register', RegisterIoTDevice.as_view(), name='registrar-dispositivo-iot'),
    path('list', IoTDeviceListView.as_view(), name='listar-dispositivos-iot'),
    path('detail/<str:device_id>', IoTDeviceDetailView.as_view(), name='detalle-dispositivo-iot'),
]