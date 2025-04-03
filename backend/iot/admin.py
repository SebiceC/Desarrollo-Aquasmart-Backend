from django.contrib import admin
from .models import DeviceType, IoTDevice

@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'name')  # Mostrar en la lista
    search_fields = ('device_id', 'name')  # Agregar barra de búsqueda
    ordering = ('device_id',)  # Ordenar por ID
    list_per_page = 20  # Paginación en el admin

@admin.register(IoTDevice)
class IoTDeviceAdmin(admin.ModelAdmin):
    list_display = ('iot_id', 'name', 'device_type', 'is_active', 'id_plot', 'id_lot', 'actual_flow')
    search_fields = ('iot_id', 'name', 'device_type__name')
    list_filter = ('is_active', 'device_type')  # Filtros en el admin
    ordering = ('iot_id',)
    list_per_page = 20
