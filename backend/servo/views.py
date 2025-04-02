from rest_framework import generics, status
from rest_framework.response import Response
from .models import Servo
from .serializers import ServoSerializer
import serial
import time
import logging

# Configuración de logging
logger = logging.getLogger(__name__)

class ServoControlAPI(generics.CreateAPIView):
    """
    Endpoint para controlar el servo motor.
    Envía ángulos (0-180°) a Arduino via Serial.
    """
    queryset = Servo.objects.all()
    serializer_class = ServoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        angle = serializer.validated_data['angle']

        # Configuración de la conexión serial (ajusta estos valores)
        SERIAL_PORT = 'COM3'  # Ejemplo: 'COM3' (Windows), '/dev/ttyUSB0' (Linux)
        BAUD_RATE = 9600
        TIMEOUT = 2  # Segundos

        try:
            # 1. Establece conexión con Arduino
            arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
            time.sleep(2)  # Espera inicialización

            # 2. Envía el ángulo como string + salto de línea
            command = f"{angle}\n"
            arduino.write(command.encode('utf-8'))
            logger.info(f"Ángulo enviado a Arduino: {angle}°")

            # 3. Opcional: Lee respuesta de Arduino (si envía confirmación)
            response = arduino.readline().decode('utf-8').strip()
            if response:
                logger.info(f"Arduino respondió: {response}")

            # 4. Cierra la conexión
            arduino.close()

            # Guarda en la base de datos
            self.perform_create(serializer)

            return Response({
                "status": "success",
                "angle": angle,
                "arduino_response": response
            }, status=status.HTTP_200_OK)

        except serial.SerialException as e:
            logger.error(f"Error de conexión serial: {str(e)}")
            return Response({
                "status": "error",
                "message": "No se pudo comunicar con Arduino",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return Response({
                "status": "error",
                "message": "Error interno del servidor"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)