from django.contrib import admin
from .models import FlowChangeRequest

@admin.register(FlowChangeRequest)
class FlowChangeRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'device', 'lot', 'plot', 'requested_flow',
        'status', 'created_at', 'reviewed_at'
    )
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('user__username', 'lot__id_lot', 'plot__plot_name')
    readonly_fields = ('lot', 'plot', 'created_at', 'reviewed_at')
    date_hierarchy = 'created_at'
