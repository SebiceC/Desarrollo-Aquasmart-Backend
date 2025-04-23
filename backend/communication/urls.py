from django.urls import path
from communication.request.views import FlowChangeRequestCreateView, FlowChangeRequestStatusView

urlpatterns = [
    path('flow-change-request', FlowChangeRequestCreateView.as_view(), name='flow-change-request'),
    path('flow-change-request/<int:pk>', FlowChangeRequestStatusView.as_view(), name='flow-change-request-status'),
]