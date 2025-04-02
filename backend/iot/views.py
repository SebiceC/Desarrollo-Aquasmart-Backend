from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework import status
from .serializers import IoTDeviceSerializer, DeviceTypeSerializer, UpdateValveFlowSerializer
from .models import IoTDevice, DeviceType, VALVE_48_ID, VALVE_4_ID
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

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

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Validar que el dispositivo es una válvula antes de actualizar
        if instance.device_type.device_id not in [VALVE_48_ID, VALVE_4_ID]:
            return Response(
                {"error": "Este endpoint solo es válido para válvulas"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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


# class ValveViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet para gestionar válvulas.
#     Permite actualizar el caudal actual (actual_flow) en m³/s.
#     """
#     queryset = Valve.objects.all()
#     serializer_class = ValveSerializer
#     permission_classes = [IsAuthenticated]  # Requiere autenticación
#     lookup_field = 'id_valve'  # Usar id_valve como campo de búsqueda

#     def update(self, request, *args, **kwargs):
#         """Actualizar el caudal de la válvula"""
#         instance = self.get_object()
        
#         # Verificar que solo se está actualizando actual_flow
#         if len(request.data) != 1 or 'actual_flow' not in request.data:
#             return Response(
#                 {"error": "Solo se permite actualizar el caudal actual (actual_flow)"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # Validar que el valor sea un número positivo
#         new_flow = request.data['actual_flow']
#         if not isinstance(new_flow, (int, float)) or new_flow < 0:
#             return Response(
#                 {"error": "actual_flow debe ser un número positivo"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # Actualizar el valor
#         instance.actual_flow = float(new_flow)
#         instance.save()

#         # Aquí iría la lógica para enviar la señal al ESP32
#         try:
#             self._send_to_esp32(instance)
#         except Exception as e:
#             # Log el error pero no fallar la actualización
#             print(f"Error al comunicarse con ESP32: {e}")

#         serializer = self.get_serializer(instance)
#         return Response(serializer.data)

#     def _send_to_esp32(self, valve_instance):
#         """Envía comando al ESP32"""
#         command = {
#             "action": "set_flow",
#             "flow": valve_instance.actual_flow,
#             "valve_id": valve_instance.id_valve
#         }
        
#         # Usar el comunicador ESP32
#         esp32_comm = ESP32Communication()
#         success = async_to_sync(esp32_comm.send_command)(
#             valve_instance.id_valve, 
#             command
#         )
        
#         if not success:
#             raise ConnectionError("No se pudo conectar con el ESP32")