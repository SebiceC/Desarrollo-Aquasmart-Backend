from django.core.management.base import BaseCommand
import paho.mqtt.client as mqtt
import ssl
import json
import time

MQTT_BROKER = "d4abf07c55364762bf6b41af1122a4ab.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "johan"
MQTT_PASSWORD = "Johan123."

TOPIC_DATOS_TIEMPO_REAL = "caudal/lote/1852896-025/datos-realtime"
TOPIC_COMANDOS = "caudal/lote/1852896-025/comandos"
TOPIC_DATOS = "caudal/lote/1852896-025/datos"

class Command(BaseCommand):
    help = "Cliente MQTT para HiveMQ Cloud con envío manual de comandos"

    def add_arguments(self, parser):
        parser.add_argument(
            '--comando',
            type=str,
            help='Comando MQTT a enviar: abrir, cerrar, ajustar, limitar'
        )
        parser.add_argument(
            '--angulo',
            type=int,
            help='Ángulo para comando ajustar (0-180)'
        )
        parser.add_argument(
            '--caudal',
            type=float,
            help='Valor de caudal para comando limitar (float)'
        )

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.stdout.write(self.style.SUCCESS("✅ Conectado a MQTT"))
            client.subscribe(TOPIC_DATOS_TIEMPO_REAL)
            self.stdout.write(f"📡 Suscrito a {TOPIC_DATOS_TIEMPO_REAL}")
            client.subscribe(TOPIC_DATOS)
            self.stdout.write(f"📡 Suscrito a {TOPIC_DATOS}")
        else:
            self.stdout.write(self.style.ERROR(f"❌ Error de conexión MQTT: {rc}"))

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            self.stdout.write(f"⚠️ Mensaje no JSON en {msg.topic}: {payload}")
            return

        if msg.topic == TOPIC_DATOS_TIEMPO_REAL:
            self.stdout.write(self.style.NOTICE(f"\n📈 [Tiempo Real] Flujo recibido:"))
            self.stdout.write(f"    Dispositivo: {data.get('device')}")
            self.stdout.write(f"    Timestamp: {data.get('timestamp')}")
            self.stdout.write(f"    Flujo (L/s): {data.get('flow_rate_Ls')}\n")

        elif msg.topic == TOPIC_DATOS:
            self.stdout.write(self.style.NOTICE(f"\n🕒 [Datos Acumulados - 12h] Consumos recibidos:"))
            self.stdout.write(f"    Dispositivo: {data.get('device')}")
            self.stdout.write(f"    Timestamp: {data.get('timestamp')}")
            self.stdout.write(f"    Consumo parcial (L): {data.get('consumo_parcial_L')}")
            self.stdout.write(f"    Consumo diario (L): {data.get('consumo_dia_L')}")
            self.stdout.write(f"    Consumo mensual (L): {data.get('consumo_mes_L')}")
            self.stdout.write(f"    Contador de unidades (pulsos): {data.get('contador_unidades')}\n")

        else:
            self.stdout.write(self.style.NOTICE(f"\n📩 Mensaje en tópico {msg.topic}:"))
            self.stdout.write(json.dumps(data, indent=4) + "\n")

    def handle(self, *args, **kwargs):
        comando = kwargs.get('comando')
        angulo = kwargs.get('angulo')
        caudal = kwargs.get('caudal')

        client = mqtt.Client()
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        client.on_connect = self.on_connect
        client.on_message = self.on_message

        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_start()

        if comando:
            mensaje = {"comando": comando}
            if comando == "ajustar" and angulo is not None:
                mensaje["angulo"] = angulo
            if comando == "limitar" and caudal is not None:
                mensaje["caudal"] = caudal

            client.publish(TOPIC_COMANDOS, json.dumps(mensaje))
            self.stdout.write(f"📤 Comando enviado: {json.dumps(mensaje)}")
        else:
            self.stdout.write("⚠️ No se recibió ningún comando para enviar. El cliente se queda escuchando...")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("⚠️ Detenido por usuario"))
            client.loop_stop()
            client.disconnect()
