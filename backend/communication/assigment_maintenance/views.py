from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.generics import (
    RetrieveAPIView, CreateAPIView, ListAPIView
)
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from communication.requests.models import FlowRequest
from communication.requests.serializers import FlowRequestSerializer
from communication.reports.models import FailureReport
from communication.reports.serializers import FailureReportSerializer

from .models import MaintenanceReport, Assignment
from .serializers import MaintenanceReportSerializer, AssignmentSerializer
from .permissions import IsAdminOrTechnicianOrOperator  # <-- Asegúrate de importar bien

User = get_user_model()


class AssignmentViewSet(viewsets.ModelViewSet):
    """
    Permite crear y listar asignaciones por parte de administradores o técnicos.
    """
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name__in=["Técnicos", "Operadores"]).exists():
            return Assignment.objects.all()
        return Assignment.objects.filter(assigned_by=user)

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)


class FlowRequestAssignmentDetailView(RetrieveAPIView):
    """
    Devuelve los detalles de una solicitud asignada (para gestión).
    """
    queryset = FlowRequest.objects.all()
    serializer_class = FlowRequestSerializer
    permission_classes = [IsAuthenticated]


class FailureReportAssignmentDetailView(RetrieveAPIView):
    """
    Devuelve los detalles de un reporte asignado (para gestión).
    """
    queryset = FailureReport.objects.all()
    serializer_class = FailureReportSerializer
    permission_classes = [IsAuthenticated]


class TechnicianAssignedItemsView(ListAPIView):
    """
    Lista todas las solicitudes o reportes asignados al técnico autenticado.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        return Assignment.objects.filter(assigned_to=self.request.user)


class AssignmentDetailView(RetrieveAPIView):
    """
    Detalle completo de una asignación específica (flujo o reporte).
    """
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]


class MaintenanceReportCreateView(CreateAPIView):
    """
    Permite al técnico crear un informe de mantenimiento.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MaintenanceReportSerializer

    def perform_create(self, serializer):
        serializer.save()


class MaintenanceReportListView(ListAPIView):
    """
    Lista todos los informes de mantenimiento.
    Técnicos, operadores y admins ven todos. Otros ven solo los suyos.
    """
    serializer_class = MaintenanceReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name__in=["Técnicos", "Operadores"]).exists():
            return MaintenanceReport.objects.all()
        return MaintenanceReport.objects.filter(assignment__assigned_to=user)


class MaintenanceReportDetailView(RetrieveAPIView):
    """
    Muestra los detalles de un informe de mantenimiento específico.
    """
    queryset = MaintenanceReport.objects.all()
    serializer_class = MaintenanceReportSerializer
    permission_classes = [IsAuthenticated]


class ApproveMaintenanceReportView(APIView):
    """
    Permite aprobar informes de mantenimiento (solo admin/técnico/operador).
    """
    permission_classes = [IsAuthenticated, IsAdminOrTechnicianOrOperator]

    def post(self, request, pk):
        try:
            report = MaintenanceReport.objects.get(pk=pk)
        except MaintenanceReport.DoesNotExist:
            return Response({"detail": "Informe no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        if report.is_approved:
            return Response({"detail": "El informe ya fue aprobado."}, status=status.HTTP_400_BAD_REQUEST)

        report.is_approved = True
        report.save()
        return Response({"detail": "Informe aprobado correctamente."})


class ReassignAssignmentView(APIView):
    """
    Permite reasignar una solicitud o reporte.
    """
    permission_classes = [IsAuthenticated, IsAdminOrTechnicianOrOperator]

    def post(self, request, pk):
        try:
            old_assignment = Assignment.objects.get(pk=pk)
        except Assignment.DoesNotExist:
            return Response({"detail": "Asignación no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        data['reassigned'] = True
        data['assigned_by'] = request.user.id

        # Reasignar mismo flujo o reporte
        if old_assignment.flow_request:
            data['flow_request'] = old_assignment.flow_request.id
        elif old_assignment.failure_report:
            data['failure_report'] = old_assignment.failure_report.id

        serializer = AssignmentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Reasignación creada correctamente."})
        return Response(serializer.errors, status=400)
