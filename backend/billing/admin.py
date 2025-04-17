from django.contrib import admin
from .rates.models import TaxRate, FixedConsumptionRate, VolumetricConsumptionRate
from .company.models import Company

@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    """
    Vista de administración para el modelo TaxRate.
    """
    list_display = ('id', 'tax_type', 'tax_value')
    search_fields = ('tax_type', 'tax_value')
    list_filter = ('id',)
    ordering = ('id',)

@admin.register(FixedConsumptionRate)
class FixedConsumptionRateAdmin(admin.ModelAdmin):
    """
    Vista de administración para el modelo FixedConsumptionRate.
    """
    list_display = ('id', 'code', 'crop_type', 'fixed_rate_cents')
    search_fields = ('id', 'code', 'crop_type')
    list_filter = ('id', 'code')
    ordering = ('id',)

@admin.register(VolumetricConsumptionRate)
class VolumetricConsumptionRateAdmin(admin.ModelAdmin):
    """
    Vista de administración para el modelo VolumetricConsumptionRate.
    """
    list_display = ('id', 'code', 'crop_type', 'volumetric_rate_cents')
    search_fields = ('id', 'code', 'crop_type')
    list_filter = ('id', 'code')
    ordering = ('id',)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """
    Vista de administración para el modelo Company.
    """
    list_display = ('id_company', 'name', 'nit', 'address', 'phone', 'email')
    search_fields = ('name', 'nit')
    list_filter = ('name',)
    ordering = ('id_company',)