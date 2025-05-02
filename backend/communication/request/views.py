from django.db import models
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import FlowChangeRequest, FlowCancelRequest, FlowActivationRequest
from .serializers import (FlowChangeRequestSerializer, FlowChangeRequestStatusSerializer, FlowCancelRequestSerializer,
    FlowCancelRequestStatusSerializer, FlowActivationRequestSerializer, FlowActivationRequestStatusSerializer, AllFlowRequestsSerializer)


class FlowChangeRequestCreateView(generics.CreateAPIView):
    """Vista para crear solicitudes de cambio de caudal."""
    queryset = FlowChangeRequest.objects.all()
    serializer_class = FlowChangeRequestSerializer
    permission_classes = [IsAuthenticated]


class FlowRequestsListView(generics.ListAPIView):
    """Vista para listar todas las solicitudes de caudal."""
    permission_classes = [IsAdminUser]
    serializer_class = AllFlowRequestsSerializer

    def get_queryset(self):
        # Unir todas las solicitudes en una sola lista
        change = FlowChangeRequest.objects.all().annotate(type=models.Value('Cambio', output_field=models.CharField()))
        cancel = FlowCancelRequest.objects.all().annotate(type=models.Value('Cancelación', output_field=models.CharField()))
        activate = FlowActivationRequest.objects.all().annotate(type=models.Value('Activación', output_field=models.CharField()))
        # Unir los tres querysets
        return list(change) + list(cancel) + list(activate)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # Serializar manualmente
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FlowRequestDetailView(generics.CreateAPIView):
    """Vista para detallar solicitud de cambio de caudal."""
    def get(self, request, tipo, pk):
        model_map = {
            'change': FlowChangeRequest,
            'cancel': FlowCancelRequest,
            'activate': FlowActivationRequest,
        }
        serializer_map = {
            'change': FlowChangeRequestSerializer,
            'cancel': FlowCancelRequestSerializer,
            'activate': FlowActivationRequestSerializer,
        }
        model = model_map.get(tipo)
        serializer_class = serializer_map.get(tipo)
        if not model or not serializer_class:
            return Response({'error': 'Tipo de solicitud no válido.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            instance = model.objects.get(pk=pk)
        except model.DoesNotExist:
            return Response({'error': 'Solicitud no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        # Permitir solo al admin o al usuario dueño de la solicitud
        if not (request.user.is_staff or instance.user == request.user):
            return Response({'error': 'Solo el dueño del predio o el administrador puede detallar la solicitud de caudal de este lote.'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = serializer_class(instance)
        return Response(serializer.data)

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


class FlowActivationRequestCreateView(generics.CreateAPIView):
    """Vista para crear solicitudes de activación de caudal."""
    queryset = FlowActivationRequest.objects.all()
    serializer_class = FlowActivationRequestSerializer
    permission_classes = [IsAuthenticated]


class FlowActivationRequestStatusView(generics.UpdateAPIView):
    """Vista para actualizar el estado de la solicitud de activación de caudal."""
    queryset = FlowActivationRequest.objects.all()
    serializer_class = FlowActivationRequestStatusSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'pk'