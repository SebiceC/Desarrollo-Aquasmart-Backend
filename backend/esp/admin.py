from django.contrib import admin
from .models import Consumo

@admin.register(Consumo)
class ConsumoAdmin(admin.ModelAdmin):
    list_display = ('device', 'timestamp', 'consumo_parcial_L', 'consumo_dia_L', 'consumo_mes_L', 'contador_unidades')
    list_filter = ('device', 'timestamp')
    search_fields = ('device',)
    ordering = ('-timestamp',)
