from django.contrib import admin
from .request.models import FlowChangeRequest, FlowCancelRequest

@admin.register(FlowChangeRequest)
class FlowChangeRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'device', 'lot', 'plot', 'requested_flow',
        'status', 'created_at', 'reviewed_at'
    )
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('user__username', 'lot__id_lot', 'plot__plot_name')
    readonly_fields = ('device', 'plot', 'created_at', 'reviewed_at')
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