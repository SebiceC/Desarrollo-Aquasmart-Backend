from django.urls import path
from .views import DeviceCreateView, DeviceListView, DeviceDetailView

urlpatterns = [
    path('devices/', DeviceCreateView.as_view(), name='device-create'),  # Crear dispositivo
    path('devices/list/', DeviceListView.as_view(), name='device-list'),  # Listar dispositivos
    path('devices/<int:pk>/', DeviceDetailView.as_view(), name='device-detail'),  # Obtener, actualizar o eliminar dispositivo
]