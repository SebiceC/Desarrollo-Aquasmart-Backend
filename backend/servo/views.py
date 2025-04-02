from rest_framework import generics, status
from rest_framework.response import Response
from .models import Servo
from .serializers import ServoSerializer
import requests
import logging
from django.conf import settings

# Configuración de logging
logger = logging.getLogger(__name__)

class ServoControlAPI(generics.CreateAPIView):
    """
    Endpoint para controlar el servo motor conectado al ESP32 via HTTP.
    ESP32 actúa como servidor web (IP: http://192.168.20.46/setangle?angle=VALOR)
    """
    queryset = Servo.objects.all()
    serializer_class = ServoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        angle = serializer.validated_data['angle']

        try:
            # 1. Construye la URL para el ESP32 (GET con parámetro en query)
            url = f"http://192.168.20.46/setangle?angle={angle}"
            timeout = getattr(settings, 'ESP32_HTTP_TIMEOUT', 3)  # Timeout opcional desde settings.py

            # 2. Envía la petición al ESP32
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Lanza error si status != 200

            # 3. Procesa la respuesta del ESP32 (ej: "OK: 90")
            esp32_response = response.text.strip()
            logger.info(f"ESP32 respondió: {esp32_response}")

            # 4. Guarda en la base de datos y retorna respuesta
            self.perform_create(serializer)
            return Response({
                "status": "success",
                "angle": angle,
                "esp32_response": esp32_response,
                "endpoint": url  # Para debug
            }, status=status.HTTP_200_OK)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al comunicarse con ESP32: {str(e)}")
            return Response({
                "status": "error",
                "message": "No se pudo conectar al ESP32",
                "details": str(e),
                "solution": "Verifica: 1) ESP32 encendido, 2) Misma red WiFi, 3) IP correcta"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return Response({
                "status": "error",
                "message": "Error interno del servidor"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)