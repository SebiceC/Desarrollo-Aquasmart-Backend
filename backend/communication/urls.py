from django.urls import path
from communication.request.views import (FlowChangeRequestCreateView, FlowRequestsListView, FlowRequestDetailView, FlowChangeRequestStatusView,
    FlowCancelRequestCreateView, FlowCancelRequestStatusView, FlowActivationRequestCreateView, FlowActivationRequestStatusView)
from communication.reports.views import (
    WaterSupplyFailureReportCreateView,
    WaterSupplyFailureReportStatusView,
)
from communication.application_report.views import ApplicationFailureReportCreateView

urlpatterns = [
    path('flow-change-request', FlowChangeRequestCreateView.as_view(), name='flow-change-request'), # Crear solicitud de cambio de caudal
    path('flow-requests', FlowRequestsListView.as_view(), name='flow-requests'), # Listar todas las solicitudes de caudal (admin)
    path('flow-requests/<str:tipo>/<int:pk>', FlowRequestDetailView.as_view(), name='detail-flow-request'), # Detallar solicitud de caudal
    path('flow-change-request/<int:pk>', FlowChangeRequestStatusView.as_view(), name='flow-change-request-status'), # Aprobar o rechazar solicitud de cambio de caudal (admin)
    path('flow-cancel-request', FlowCancelRequestCreateView.as_view(), name='flow-cancel-request'), # Crear solicitud de cancelación de caudal
    path('flow-cancel-request/<int:pk>', FlowCancelRequestStatusView.as_view(), name='flow-cancel-request-status'), # Aprobar o rechazar solicitud de cancelación de caudal (admin)
    path('flow-activation-request', FlowActivationRequestCreateView.as_view(), name='flow-activation-request'), # Crear solicitud de activación de caudal
    path('flow-activation-request/<int:pk>', FlowActivationRequestStatusView.as_view(), name='flow-activation-request-status'), # Aprobar o rechazar solicitud de activación de caudal (admin)
    path('water-supply-failure-report', WaterSupplyFailureReportCreateView.as_view(), name='water-supply-failure-report'),#crear reporte de fallo
    path('water-supply-failure-report/<int:pk>', WaterSupplyFailureReportStatusView.as_view(), name='water-supply-failure-report-status'), #Aprobar o rechazar reporte del usuario
    path('application-failure-report', ApplicationFailureReportCreateView.as_view(), name='application-failure-report'),  # Nueva ruta

]