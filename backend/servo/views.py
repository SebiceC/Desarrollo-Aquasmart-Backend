import requests
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Servo
from .serializers import ServoSerializer
import logging

logger = logging.getLogger(__name__)

class ServoControlAPI(generics.CreateAPIView):
    queryset = Servo.objects.all()
    serializer_class = ServoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        angle = serializer.validated_data['angle']

        try:
            # Configuración desde settings.py
            url = f"{settings.ESP32_HTTP_URL}?angle={angle}"  # GET con parámetro en URL
            response = requests.get(url, timeout=settings.ESP32_HTTP_TIMEOUT)
            
            if response.status_code == 200:
                return Response({
                    "status": "success",
                    "angle": angle,
                    "esp32_response": response.text  # "OK: 45"
                })
            else:
                return Response({
                    "status": "error",
                    "message": f"El ESP32 respondió con error: {response.text}"
                }, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al comunicarse con ESP32: {str(e)}")
            return Response({
                "status": "error",
                "message": "No se pudo conectar al ESP32",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)