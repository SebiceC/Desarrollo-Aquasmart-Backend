from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import WaterSupplyFailureReport
from .serializers import WaterSupplyFailureReportSerializer, WaterSupplyFailureReportStatusSerializer

class WaterSupplyFailureReportCreateView(generics.CreateAPIView):
    """Vista para crear reportes de fallos en suministro de agua."""
    queryset = WaterSupplyFailureReport.objects.all()
    serializer_class = WaterSupplyFailureReportSerializer
    permission_classes = [IsAuthenticated]

class WaterSupplyFailureReportStatusView(generics.UpdateAPIView):
    """Vista para actualizar el estado de un reporte de fallos en suministro de agua."""
    queryset = WaterSupplyFailureReport.objects.all()
    serializer_class = WaterSupplyFailureReportStatusSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'pk'
