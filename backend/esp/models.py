from django.db import models
from iot.models import IoTDevice 
from plots_lots.models import Lot

class Consumo(models.Model):
    device = models.ForeignKey(
        IoTDevice,
        on_delete=models.CASCADE,
        to_field='iot_id',
        db_column='device',
        verbose_name="Dispositivo IoT"
    )
    timestamp = models.DateTimeField()
    consumo_parcial_L = models.FloatField()
    consumo_dia_L = models.FloatField()
    consumo_mes_L = models.FloatField()
    contador_unidades = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.device.iot_id} - {self.timestamp}"
    



class EnviosContador(models.Model):
    device = models.OneToOneField(IoTDevice, on_delete=models.CASCADE)
    lote = models.ForeignKey(Lot, on_delete=models.CASCADE)
    contador = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.device} - Envios: {self.contador}"

