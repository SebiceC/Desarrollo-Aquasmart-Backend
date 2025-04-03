from django.urls import path
from .views import (
    RegisterIoTDeviceView,ActivateIoTDevice,
    DeactivateIoTDevice,DeviceTypeListCreateView, 
    DeviceTypeDetailView,DeviceTypeUpdateView, 
    DeviceTypeDeleteView,IoTDeviceListView,
    IoTDeviceDetailView, IoTDeviceUpdateView)

urlpatterns = [
    #endpoint dispositivo iot
    path('iot-devices/register', RegisterIoTDeviceView.as_view(), name='registrar-dispositivo-iot'),# POST
    path('iot-devices/<str:iot_id>/activate', ActivateIoTDevice.as_view(), name='activate_iot_device'),# PATCH
    path('iot-devices/<str:iot_id>/desactivate', DeactivateIoTDevice.as_view(), name='deactivate_iot_device'),# PATCH
    path('iot-devices', IoTDeviceListView.as_view(), name='list_iot_devices'),  # 🔹 Ver todos GET
    path('iot-devices/<str:iot_id>', IoTDeviceDetailView.as_view(), name='get_iot_device'),  # 🔹 Ver uno GET
    path('iot-devices/<str:iot_id>/update', IoTDeviceUpdateView.as_view(), name='update_iot_device'),  # 🔹 Actualizar PUT tods los datos , PATCH parcial
    #endpints tipo de dispositivos
    path('device-types', DeviceTypeListCreateView.as_view(), name='list_create_device_types'),  # 🔹 GET Ver todos / POST Crear 
    path('device-types/<str:device_id>', DeviceTypeDetailView.as_view(), name='get_device_type'),  # 🔹 Ver uno GET
    path('device-types/<str:device_id>/update', DeviceTypeUpdateView.as_view(), name='update_device_type'),  # 🔹 Actualizar PUT
    path('device-types/<str:device_id>/delete', DeviceTypeDeleteView.as_view(), name='delete_device_type'),  # 🔹 Eliminar DELETE
]
