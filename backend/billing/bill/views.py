from rest_framework import generics
from .models import Bill
from .serializers import BillSerializer
from rest_framework.permissions import IsAuthenticated
from .permissions import IsOwnerOrAdmin  # Asegúrate de importar tu permiso

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