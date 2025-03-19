from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Device
from .serializers import DeviceSerializer

class DeviceUpdateView(generics.UpdateAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]  # Solo usuarios autenticados pueden acceder

    def get_permissions(self):
        """
        Asigna permisos personalizados para actualizar dispositivos IoT.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), permissions.DjangoModelPermissions()]
        return super().get_permissions()