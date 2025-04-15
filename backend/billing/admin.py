from django.contrib import admin
from .rates.models import TaxRate, ConsumptionRate
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

@admin.register(ConsumptionRate)
class ConsumptionRateAdmin(admin.ModelAdmin):
    """
    Vista de administración para el modelo ConsumptionRate.
    """
    list_display = ('id', 'crop_type', 'fixed_rate_cents', 'volumetric_rate_cents')
    search_fields = ('id', 'crop_type')
    list_filter = ('id',)
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