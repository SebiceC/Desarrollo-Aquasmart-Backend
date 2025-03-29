from django.contrib import admin
from .models import FlowMeasurementPredio, FlowMeasurementLote, FlowInconsistency


@admin.register(FlowMeasurementPredio)
class FlowMeasurementPredioAdmin(admin.ModelAdmin):
    list_display = ("id", "plot", "flow_rate", "timestamp")
    search_fields = ("plot__plot_name",)
    list_filter = ("timestamp",)


@admin.register(FlowMeasurementLote)
class FlowMeasurementLoteAdmin(admin.ModelAdmin):
    list_display = ("id", "lot", "flow_rate", "timestamp")
    search_fields = ("lot__id_lot",)
    list_filter = ("timestamp",)


@admin.register(FlowInconsistency)
class FlowInconsistencyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "plot",
        "recorded_flow",
        "total_lots_flow",
        "difference",
        "timestamp",
    )
    search_fields = ("plot__plot_name",)
    list_filter = ("timestamp",)
