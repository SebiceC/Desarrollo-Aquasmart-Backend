from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import IoTDevice, VALVE_48_ID, VALVE_4_ID
import requests

@receiver(post_save, sender=IoTDevice)
def send_flow_to_esp(sender, instance, **kwargs):
    # Verificar si es una válvula y actual_flow ha cambiado
    if instance.device_type_id in [VALVE_48_ID, VALVE_4_ID]:
        try:
            esp_ip = "172.20.10.2"  # Reemplazar con IP real del ESP32
            angle = int(instance.actual_flow)  # Conversión directa temporal
            requests.get(f"http://{esp_ip}/setangle?angle={angle}", timeout=3)
        except Exception as e:
            print(f"Error enviando a ESP32: {str(e)}")