from django.contrib import admin
from .models import IoTDevice

@admin.register(IoTDevice)
class IoTDeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'id_plot', 'name', 'device_type', 'is_active', 'characteristics', 'id_lot')
    list_filter = ('device_type', 'is_active') 
    search_fields = ('name', 'id_plot', 'id_lot', 'device_id')  
