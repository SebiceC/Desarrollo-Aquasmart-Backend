from django.contrib import admin
from .models import Device

# Registrar el modelo Device
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'characteristics', 'id_predio', 'id_lote')  # Campos a mostrar en la lista
    search_fields = ('name', 'characteristics')  # Campos por los que se puede buscar
    list_filter = ('id_predio', 'id_lote')  # Filtros laterales