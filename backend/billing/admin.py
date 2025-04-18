from django.contrib import admin
from .rates.models import TaxRate, FixedConsumptionRate, VolumetricConsumptionRate
from .company.models import Company
from .bill.models import Bill

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

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        'id_bill', 'code', 'company_name', 'client_name', 'lot_code', 'plot_name',
        'fixed_rate_name', 'fixed_rate_value', 'fixed_rate_quantity',
        'volumetric_rate_name', 'volumetric_rate_value', 'volumetric_rate_quantity',
        'total_amount', 'status', 'creation_date', 'dian_validation_date', 'payment_date', 'due_payment_date'
    )
    search_fields = ('code', 'company_name', 'client_name', 'lot_code', 'plot_name')
    list_filter = ('company_name', 'status', 'creation_date', 'due_payment_date')
    ordering = ('-creation_date',)
    readonly_fields = [ 'code',
        'company_name', 'company_nit', 'company_address', 'company_phone', 'company_email',
        'client', 'client_name', 'client_document', 'client_address',
        'lot_code', 'plot_name',
        'fixed_consumption_rate', 'fixed_rate_code', 'fixed_rate_name', 'fixed_rate_value',
        'volumetric_consumption_rate', 'volumetric_rate_code', 'volumetric_rate_name', 'volumetric_rate_value',
        'total_fixed_rate', 'total_volumetric_rate', 'total_amount', 'pdf_bill_name'
    ]