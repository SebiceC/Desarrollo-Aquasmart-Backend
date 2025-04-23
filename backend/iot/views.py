from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework import status
from .serializers import IoTDeviceSerializer, DeviceTypeSerializer, UpdateValveFlowSerializer
from .models import IoTDevice, DeviceType
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class RegisterIoTDeviceView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = IoTDeviceSerializer(data=request.data)

        if serializer.is_valid():
            try:
                # Guardar el dispositivo en la base de datos
                iot_device = serializer.save()
                return Response({
                    "message": "Dispositivo registrado exitosamente.",
                    "iot_id": iot_device.iot_id  # Retornar el ID generado
                }, status=status.HTTP_201_CREATED)
            except Exception:
                return Response({"error": "Error al registrar el dispositivo."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ActivateIoTDevice(APIView):
    def patch(self, request, iot_id, *args, **kwargs):
        iot_device = get_object_or_404(IoTDevice, iot_id=iot_id)
        if iot_device.is_active:
            return Response({"message": "El dispositivo ya está activado."}, status=status.HTTP_200_OK)
        
        iot_device.is_active = True
        iot_device.save()
        return Response({
            "message": "Dispositivo activado exitosamente.",
            "iot_id": iot_device.iot_id,
            "is_active": iot_device.is_active
        }, status=status.HTTP_200_OK)

class DeactivateIoTDevice(APIView):
    def patch(self, request, iot_id, *args, **kwargs):
        iot_device = get_object_or_404(IoTDevice, iot_id=iot_id)
        if not iot_device.is_active:
            return Response({"message": "El dispositivo ya está desactivado."}, status=status.HTTP_200_OK)
        
        iot_device.is_active = False
        iot_device.save()
        return Response({
            "message": "Dispositivo desactivado exitosamente.",
            "iot_id": iot_device.iot_id,
            "is_active": iot_device.is_active
        }, status=status.HTTP_200_OK)

# 🔹 Listar todos los dispositivos IoT
class IoTDeviceListView(generics.ListAPIView):
    queryset = IoTDevice.objects.all()
    serializer_class = IoTDeviceSerializer

# 🔹 Ver un dispositivo específico por iot_id
class IoTDeviceDetailView(generics.RetrieveAPIView):
    queryset = IoTDevice.objects.all()
    serializer_class = IoTDeviceSerializer
    lookup_field = 'iot_id'  # Buscar por el campo iot_id

# 🔹 Actualizar un dispositivo por iot_id
class IoTDeviceUpdateView(generics.UpdateAPIView):
    queryset = IoTDevice.objects.all()
    serializer_class = IoTDeviceSerializer
    lookup_field = 'iot_id'  # Buscar por iot_id
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Dispositivo actualizado exitosamente."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# 🔹 Actualizar el caudal de una válvula por iot_id
class UpdateValveFlowView(generics.UpdateAPIView):
    queryset = IoTDevice.objects.all()
    serializer_class = UpdateValveFlowSerializer
    lookup_field = 'iot_id'  # Buscar por iot_id
    permission_classes = [IsAuthenticated, IsAdminUser]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Caudal actualizado exitosamente."}, status=status.HTTP_200_OK)

# 🔹 Listar todos los tipos de dispositivos y crear uno nuevo
class DeviceTypeListCreateView(generics.ListCreateAPIView):
    queryset = DeviceType.objects.all()
    serializer_class = DeviceTypeSerializer

# 🔹 Ver un tipo de dispositivo específico por `device_id`
class DeviceTypeDetailView(generics.RetrieveAPIView):
    queryset = DeviceType.objects.all()
    serializer_class = DeviceTypeSerializer
    lookup_field = 'device_id'  # Buscar por `device_id`

# 🔹 Actualizar un tipo de dispositivo por `device_id`
class DeviceTypeUpdateView(generics.UpdateAPIView):
    queryset = DeviceType.objects.all()
    serializer_class = DeviceTypeSerializer
    lookup_field = 'device_id'  # Buscar por `device_id`

# 🔹 Eliminar un tipo de dispositivo por `device_id`
class DeviceTypeDeleteView(generics.DestroyAPIView):
    queryset = DeviceType.objects.all()
    serializer_class = DeviceTypeSerializer
    lookup_field = 'device_id'  # Buscar por `device_id`

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Tipo de dispositivo eliminado exitosamente."}, status=status.HTTP_204_NO_CONTENT)