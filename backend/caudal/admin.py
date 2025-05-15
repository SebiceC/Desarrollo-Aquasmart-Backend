from django.contrib import admin
from .models import FlowMeasurementPredio, FlowMeasurementLote, FlowInconsistency,WaterConsumptionRecord

@admin.register(FlowMeasurementPredio)
class FlowMeasurementPredioAdmin(admin.ModelAdmin):
    list_display = ('id', 'plot', 'flow_rate', 'timestamp')
    search_fields = ('plot__plot_name',)
    list_filter = ('timestamp',)

@admin.register(FlowMeasurementLote)
class FlowMeasurementLoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'lot', 'flow_rate', 'timestamp')
    search_fields = ('lot__id_lot',)
    list_filter = ('timestamp',)

@admin.register(FlowInconsistency)
class FlowInconsistencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'plot', 'recorded_flow', 'total_lots_flow', 'difference', 'timestamp')
    search_fields = ('plot__plot_name',)
    list_filter = ('timestamp',)
    
class WaterConsumptionRecordAdmin(admin.ModelAdmin):
    list_display = ['lot', 'start_date', 'end_date', 'previous_reading', 'current_reading', 'period_consumption', 'billed']
    list_filter = ['lot', 'billed', 'start_date']
    search_fields = ['lot__id_lot']
    
    def save_model(self, request, obj, form, change):
        # Calcular automáticamente el consumo del periodo
        if obj.current_reading is not None and obj.previous_reading is not None:
            obj.period_consumption = max(0, obj.current_reading - obj.previous_reading)
        
        # Obtener el último registro para calcular acumulados
        last_record = WaterConsumptionRecord.objects.filter(
            lot=obj.lot, 
            end_date__lt=obj.end_date
        ).order_by('-end_date').first()
        
        # Calcular consumo acumulado
        if last_record:
            obj.accumulated_consumption = last_record.accumulated_consumption + obj.period_consumption
        else:
            obj.accumulated_consumption = obj.period_consumption
        
        # Calcular consumo mensual
        month_start = obj.end_date.replace(day=1, hour=0, minute=0, second=0)
        month_records = WaterConsumptionRecord.objects.filter(
            lot=obj.lot,
            end_date__gte=month_start,
            end_date__lt=obj.end_date
        )
        monthly_consumption = sum(record.period_consumption for record in month_records)
        obj.monthly_consumption = monthly_consumption + obj.period_consumption
        
        super().save_model(request, obj, form, change)

admin.site.register(WaterConsumptionRecord, WaterConsumptionRecordAdmin)    