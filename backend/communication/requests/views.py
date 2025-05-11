from rest_framework import viewsets, permissions, status 
from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from rest_framework.permissions import IsAuthenticated
from django.utils import timezone


from communication.requests.models import FlowRequest, FlowRequestType
from communication.requests.serializers import FlowRequestSerializer


# Gestiona solicitudes generales de caudal (cambio)
class FlowRequestViewSet(viewsets.ModelViewSet):
    serializer_class = FlowRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="Manager").exists():
            return FlowRequest.objects.all()
        return FlowRequest.objects.filter(created_by=user)

    def perform_create(self, serializer):
        # Guarda la solicitud con el usuario actual como creador
        serializer.save(created_by=self.request.user, type='Solicitud')


# Gestiona solicitudes de cancelación (temporal o definitiva)
class CancelFlowRequestViewSet(viewsets.ModelViewSet):
    serializer_class = FlowRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        base_qs = FlowRequest.objects.filter(
            flow_request_type__in=[
                FlowRequestType.FLOW_TEMPORARY_CANCEL,
                FlowRequestType.FLOW_DEFINITIVE_CANCEL
            ]
        )
        user = self.request.user
        if user.groups.filter(name="Manager").exists():
            return base_qs
        return base_qs.filter(created_by=user)

    def perform_create(self, serializer):
        # Asocia el usuario creador y marca como tipo 'Solicitud'
        serializer.save(created_by=self.request.user, type='Solicitud')


# Gestiona solicitudes de activación de caudal
class ActivateFlowRequestViewSet(viewsets.ModelViewSet):
    serializer_class = FlowRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        base_qs = FlowRequest.objects.filter(flow_request_type=FlowRequestType.FLOW_ACTIVATION)
        user = self.request.user
        if user.groups.filter(name="Manager").exists():
            return base_qs
        return base_qs.filter(created_by=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, type='Solicitud')


# Permite visualizar el detalle de una solicitud específica
class FlowRequestDetailView(RetrieveAPIView):
    queryset = FlowRequest.objects.all()
    serializer_class = FlowRequestSerializer
    permission_classes = [IsAuthenticated]


# Permite aprobar una solicitud de caudal

class FlowRequestApproveView(APIView):
    """
    Permite al administrador aprobar una solicitud de caudal.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
     try:
        flow = FlowRequest.objects.get(pk=pk)
     except FlowRequest.DoesNotExist:
        return Response({"detail": "Solicitud no encontrada."}, status=status.HTTP_404_NOT_FOUND)

     if flow.status == "Finalizado":
        return Response({"detail": "La solicitud ya fue finalizada y no puede modificarse."}, status=status.HTTP_400_BAD_REQUEST)

     flow.is_approved = True
     flow.status = "Finalizado"
     flow.finalized_at = timezone.now()
     flow.save()

     return Response({"detail": "Solicitud aprobada correctamente."}, status=status.HTTP_200_OK)

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            flow = FlowRequest.objects.get(pk=pk)
        except FlowRequest.DoesNotExist:
            return Response({"detail": "Solicitud no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        flow.is_approved = True
        flow.status = "Finalizado"
        flow.finalized_at = timezone.now()
        flow.save()

        return Response({"detail": "Solicitud aprobada correctamente."}, status=status.HTTP_200_OK)


class FlowRequestRejectView(APIView):
    """
    Permite al administrador rechazar una solicitud de caudal.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
     observations = request.data.get("observations")
     if not observations:
        return Response({"detail": "Debe incluir observaciones del rechazo."}, status=status.HTTP_400_BAD_REQUEST)

     try:
        flow = FlowRequest.objects.get(pk=pk)
     except FlowRequest.DoesNotExist:
         return Response({"detail": "Solicitud no encontrada."}, status=status.HTTP_404_NOT_FOUND)

     if flow.status == "Finalizado":
         return Response({"detail": "La solicitud ya fue finalizada y no puede modificarse."}, status=status.HTTP_400_BAD_REQUEST)

     flow.is_approved = False
     flow.status = "Finalizado"
     flow.observations = observations
     flow.finalized_at = timezone.now()
     flow.save()

     return Response({"detail": "Solicitud rechazada correctamente."}, status=status.HTTP_200_OK)

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        observations = request.data.get("observations")
        if not observations:
            return Response({"detail": "Debe incluir observaciones del rechazo."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            flow = FlowRequest.objects.get(pk=pk)
        except FlowRequest.DoesNotExist:
            return Response({"detail": "Solicitud no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        flow.is_approved = False
        flow.status = "Finalizado"
        flow.observations = observations
        flow.finalized_at = timezone.now()
        flow.save()

        return Response({"detail": "Solicitud rechazada correctamente."}, status=status.HTTP_200_OK)
