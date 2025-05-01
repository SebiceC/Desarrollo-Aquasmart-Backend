from rest_framework import viewsets
from .models import Reporte, Asignacion, InformeMantenimiento
from .serializers import ReporteSerializer, AsignacionSerializer, InformeMantenimientoSerializer

class ReporteViewSet(viewsets.ModelViewSet):
    queryset = Reporte.objects.all()
    serializer_class = ReporteSerializer

    def pending_reports(self, request, *args, **kwargs):
        queryset = self.queryset.filter(estado='PENDIENTE')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class AsignacionViewSet(viewsets.ModelViewSet):
    queryset = Asignacion.objects.all()
    serializer_class = AsignacionSerializer

    def assign_technician(self, request, *args, **kwargs):
        # Tu lógica de asignación aquí
        return Response({'status': 'technician assigned'})

class InformeMantenimientoViewSet(viewsets.ModelViewSet):
    queryset = InformeMantenimiento.objects.all()
    serializer_class = InformeMantenimientoSerializer

    def complete_report(self, request, *args, **kwargs):
        # Tu lógica para completar reporte aquí
        return Response({'status': 'report completed'})