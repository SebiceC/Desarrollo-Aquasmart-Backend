from rest_framework import viewsets, permissions
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from communication.reports.models import FailureReport, TypeReport
from communication.reports.serializers import FailureReportSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from communication.requests.models import FlowRequest
from communication.reports.models import FailureReport
from communication.requests.serializers import FlowRequestSerializer
from communication.reports.serializers import FailureReportSerializer



class UserRequestOrReportUnifiedDetailView(APIView):
    """
    Devuelve el detalle de una solicitud o reporte según el ID, sin necesidad de especificar el tipo.
    Solo devuelve datos del usuario autenticado.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user

        # Buscar primero en FlowRequest
        flow = FlowRequest.objects.filter(pk=pk, created_by=user).first()
        if flow:
            return Response(FlowRequestSerializer(flow).data)

        # Luego buscar en FailureReport
        report = FailureReport.objects.filter(pk=pk, created_by=user).first()
        if report:
            return Response(FailureReportSerializer(report).data)

        return Response({"detail": "No se encontró una solicitud o reporte con ese ID perteneciente al usuario."}, status=404)

class UserRequestsAndReportsStatusView(APIView):
    """
    Muestra al usuario final sus solicitudes y reportes, con sus respectivos estados.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Filtrar solicitudes y reportes creados por el usuario
        flow_requests = FlowRequest.objects.filter(created_by=user)
        failure_reports = FailureReport.objects.filter(created_by=user)

        flow_data = [
            {
                "id": fr.id,
                "tipo": fr.flow_request_type,
                "estado": fr.status,
                "fecha": fr.created_at,
            }
            for fr in flow_requests
        ]

        report_data = [
            {
                "id": rep.id,
                "tipo_falla": rep.failure_type,
                "estado": rep.status if hasattr(rep, 'status') else 'Registrado',
                "fecha": rep.created_at,
            }
            for rep in failure_reports
        ]

        return Response({
            "mis_solicitudes": flow_data,
            "mis_reportes": report_data
        })

class WaterSupplyFailureReportViewSet(viewsets.ModelViewSet):
    """
    Gestiona los reportes de fallos en el suministro de agua.
    """
    queryset = FailureReport.objects.filter(failure_type=TypeReport.WATER_SUPPLY_FAILURE)
    serializer_class = FailureReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Devuelve solo los reportes creados por el usuario (o todos si es gerente)
        user = self.request.user
        if user.groups.filter(name="Manager").exists():
            return self.queryset
        return self.queryset.filter(created_by=user)

    def perform_create(self, serializer):
        # Asocia automáticamente el usuario autenticado
        serializer.save(created_by=self.request.user, type='Reporte', failure_type=TypeReport.WATER_SUPPLY_FAILURE)

class AppFailureReportViewSet(viewsets.ModelViewSet):
    """
    Gestiona los reportes de fallos en el aplicativo.
    """
    queryset = FailureReport.objects.filter(failure_type=TypeReport.APPLICATION_FAILURE)
    serializer_class = FailureReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Retorna reportes creados por el usuario autenticado
        user = self.request.user
        if user.groups.filter(name="Manager").exists():
            return self.queryset
        return self.queryset.filter(created_by=user)

    def perform_create(self, serializer):
        # Guarda el reporte como tipo 'Aplicativo'
        serializer.save(created_by=self.request.user, type='Reporte', failure_type=TypeReport.APPLICATION_FAILURE, lot=None, plot=None)

class FailureReportDetailView(RetrieveAPIView):
    """
    Vista de detalle de un reporte de fallos.
    """
    queryset = FailureReport.objects.all()
    serializer_class = FailureReportSerializer
    permission_classes = [IsAuthenticated]