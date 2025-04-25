from django.urls import path
from communication.request.views import (FlowChangeRequestCreateView, FlowChangeRequestStatusView,
    FlowCancelRequestCreateView, FlowCancelRequestStatusView, FlowActivationRequestCreateView, FlowActivationRequestStatusView)

urlpatterns = [
    path('flow-change-request', FlowChangeRequestCreateView.as_view(), name='flow-change-request'), # Crear solicitud de cambio de caudal 
    path('flow-change-request/<int:pk>', FlowChangeRequestStatusView.as_view(), name='flow-change-request-status'), # Aprobar o rechazar solicitud de cambio de caudal (admin)
    path('flow-cancel-request', FlowCancelRequestCreateView.as_view(), name='flow-cancel-request'), # Crear solicitud de cancelación de caudal
    path('flow-cancel-request/<int:pk>', FlowCancelRequestStatusView.as_view(), name='flow-cancel-request-status'), # Aprobar o rechazar solicitud de cancelación de caudal (admin)
    path('flow-activation-request', FlowActivationRequestCreateView.as_view(), name='flow-cancel-request'), # Crear solicitud de activación de caudal
    path('flow-activation-request/<int:pk>', FlowActivationRequestStatusView.as_view(), name='flow-cancel-request-status'), # Aprobar o rechazar solicitud de activación de caudal (admin)
]