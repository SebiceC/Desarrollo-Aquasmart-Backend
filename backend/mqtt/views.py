from rest_framework.decorators import api_view
from rest_framework.response import Response
import paho.mqtt.client as mqtt
import json

MQTT_BROKER = "d4abf07c55364762bf6b41af1122a4ab.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "johan"
MQTT_PASSWORD = "Johan123."
TOPIC_COMANDOS = "caudal/lote/1852896-025/comandos"

VALID_COMMANDS = {"abrir", "cerrar", "ajustar", "limitar"}

def publish_mqtt_command(command_payload):
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.tls_set()
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
    client.publish(TOPIC_COMANDOS, json.dumps(command_payload))
    client.loop_stop()
    client.disconnect()

@api_view(['POST'])
def send_mqtt_command(request):
    """
    Recibe JSON con el comando para enviar por MQTT al ESP32.
    Ejemplo válido:
    {
        "comando": "ajustar",
        "angulo": 90
    }
    """
    command = request.data

    # Validar campo comando
    cmd = command.get("comando")
    if not cmd or cmd not in VALID_COMMANDS:
        return Response(
            {"error": f"Comando inválido o no enviado. Comandos válidos: {list(VALID_COMMANDS)}"},
            status=400
        )
    
    # Validar parámetros según comando
    if cmd == "ajustar":
        angulo = command.get("angulo")
        if angulo is None or not (0 <= angulo <= 180):
            return Response(
                {"error": "El comando 'ajustar' requiere un parámetro 'angulo' entre 0 y 180."},
                status=400
            )
    elif cmd == "limitar":
        caudal = command.get("caudal")
        if caudal is None or not (caudal > 0):
            return Response(
                {"error": "El comando 'limitar' requiere un parámetro 'caudal' mayor a 0."},
                status=400
            )
    
    try:
        publish_mqtt_command(command)
        return Response({"status": "Comando enviado correctamente", "comando": command})
    except Exception as e:
        return Response({"error": str(e)}, status=500)
