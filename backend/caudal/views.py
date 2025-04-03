from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import FlowMeasurement, FlowMeasurementPredio, FlowMeasurementLote,FlowInconsistency
from .serializers import FlowMeasurementSerializer,FlowMeasurementLoteSerializer, FlowMeasurementPredioSerializer,FlowInconsistencySerializer


class FlowMeasurementViewSet(viewsets.ModelViewSet):
    """
    API para gestionar las mediciones de caudal.
    """
    queryset = FlowMeasurement.objects.all()
    serializer_class = FlowMeasurementSerializer 
    permission_classes=[AllowAny]

    def get_queryset(self):
        """
        Permite filtrar por dispositivo si se pasa como parámetro en la URL.
        """
        queryset = super().get_queryset()
        device_id = self.request.query_params.get('device')
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        return queryset

class FlowMeasurementPredioViewSet(viewsets.ModelViewSet):
    queryset = FlowMeasurementPredio.objects.all()
    serializer_class = FlowMeasurementPredioSerializer
    permission_classes=[AllowAny]

class FlowMeasurementLoteViewSet(viewsets.ModelViewSet):
    queryset = FlowMeasurementLote.objects.all()
    serializer_class = FlowMeasurementLoteSerializer
    permission_classes=[AllowAny]    


class FlowInconsistencyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista para consultar inconsistencias detectadas en la medición del caudal.
    Solo permite lectura de los registros.
    """
    queryset = FlowInconsistency.objects.all()
    serializer_class = FlowInconsistencySerializer
    permission_classes=[AllowAny]