from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import FlowMeasurement, FlowMeasurementPredio, FlowMeasurementLote,FlowInconsistency, Lot,Plot
from .serializers import FlowMeasurementSerializer,FlowMeasurementLoteSerializer, FlowMeasurementPredioSerializer,FlowInconsistencySerializer
from rest_framework import status
from django.shortcuts import get_object_or_404

class FlowMeasurementViewSet(viewsets.ModelViewSet):
    """
    API para gestionar las mediciones de caudal.
    """
    queryset = FlowMeasurement.objects.all()
    serializer_class = FlowMeasurementSerializer 
    permission_classes=[IsAuthenticated]
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
    permission_classes=[IsAuthenticated]

class FlowMeasurementLoteViewSet(viewsets.ModelViewSet):
    queryset = FlowMeasurementLote.objects.all()
    serializer_class = FlowMeasurementLoteSerializer
    permission_classes=[IsAuthenticated]    


class FlowInconsistencyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista para consultar inconsistencias detectadas en la medición del caudal.
    Solo permite lectura de los registros.
    """
    queryset = FlowInconsistency.objects.all()
    serializer_class = FlowInconsistencySerializer
    permission_classes=[IsAuthenticated]

class MedicionesPredioView(APIView):
    """Lista todas las mediciones de caudal de un predio específico"""
    permission_classes =[IsAuthenticated]
    
    def get(self, request, predio_id):
        predio = get_object_or_404(Plot,plot_id=predio_id)

        # Verificar que el usuario autenticado es el dueño del predio
        if predio.owner != request.user:
            return Response({"detail": "No tienes permiso para ver estas mediciones."}, status=status.HTTP_403_FORBIDDEN)
    def get(self, request, predio_id):
        mediciones = FlowMeasurementPredio.objects.filter(plot_id=predio_id).order_by('-timestamp')
        serializer = FlowMeasurementPredioSerializer(mediciones, many=True)
        return Response(serializer.data)

class MedicionesLoteView(APIView):
    """Lista todas las mediciones de caudal de un lote específico"""
    
    permission_classes =[IsAuthenticated]
    # Verificar que el usuario autenticado es el dueño del predio
    def get(self, request, lote_id):
        lote = get_object_or_404(Lot, lot_id=lote_id)
        plot = lote.plot
        # Verificar que el usuario autenticado es el dueño del lote
        if plot.owner != request.user:
            return Response({"detail": "No tienes permiso para ver estas mediciones."}, status=status.HTTP_403_FORBIDDEN)
    def get(self, request, lote_id):
        mediciones = FlowMeasurementLote.objects.filter(lot_id=lote_id).order_by('-timestamp')
        serializer = FlowMeasurementLoteSerializer(mediciones, many=True)
        return Response(serializer.data)    

