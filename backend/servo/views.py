from rest_framework import generics, status
from rest_framework.response import Response
from .models import Servo
from .serializers import ServoSerializer
import serial
import requests
import time
import logging
from django.conf import settings

# Configuración de logging
logger = logging.getLogger(__name__)

class ServoControlAPI(generics.CreateAPIView):
    """
    Endpoint para controlar el servo motor conectado a ESP32.
    Soporta comunicación via Serial (UART) o HTTP (WiFi).
    """
    queryset = Servo.objects.all()
    serializer_class = ServoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        angle = serializer.validated_data['angle']

        # Configuración desde settings.py (ajustar según necesidad)
        COMMUNICATION_MODE = getattr(settings, 'ESP32_COMM_MODE', 'http')  # 'serial' o 'http'
        SERIAL_PORT = getattr(settings, 'ESP32_SERIAL_PORT', 'COM4')
        BAUD_RATE = getattr(settings, 'ESP32_BAUD_RATE', 115200)
        ESP32_HTTP_URL = getattr(settings, 'ESP32_HTTP_ENDPOINT', 'http://192.168.1.100/servo')
        SIMULATION_MODE = getattr(settings, 'ESP32_SIMULATION', False)

        if SIMULATION_MODE:
            logger.warning(f"MODO SIMULACIÓN: Comando para mover servo a {angle}° (sin dispositivo real)")
            self.perform_create(serializer)
            return Response({
                "status": "success",
                "angle": angle,
                "message": "Modo simulación activado - Ningún dispositivo controlado",
                "mode": "simulation"
            })

        try:
            if COMMUNICATION_MODE == 'serial':
                # Modo Serial/UART (similar a Arduino pero con baudrate más alto)
                response = self._control_via_serial(angle, SERIAL_PORT, BAUD_RATE)
            else:
                # Modo HTTP (recomendado para ESP32 con WiFi)
                response = self._control_via_http(angle, ESP32_HTTP_URL)
            
            self.perform_create(serializer)
            return response

        except Exception as e:
            logger.error(f"Error control servo: {str(e)}")
            return Response({
                "status": "error",
                "message": "Fallo en comunicación con ESP32",
                "details": str(e),
                "solution": "Verifique conexión y parámetros en settings.py"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _control_via_serial(self, angle, port, baudrate):
        """Control via Serial (UART)"""
        esp32 = serial.Serial(port, baudrate, timeout=2)
        time.sleep(2)  # Espera inicialización
        
        # Formato de comando personalizable (depende del firmware en el ESP32)
        command = f"SERVO:{angle}\n".encode('utf-8')
        esp32.write(command)
        logger.info(f"Enviado a ESP32 (Serial): {command.decode().strip()}")
        
        # Lee respuesta
        response = esp32.readline().decode('utf-8').strip()
        esp32.close()
        
        return Response({
            "status": "success",
            "angle": angle,
            "device_response": response,
            "mode": "serial"
        })

    def _control_via_http(self, angle, url):
        """Control via HTTP (REST API)"""
        payload = {'angle': angle}
        timeout = 5  # segundos
        
        response = requests.post(
            url,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()  # Lanza error si HTTP no es 200
        
        logger.info(f"Enviado a ESP32 (HTTP): {payload} | Respuesta: {response.json()}")
        
        return Response({
            "status": "success",
            "angle": angle,
            "device_response": response.json(),
            "mode": "http"
        })