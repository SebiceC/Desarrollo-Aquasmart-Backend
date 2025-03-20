from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import IoTDevice
from .serializers import IoTDeviceSerializer

class RegisterIoTDevice(APIView):
    def post(self, request, *args, **kwargs):
        serializer = IoTDeviceSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({"message": "Dispositivo registrado exitosamente."}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": "Error en envío de formulario, por favor intente de nuevo más tarde."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class IoTDeviceListView(APIView):
    def get(self, request, *args, **kwargs):
        devices = IoTDevice.objects.all()
        serializer = IoTDeviceSerializer(devices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class IoTDeviceDetailView(APIView):
    def get_object(self, device_id):
        try:
            return IoTDevice.objects.get(device_id=device_id)
        except IoTDevice.DoesNotExist:
            return None

    def get(self, request, device_id, *args, **kwargs):
        device = self.get_object(device_id)
        if device:
            serializer = IoTDeviceSerializer(device)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"error": "Dispositivo no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, device_id, *args, **kwargs):
        device = self.get_object(device_id)
        if device:
            serializer = IoTDeviceSerializer(device, data=request.data, partial=True)
            if serializer.is_valid():
                try:
                    serializer.save()
                    return Response({"message": "Dispositivo actualizado exitosamente."}, status=status.HTTP_200_OK)
                except Exception as e:
                    return Response({"error": f"Error al actualizar el dispositivo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "Dispositivo no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, device_id, *args, **kwargs):
        device = self.get_object(device_id)
        if device:
            device.delete()
            return Response({"message": "Dispositivo eliminado exitosamente."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Dispositivo no encontrado."}, status=status.HTTP_404_NOT_FOUND)