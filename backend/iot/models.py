from django.db import models
from plots_lots.models import Plot,Lot

class IoTDevice(models.Model):

    DEVICE_TYPE = (
        ('caudalimetro', 'Caudalimetro'),
        ('electrovalvula', 'Electrovalvula'),
    )

    id_plot = models.CharField(max_length=10, blank=True, null=True, verbose_name="ID del Predio")
    id_lot = models.CharField(max_length=15, blank=True, null=True, verbose_name="ID del Lote")    
    name = models.CharField(max_length=100, verbose_name="Nombre del Dispositivo")
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPE, verbose_name="Tipo de Dispositivo")
    is_active = models.BooleanField(default=True, help_text="Indica si el dispositivo esta habilitado", db_index=True, verbose_name="estado dispositivo")
    characteristics = models.CharField(max_length=300, blank=True, null=False, default="Sin características", verbose_name="Características del Dispositivo")

    class Meta:
        verbose_name = "Dispositivo iot"
        verbose_name_plural = "Dispositivos iot"

    def __str__(self):
        return f"{self.name} ({self.device_type})"
