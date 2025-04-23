from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import IoTDevice, VALVE_48_ID, VALVE_4_ID,DeviceType
import requests
from django.db import transaction
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
            
def create_default_divice_types(sender, **kwargs):  
   
    try:
        default_types = {
            1:"Antena",
            2:"Servidor",
            3:"Medidor de Flujo 48’’",
            4:"Medidor de Flujo 4’’",
            5:"Válvula 48’’",
            6:"Válvula 4’’",
            7:"Panel Solar",
            8:"Actuador 48’’",
            9:"Actuador 4’’",
            10:"Controlador de Carga",
            11:"Batería",
            12:"Convertidor de Voltaje",
            13:"Microcontrolador",
            14:"Traductor de Información TTL",   
        }

        with transaction.atomic():
            for device_id, name in default_types.items():
                DeviceType.objects.update_or_create(
                    device_id=device_id,
                    defaults={"name": name}
                )

    except Exception as e:
        print(f"Error creando tipos de dispositivo: {e}")