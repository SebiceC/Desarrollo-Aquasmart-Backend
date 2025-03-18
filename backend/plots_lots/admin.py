from django.contrib import admin
from .models import Plot,Lot,SoilType


# Register your models here.
@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    list_display = ('id_plot', 'owner', 'plot_name', 'latitud', 'longitud', 'plot_extension', 'registration_date', 'is_activate')
    search_fields = ('plot_name', 'owner')
    list_filter = ('registration_date',)
    ordering = ('registration_date',)
    readonly_fields = ('id_plot',)  # 🔹 Agregar esto
@admin.register(SoilType)
class SoilTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ('id_lot','plot', 'crop_type', 'crop_variety', 'soil_type','registration_date','is_activate')
    list_filter = ('plot', 'soil_type')
    search_fields = ('crop_type', 'crop_variety')    
