from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import IoTDevice
from .serializers import IoTDeviceSerializer

class RegisterIoTDevice(APIView):
    def post(self, request, *args, **kwargs):
        # Usamos el serializer para procesar los datos
        serializer = IoTDeviceSerializer(data=request.data)

        if serializer.is_valid():
            try:
                # Guardar el dispositivo en la base de datos
                serializer.save()
                return Response({"message": "Dispositivo registrado exitosamente."}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": "Error en envío de formulario, por favor intente de nuevo más tarde."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
