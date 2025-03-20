from django.db import models
import random

class IoTDevice(models.Model):

    DEVICE_TYPE = (
        ('caudalimetro', 'Caudalimetro'),
        ('electrovalvula', 'Electrovalvula'),
    )

    id_plot = models.CharField(max_length=10, blank=True, null=True, verbose_name="ID del Predio")
    id_lot = models.CharField(max_length=15, blank=True, null=True, verbose_name="ID del Lote")
    name = models.CharField(max_length=100, verbose_name="Nombre del Dispositivo")
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPE, verbose_name="Tipo de Dispositivo")
    device_id = models.CharField(max_length=9, unique=True, verbose_name="ID del Dispositivo")  # Formato: 01-XXXX
    is_active = models.BooleanField(default=True, help_text="Indica si el dispositivo está habilitado", db_index=True, verbose_name="estado dispositivo")
    characteristics = models.CharField(max_length=300, blank=True, null=False, default="Sin características", verbose_name="Características del Dispositivo")

    class Meta:
        verbose_name = "Dispositivo IoT"
        verbose_name_plural = "Dispositivos IoT"

    def __str__(self):
        return f"{self.name} ({self.device_type})"

    def save(self, *args, **kwargs):
        # Generar un ID único solo si el dispositivo es nuevo (no tiene device_id)
        if not self.device_id:
            prefix = "01" if self.device_type == "caudalimetro" else "02"  # 01 para caudalimetro, 02 para electrovalvula
            random_number = random.randint(1000, 9999)  # Generar número aleatorio de 4 dígitos
            self.device_id = f"{prefix}-{random_number}"
            
            # Asegurarse de que el ID del dispositivo sea único
            while IoTDevice.objects.filter(device_id=self.device_id).exists():
                random_number = random.randint(1000, 9999)
                self.device_id = f"{prefix}-{random_number}"

        super().save(*args, **kwargs)  # Guardar el dispositivo con el ID generado