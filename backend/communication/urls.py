from django.urls import path
from communication.requests.views import (
    FlowRequestViewSet, CancelFlowRequestViewSet, ActivateFlowRequestViewSet,
    FlowRequestDetailView, FlowRequestApproveView, FlowRequestRejectView
)
from communication.requests.views import (
    FlowRequestViewSet, CancelFlowRequestViewSet, ActivateFlowRequestViewSet,
    FlowRequestDetailView, FlowRequestApproveView, FlowRequestRejectView
)
from communication.reports.views import (
    WaterSupplyFailureReportViewSet, AppFailureReportViewSet,UserRequestsAndReportsStatusView
)
from communication.assigment_maintenance.views import (
    AssignmentViewSet,
    FlowRequestAssignmentDetailView,
    FailureReportAssignmentDetailView,
    TechnicianAssignedItemsView,
    AssignmentDetailView,
    MaintenanceReportCreateView,
    MaintenanceReportListView,
    MaintenanceReportDetailView,
    ApproveMaintenanceReportView,
    ReassignAssignmentView


)

# === Flow Requests ===
flow_request_create = FlowRequestViewSet.as_view({'post': 'create'})      # Crear solicitud de cambio de caudal
flow_request_list = FlowRequestViewSet.as_view({'get': 'list'})           # Listar solicitudes de cambio de caudal

cancel_request_create = CancelFlowRequestViewSet.as_view({'post': 'create'})   # Crear solicitud de cancelación de caudal
cancel_request_list = CancelFlowRequestViewSet.as_view({'get': 'list'})        # Listar solicitudes de cancelación

activate_request_create = ActivateFlowRequestViewSet.as_view({'post': 'create'})  # Crear solicitud de activación de caudal
activate_request_list = ActivateFlowRequestViewSet.as_view({'get': 'list'})       # Listar solicitudes de activación

# === Flow Request Management ===
flow_request_detail = FlowRequestDetailView.as_view()         # Ver detalle de solicitud
flow_request_approve = FlowRequestApproveView.as_view()       # Aprobar solicitud
flow_request_reject = FlowRequestRejectView.as_view()         # Rechazar solicitud

# === Reports ===
water_report_create = WaterSupplyFailureReportViewSet.as_view({'post': 'create'})  # Crear reporte de falla en suministro
water_report_list = WaterSupplyFailureReportViewSet.as_view({'get': 'list'})       # Listar reportes de falla en suministro

app_report_create = AppFailureReportViewSet.as_view({'post': 'create'})            # Crear reporte de falla en el aplicativo
app_report_list = AppFailureReportViewSet.as_view({'get': 'list'})                 # Listar reportes de falla en el aplicativo

# === Assignments ===
assignment_create = AssignmentViewSet.as_view({'post': 'create'})  # Crear asignación
assignment_list = AssignmentViewSet.as_view({'get': 'list'})       # Listar asignaciones

urlpatterns = [
    # Flow Request Endpoints
    path('flow-requests/create', flow_request_create, name='flow-request-create'),
    path('flow-requests/list', flow_request_list, name='flow-request-list'),

    path('flow-requests/cancel/create', cancel_request_create, name='flow-request-cancel-create'),
    path('flow-requests/cancel/list', cancel_request_list, name='flow-request-cancel-list'),

    path('flow-requests/activate/create', activate_request_create, name='flow-request-activate-create'),
    path('flow-requests/activate/list', activate_request_list, name='flow-request-activate-list'),

    # Flow Request Management
    path('flow-request/<int:pk>/approve', flow_request_approve, name='flow-request-approve'),
    path('flow-request/<int:pk>/reject', flow_request_reject, name='flow-request-reject'),

    # Report Endpoints
    path('reports/water-supply/create', water_report_create, name='water-supply-failure-create'),
    path('reports/water-supply/list', water_report_list, name='water-supply-failure-list'),

    path('reports/app-failure/create', app_report_create, name='app-failure-create'),
    path('reports/app-failure/list', app_report_list, name='app-failure-list'),

    # Assignment Endpoints
    path('assignments/create', assignment_create, name='assignment-create'),
    path('assignments/list', assignment_list, name='assignment-list'),
     path('assignments/flow-request/<int:pk>', FlowRequestAssignmentDetailView.as_view(), name='assignment-flow-request-detail'),
    path('assignments/failure-report/<int:pk>', FailureReportAssignmentDetailView.as_view(), name='assignment-failure-report-detail'),

    #maintenance reports
    path('technician/assignments', TechnicianAssignedItemsView.as_view(), name='technician-assignments'),  # Lista de reportes/solicitudes asignados a un técnico
    path('technician/assignments/<int:pk>', AssignmentDetailView.as_view(), name='assignment-detail'),     # Detalle de una asignación específica
    path('maintenance-reports/create', MaintenanceReportCreateView.as_view(), name='maintenance-report-create'),  # Crear informe de mantenimiento
    path('maintenance-reports/list', MaintenanceReportListView.as_view(), name='maintenance-report-list'),      # Lista de informes (visible para admin y técnicos)
    path('maintenance-reports/<int:pk>', MaintenanceReportDetailView.as_view(), name='maintenance-report-detail'),  # Detalle del informe

    path('maintenance-reports/<int:pk>/approve', ApproveMaintenanceReportView.as_view(), name='maintenance-report-approve'),
    path('assignments/<int:pk>/reassign', ReassignAssignmentView.as_view(), name='assignment-reassign'),

    #Solicitudes del usuario
    path('my/requests-and-reports', UserRequestsAndReportsStatusView.as_view(), name='user-requests-reports'),


]
