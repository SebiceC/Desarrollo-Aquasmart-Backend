from rest_framework import generics
from .models import Bill
from .serializers import BillSerializer
from rest_framework.permissions import IsAuthenticated
from .permissions import IsOwnerOrAdmin  # Asegúrate de importar tu permiso
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

class BillListView(generics.ListAPIView):
    """Vista para obtener todas las facturas o solo las de un usuario."""
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Devuelve solo las facturas del usuario si es un usuario normal, o todas las facturas si es un admin."""
        user = self.request.user
        if user.is_staff:
            return Bill.objects.all()  # Administradores pueden ver todas las facturas
        return Bill.objects.filter(client=user)  # Usuarios solo pueden ver sus propias facturas

class BillDetailView(generics.RetrieveAPIView):
    """Vista para obtener el detalle de una factura específica."""
    queryset = Bill.objects.all()
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]  # Asegúrate de que esté el permiso

    def get_object(self):
        """Devuelve la factura asociada al pk, verificando el permiso del usuario."""
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)  # Verifica permisos
        return obj
from .serializers import BillStatusUpdateSerializer

class UpdateBillStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BillStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            try:
                bill = Bill.objects.get(code=code)
            except Bill.DoesNotExist:
                return Response({"detail": "Factura no encontrada."}, status=status.HTTP_404_NOT_FOUND)

            if bill.client != request.user:
                return Response({"detail": "No tienes permiso para modificar esta factura."}, status=status.HTTP_403_FORBIDDEN)

            if bill.status == 'pagada':
                return Response({"detail": "La factura ya está marcada como pagada."}, status=status.HTTP_400_BAD_REQUEST)

            bill.status = 'pagada'
            bill.save()
            return Response({"detail": f" Pago exitoso de la factura {bill.code}."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    