from django.urls import path

# === Importación de vistas relacionadas con solicitudes de caudal ===
from communication.requests.views import (
    FlowRequestViewSet,
    CancelFlowRequestViewSet,
    ActivateFlowRequestViewSet,
    FlowRequestDetailView,
    FlowRequestApproveView,
    FlowRequestRejectView
)

# === Importación de vistas relacionadas con reportes de fallos ===
from communication.reports.views import (
    WaterSupplyFailureReportViewSet,
    AppFailureReportViewSet,
    UserRequestsAndReportsStatusView,
    UserRequestOrReportUnifiedDetailView
)

# === Importación de vistas relacionadas con asignaciones e informes de mantenimiento ===
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
    ReassignAssignmentView,
    AllRequestsAndReportsView,
    AdminRequestOrReportUnifiedDetailView
)

# === Vistas simplificadas con métodos específicos ===
flow_request_create = FlowRequestViewSet.as_view({'post': 'create'})          # Crear solicitud general de caudal
flow_request_list = FlowRequestViewSet.as_view({'get': 'list'})               # Listar todas las solicitudes de caudal

cancel_request_create = CancelFlowRequestViewSet.as_view({'post': 'create'})  # Crear solicitud de cancelación de caudal
cancel_request_list = CancelFlowRequestViewSet.as_view({'get': 'list'})       # Listar solicitudes de cancelación

activate_request_create = ActivateFlowRequestViewSet.as_view({'post': 'create'})  # Crear solicitud de activación de caudal
activate_request_list = ActivateFlowRequestViewSet.as_view({'get': 'list'})       # Listar solicitudes de activación

water_report_create = WaterSupplyFailureReportViewSet.as_view({'post': 'create'})  # Crear reporte de fallo en suministro
water_report_list = WaterSupplyFailureReportViewSet.as_view({'get': 'list'})       # Listar reportes de fallo en suministro

app_report_create = AppFailureReportViewSet.as_view({'post': 'create'})  # Crear reporte de fallo en el aplicativo
app_report_list = AppFailureReportViewSet.as_view({'get': 'list'})       # Listar reportes de fallo en el aplicativo

assignment_create = AssignmentViewSet.as_view({'post': 'create'})  # Crear asignación de técnico a solicitud/reporte
assignment_list = AssignmentViewSet.as_view({'get': 'list'})       # Listar asignaciones existentes

# === Rutas del sistema ===
urlpatterns = [

    # === Endpoints de solicitudes de caudal ===
    path('flow-requests/create', flow_request_create, name='flow-request-create'),
    path('flow-requests/list', flow_request_list, name='flow-request-list'),

    path('flow-requests/cancel/create', cancel_request_create, name='flow-request-cancel-create'),
    path('flow-requests/cancel/list', cancel_request_list, name='flow-request-cancel-list'),

    path('flow-requests/activate/create', activate_request_create, name='flow-request-activate-create'),
    path('flow-requests/activate/list', activate_request_list, name='flow-request-activate-list'),

    # === Gestión de solicitudes (aprobación/rechazo) ===
    path('flow-request/<int:pk>/approve', FlowRequestApproveView.as_view(), name='flow-request-approve'),  # Aprobar solicitud
    path('flow-request/<int:pk>/reject', FlowRequestRejectView.as_view(), name='flow-request-reject'),     # Rechazar solicitud

    # === Endpoints de reportes de fallos ===
    path('reports/water-supply/create', water_report_create, name='water-supply-failure-create'),
    path('reports/water-supply/list', water_report_list, name='water-supply-failure-list'),

    path('reports/app-failure/create', app_report_create, name='app-failure-create'),
    path('reports/app-failure/list', app_report_list, name='app-failure-list'),

    # === Endpoints de asignaciones (para delegar trabajo a técnicos) ===
    path('assignments/create', assignment_create, name='assignment-create'),
    path('assignments/list', assignment_list, name='assignment-list'),

    # Detalles de asignaciones para solicitudes o reportes
    path('assignments/flow-request/<int:pk>', FlowRequestAssignmentDetailView.as_view(), name='assignment-flow-request-detail'),
    path('assignments/failure-report/<int:pk>', FailureReportAssignmentDetailView.as_view(), name='assignment-failure-report-detail'),

    # Reasignar una solicitud o reporte
    path('assignments/<int:pk>/reassign', ReassignAssignmentView.as_view(), name='assignment-reassign'),

    # === Vista del técnico: elementos asignados ===
    path('technician/assignments', TechnicianAssignedItemsView.as_view(), name='technician-assignments'),          # Lista de asignaciones del técnico actual
    path('technician/assignments/<int:pk>', AssignmentDetailView.as_view(), name='assignment-detail'),             # Ver detalle de una asignación específica

    # === Endpoints para informes de mantenimiento ===
    path('maintenance-reports/create', MaintenanceReportCreateView.as_view(), name='maintenance-report-create'),   # Crear nuevo informe de mantenimiento
    path('maintenance-reports/list', MaintenanceReportListView.as_view(), name='maintenance-report-list'),         # Ver lista de informes
    path('maintenance-reports/<int:pk>', MaintenanceReportDetailView.as_view(), name='maintenance-report-detail'), # Ver detalle de un informe
    path('maintenance-reports/<int:pk>/approve', ApproveMaintenanceReportView.as_view(), name='maintenance-report-approve'), # Aprobar un informe

    # === Endpoints del usuario autenticado ===
    path('my/requests-and-reports', UserRequestsAndReportsStatusView.as_view(), name='user-requests-reports'),            # Ver resumen de mis solicitudes y reportes
    path('my/requests-and-reports/<int:pk>', UserRequestOrReportUnifiedDetailView.as_view(), name='user-unified-request-report-detail'),  # Ver detalle de uno (ID único)

    # === Endpoints para administración general ===
    path('admin/requests-and-reports', AllRequestsAndReportsView.as_view(), name='all-requests-reports'),                 # Ver todas las solicitudes y reportes
    path('admin/requests-and-reports/<int:pk>', AdminRequestOrReportUnifiedDetailView.as_view(), name='admin-unified-request-report-detail')  # Ver detalle unificado
]
