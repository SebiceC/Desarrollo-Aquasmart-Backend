from rest_framework import viewsets
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .models import Plot,Lot
from .serializers import PlotSerializer,LotSerializer,LotActivationSerializer,PlotDetailSerializer
from .permissions import IsOwnerOrAdmin

class PlotViewSet(viewsets.ModelViewSet):
    queryset = Plot.objects.all()
    serializer_class = PlotSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """
        Retorna todos los predios para administradores,
        o solo los predios del usuario para usuarios normales.
        """
        if self.request.user.is_staff:
            return Plot.objects.all()
        return Plot.objects.filter(owner=self.request.user)

    def perform_update(self, serializer):
        """ Validar que el usuario no envíe los mismos datos al actualizar """
        instance = self.get_object()
        data = serializer.validated_data

        # Verifica si los datos enviados son iguales a los actuales
        has_changes = any(
            getattr(instance, field) != value for field, value in data.items()
        )

        if not has_changes:
            raise Exception("No se detectaron cambios en los datos del predio, modifique al menos un campo para actualizar.")

        serializer.save()

    def update(self, request, *args, **kwargs):
        """ Manejo de errores en actualización con PUT y respuesta de éxito """
        try:
            response = super().update(request, *args, **kwargs)
            return Response({"success": "Actualización exitosa.", "data": response.data}, status=status.HTTP_200_OK)
        except Exception as e:
            if str(e) == "No se detectaron cambios en los datos del predio, modifique al menos un campo para actualizar.":
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Error en la actualización del predio, por favor intente más tarde."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        """ Manejo de errores en actualización con PATCH y respuesta de éxito """
        try:
            response = super().partial_update(request, *args, **kwargs)
            return Response({"success": "Actualización exitosa.", "data": response.data}, status=status.HTTP_200_OK)
        except Exception as e:
            if str(e) == "No se detectaron cambios en los datos del predio, modifique al menos un campo para actualizar.":
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Error en la actualización del predio, por favor intente más tarde."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def inactive(self, request, pk=None):
        """ Inhabilita un predio cambiando is_activate a False """
        try:
            predio = self.get_queryset().filter(id_plot=pk).first()
            
            if not predio:
                return Response({"error": "Predio no encontrado."}, status=status.HTTP_404_NOT_FOUND)

            if not predio.is_activate:
                return Response({"error": "El predio ya está inhabilitado."}, status=status.HTTP_400_BAD_REQUEST)

            predio.is_activate = False
            predio.save()
            return Response({"success": "Predio inhabilitado exitosamente."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"No se pudo inhabilitar el predio: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def active(self, request, pk=None):
        """ Habilita un predio cambiando is_activate a True """
        try:
            predio = self.get_object()
            if predio.is_activate:
                return Response({"error": "El predio ya está habilitado."}, status=status.HTTP_400_BAD_REQUEST)

            predio.is_activate = True
            predio.save()
            return Response({"success": "Predio habilitado exitosamente."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "No se pudo habilitar el predio."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LotCreateView(generics.CreateAPIView):
    queryset = Lot.objects.all()
    serializer_class = LotSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]     
    
class ActivateLotView(generics.UpdateAPIView):
    queryset = Lot.objects.all()
    serializer_class = LotActivationSerializer
    lookup_field = 'id_lot'  # Usamos el campo id_lot para buscar el lote
    permission_classes = [IsAuthenticated,IsAdminUser]

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()  # Obtiene el lote por id_lot
        instance.is_activate = True  # Activa el lote
        instance.save()  # Guarda los cambios

        return Response(
            {
                "message": f"Lote {instance.id_lot} activado correctamente.",
                "data": {"is_activate": True}
            },
            status=status.HTTP_200_OK
        )    

class DeactivateLotView(generics.UpdateAPIView):
    queryset = Lot.objects.all()
    serializer_class = LotActivationSerializer
    lookup_field = 'id_lot'  # Usamos el campo id_lot para buscar el lote
    permission_classes = [IsAuthenticated,IsAdminUser]
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()  # Obtiene el lote por id_lot
        instance.is_activate = False  # Desactiva el lote
        instance.save()  # Guarda los cambios

        return Response(
            {
                "message": f"Lote {instance.id_lot} desactivado correctamente.",
                "data": {"is_activate": False}
            },
            status=status.HTTP_200_OK
        )  
    
class PlotDetailView(generics.RetrieveAPIView):
    queryset = Plot.objects.all()
    serializer_class = PlotDetailSerializer
    lookup_field = 'id_plot'  # Usamos el campo id_plot para buscar el predio     
    [IsAuthenticated,IsAdminUser]
