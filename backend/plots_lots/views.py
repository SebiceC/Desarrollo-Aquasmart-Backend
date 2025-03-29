from rest_framework import viewsets, generics, status, response
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Plot, Lot, SoilType
from .serializers import (
    PlotSerializer,
    PlotDetailSerializer,
    LotSerializer,
    LotDetailSerializer,
    SoilTypeSerializer,
)
from .permissions import IsOwnerOrAdmin


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Vista base que implementa funcionalidad común para predios y lotes.

    Proporciona:
    - Permisos basados en autenticación y propiedad
    - Filtrado de objetos por usuario
    - Activación/desactivación de objetos
    """

    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    model_name = ""  # Debe ser definido en las clases hijas

    def get_queryset(self):
        """
        Retorna todos los objetos para administradores,
        o solo los objetos del usuario para usuarios normales.
        """
        queryset = self.queryset
        if not self.request.user.is_staff:
            queryset = self.get_user_queryset()
        return queryset.order_by("-registration_date")

    def get_user_queryset(self):
        """
        Debe ser implementado por las clases hijas para filtrar
        objetos específicos del usuario.
        """
        raise NotImplementedError(
            "Las clases hijas deben implementar get_user_queryset"
        )

    def perform_update(self, serializer):
        """Validar que el usuario no envíe los mismos datos al actualizar"""
        instance = self.get_object()
        data = serializer.validated_data

        has_changes = any(
            getattr(instance, field) != value for field, value in data.items()
        )

        if not has_changes:
            raise ValueError(
                f"No se detectaron cambios en los datos del {self.model_name}"
            )

        return serializer.save()

    def update(self, request, *args, **kwargs):
        try:
            response = super().update(request, *args, **kwargs)
            return Response(
                {
                    "mensaje": f"{self.model_name} actualizado exitosamente",
                    "data": response.data,
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

    def toggle_active(self, request, *args, **kwargs):
        """
        Activa o desactiva un objeto.
        """
        instance = self.get_object()
        action = kwargs.get("activate", True)

        if instance.is_activate == action:
            status_text = "activado" if action else "desactivado"
            return Response(
                {"error": f"El {self.model_name} ya está {status_text}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.is_activate = action
        instance.save()

        status_text = "activado" if action else "desactivado"
        return Response(
            {
                "mensaje": f"{self.model_name} {status_text} exitosamente",
                "data": self.get_serializer(instance).data,
            },
            status=status.HTTP_200_OK,
        )

    def list(self, request, *args, **kwargs):
        """
        Lista los objetos, filtrando por usuario si no es admin.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PlotViewSet(BaseModelViewSet):
    """
    ViewSet para gestionar predios.
    """

    queryset = Plot.objects.all()
    serializer_class = PlotSerializer
    model_name = "Predio"
    lookup_field = "id_plot"
    lookup_url_kwarg = "id_plot"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PlotDetailSerializer
        return PlotSerializer

    def get_user_queryset(self):
        return Plot.objects.filter(owner=self.request.user)

    def inactive(self, request, *args, **kwargs):
        return self.toggle_active(request, *args, activate=False)

    def active(self, request, *args, **kwargs):
        return self.toggle_active(request, *args, activate=True)


class LotViewSet(BaseModelViewSet):
    """
    ViewSet para gestionar lotes.
    """

    queryset = Lot.objects.all()
    serializer_class = LotSerializer
    model_name = "Lote"
    lookup_field = "id_lot"
    lookup_url_kwarg = "id_lot"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LotDetailSerializer
        return LotSerializer

    def get_user_queryset(self):
        return Lot.objects.filter(plot__owner=self.request.user)

    def inactive(self, request, *args, **kwargs):
        return self.toggle_active(request, *args, activate=False)

    def active(self, request, *args, **kwargs):
        return self.toggle_active(request, *args, activate=True)


class SoilTypeListCreateView(generics.ListCreateAPIView):
    queryset = SoilType.objects.all()
    serializer_class = SoilTypeSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]


class SoilTypeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SoilType.objects.all()
    serializer_class = SoilTypeSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return response.Response(
            {"message": "Eliminado exitosamente"}, status=status.HTTP_200_OK
        )
