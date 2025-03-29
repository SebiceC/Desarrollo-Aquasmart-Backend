from django.db import models
from plots_lots.models import Plot, Lot
import random


class DeviceType(models.Model):
    device_id = models.CharField(max_length=2, primary_key=True, editable=False)
    name = models.CharField(max_length=50, blank=False, null=False)

    def save(self, *args, **kwargs):
        if not self.device_id:
            last_device = DeviceType.objects.order_by("-device_id").first()
            if last_device:
                new_id = int(last_device.device_id) + 1  # Incrementa el último ID
                self.device_id = f"{new_id:02d}"  # Formatea con dos dígitos
            else:
                self.device_id = "01"  # Primer ID

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.device_id})"


class IoTDevice(models.Model):
    iot_id = models.CharField(
        max_length=7, primary_key=True, editable=False
    )  # Formato XX-YYYY
    id_plot = models.ForeignKey(
        Plot,
        on_delete=models.SET_NULL,  # Si el plot se elimina, el campo queda en NULL
        null=True,  # Permite valores NULL en la base de datos
        blank=True,  # Permite que los formularios no requieran este campo
        related_name="iot_devices",
    )
    id_lot = models.ForeignKey(
        Lot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="iot_devices",
    )
    owner_name = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=100, verbose_name="Nombre del Dispositivo")
    device_type = models.ForeignKey(
        DeviceType, on_delete=models.CASCADE, verbose_name="Tipo de Dispositivo"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si el dispositivo está habilitado",
        db_index=True,
        verbose_name="Estado del Dispositivo",
    )
    characteristics = models.CharField(
        max_length=300,
        blank=True,
        null=False,
        default="Sin características",
        verbose_name="Características del Dispositivo",
    )

    def save(self, *args, **kwargs):
        if not self.iot_id:
            random_suffix = (
                f"{random.randint(0, 9999):04d}"  # Números aleatorios de 4 dígitos
            )
            self.iot_id = f"{self.device_type.device_id}-{random_suffix}"  # XX-YYYY

        if self.id_plot and self.id_plot.owner:
            self.owner_name = self.id_plot.owner.get_full_name()
        elif not self.owner_name:
            self.owner_name = "Sin dueño"  # ✅ Valor predeterminado si está vacío

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Dispositivo IoT"
        verbose_name_plural = "Dispositivos IoT"

    def __str__(self):
        return f"{self.name} ({self.device_type.name})"
