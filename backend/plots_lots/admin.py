from django.contrib import admin
from .models import Plot, Lot, SoilType, CropType

# Register your models here.
@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    list_display = ('id_plot', 'owner', 'plot_name', 'latitud', 'longitud', 'plot_extension', 'registration_date', 'is_activate')
    search_fields = ('id_plot', 'plot_name', 'owner')
    list_filter = ('registration_date',)
    ordering = ('registration_date',)
    readonly_fields = ('id_plot',)

@admin.register(SoilType)
class SoilTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('id', 'name')
    ordering = ('id',)

@admin.register(CropType)
class CropTypeAdmin(admin.ModelAdmin):
    list_display = ('id','name')
    search_fields = ('id', 'name')
    ordering = ('id',)

@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ('id_lot', 'plot', 'crop_type', 'crop_variety', 'soil_type', 'registration_date', 'is_activate')
    list_filter = ('plot', 'soil_type')
    search_fields = ('id_lot', 'crop_type', 'crop_variety')
    ordering = ('registration_date',)