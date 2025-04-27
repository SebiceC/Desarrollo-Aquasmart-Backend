from django.contrib import admin
from .request.models import FlowChangeRequest, FlowCancelRequest, FlowActivationRequest
from .reports.models import WaterSupplyFailureReport  

@admin.register(WaterSupplyFailureReport)
class WaterSupplyFailureReportAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'lot', 'plot', 'observations',
        'status', 'created_at', 'reviewed_at'
    )
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('user__username', 'lot__id_lot', 'plot__plot_name', 'observations')
    readonly_fields = ('plot', 'created_at', 'reviewed_at')
    date_hierarchy = 'created_at'


@admin.register(FlowChangeRequest)
class FlowChangeRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'lot', 'plot', 'requested_flow',
        'status', 'created_at', 'reviewed_at'
    )
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('user__username', 'lot__id_lot', 'plot__plot_name')
    readonly_fields = ('plot', 'created_at', 'reviewed_at')
    date_hierarchy = 'created_at'

@admin.register(FlowCancelRequest)
class FlowCancelRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'lot', 'plot', 'cancel_type', 'observations',
        'status', 'created_at', 'reviewed_at'
    )
    list_filter = ('status', 'cancel_type', 'created_at', 'reviewed_at')
    search_fields = ('user__username', 'lot__id_lot', 'plot__plot_name')
    readonly_fields = ('plot', 'created_at', 'reviewed_at')
    date_hierarchy = 'created_at'

@admin.register(FlowActivationRequest)
class FlowActivationRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'lot', 'plot', 'requested_flow',
        'status', 'created_at', 'reviewed_at'
    )
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('user__username', 'lot__id_lot', 'plot__plot_name')
    readonly_fields = ('plot', 'created_at', 'reviewed_at')
    date_hierarchy = 'created_at'