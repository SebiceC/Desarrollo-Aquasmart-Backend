from django.contrib import admin
from communication.requests.models import FlowRequest
from communication.reports.models import FailureReport
from communication.assigment_maintenance.models import Assignment, MaintenanceReport

@admin.register(FlowRequest)
class FlowRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by', 'lot', 'flow_request_type', 'status', 'is_approved', 'observations', 'created_at', 'finalized_at')
    readonly_fields = ('id', 'type', 'created_at', 'finalized_at', 'requires_delegation')
    search_fields = ('id', 'created_by__document', 'lot__id_lot', 'plot__id_plot', 'plot__name')
    list_filter = ('flow_request_type', 'status', 'created_at')

@admin.register(FailureReport)
class FailureReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_by', 'lot', 'plot', 'failure_type', 'status', 'observations', 'created_at', 'finalized_at')
    readonly_fields = ('id', 'type', 'created_at', 'finalized_at')
    search_fields = ('id', 'created_by__document', 'lot__id_lot', 'plot__id_plot', 'plot__name')
    list_filter = ('failure_type', 'status', 'created_at')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)  # Solo visible en la vista de edición
    exclude = ('id',)  # No mostrarlo al crear (formulario 'add')
    list_display = ('id', 'flow_request', 'failure_report', 'assigned_by', 'assigned_to', 'assignment_date', 'reassigned')
    search_fields = ('id', 'assigned_by__document', 'assigned_to__document')
    list_filter = ('assignment_date', 'reassigned')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Ya existe, entonces muestra el ID
            return ('id',)
        return ()

@admin.register(MaintenanceReport)
class MaintenanceReportAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)  # Solo visible en la vista de edición
    exclude = ('id',)  # No mostrarlo al crear (formulario 'add')
    list_display = ('id', 'assignment', 'intervention_date', 'status', 'created_at', 'is_approved')
    search_fields = ('id', 'assignment__id')
    list_filter = ('status', 'created_at', 'is_approved')
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Ya existe, entonces muestra el ID
            return ('id',)
        return ()
