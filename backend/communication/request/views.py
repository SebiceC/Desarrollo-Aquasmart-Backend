from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import FlowChangeRequest, FlowCancelRequest
from .serializers import (FlowChangeRequestSerializer, FlowChangeRequestStatusSerializer,
    FlowCancelRequestSerializer, FlowCancelRequestStatusSerializer)

class FlowChangeRequestCreateView(generics.CreateAPIView):
    """Vista para crear solicitudes de cambio de caudal."""
    queryset = FlowChangeRequest.objects.all()
    serializer_class = FlowChangeRequestSerializer
    permission_classes = [IsAuthenticated]

class FlowChangeRequestStatusView(generics.UpdateAPIView):
    """Vista para actualizar el estado de la solicitud de cambio de caudal."""
    queryset = FlowChangeRequest.objects.all()
    serializer_class = FlowChangeRequestStatusSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'pk'

class FlowCancelRequestCreateView(generics.CreateAPIView):
    """Vista para crear solicitudes de cancelación de caudal."""
    queryset = FlowCancelRequest.objects.all()
    serializer_class = FlowCancelRequestSerializer
    permission_classes = [IsAuthenticated]

class FlowCancelRequestStatusView(generics.UpdateAPIView):
    """Vista para actualizar el estado de la solicitud de cancelación de caudal."""
    queryset = FlowCancelRequest.objects.all()
    serializer_class = FlowCancelRequestStatusSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'pk'