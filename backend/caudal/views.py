from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .models import (
    FlowMeasurement,
    FlowMeasurementPredio,
    FlowMeasurementLote,
    FlowInconsistency,
)
from .serializers import (
    FlowMeasurementSerializer,
    FlowMeasurementLoteSerializer,
    FlowMeasurementPredioSerializer,
    FlowInconsistencySerializer,
)


class FlowMeasurementViewSet(viewsets.ModelViewSet):
    """
    API para gestionar las mediciones de caudal.
    """

    queryset = FlowMeasurement.objects.all()
    serializer_class = FlowMeasurementSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """
        Permite filtrar por dispositivo si se pasa como parámetro en la URL.
        """
        queryset = super().get_queryset()
        device_id = self.request.query_params.get("device")
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        return queryset


class FlowMeasurementPredioViewSet(viewsets.ModelViewSet):
    queryset = FlowMeasurementPredio.objects.all()
    serializer_class = FlowMeasurementPredioSerializer
    permission_classes = [AllowAny]


class FlowMeasurementLoteViewSet(viewsets.ModelViewSet):
    queryset = FlowMeasurementLote.objects.all()
    serializer_class = FlowMeasurementLoteSerializer
    permission_classes = [AllowAny]


class FlowInconsistencyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista para consultar inconsistencias detectadas en la medición del caudal.
    Solo permite lectura de los registros.
    """

    queryset = FlowInconsistency.objects.all()
    serializer_class = FlowInconsistencySerializer
    permission_classes = [AllowAny]


class MedicionesPredioView(APIView):
    """Lista todas las mediciones de caudal de un predio específico"""

    def get(self, request, predio_id):
        mediciones = FlowMeasurementPredio.objects.filter(plot_id=predio_id).order_by(
            "-timestamp"
        )
        serializer = FlowMeasurementPredioSerializer(mediciones, many=True)
        return Response(serializer.data)


class MedicionesLoteView(APIView):
    """Lista todas las mediciones de caudal de un lote específico"""

    def get(self, request, lote_id):
        mediciones = FlowMeasurementLote.objects.filter(lot_id=lote_id).order_by(
            "-timestamp"
        )
        serializer = FlowMeasurementLoteSerializer(mediciones, many=True)
        return Response(serializer.data)
