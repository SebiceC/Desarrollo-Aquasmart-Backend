from django.db import models
from django.utils import timezone
from users.models import CustomUser
from plots_lots.models import Lot, Plot

class BaseFlowRequest(models.Model):
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Solicitante", help_text="Usuario que realiza la solicitud de cambio de caudal")
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Lote", help_text="Lote al que se le solicita el cambio de caudal")
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Predio", help_text="Predio de la válvula principal (si es válvula principal de predio)")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendiente', verbose_name="Estado", help_text="Estado actual de la solicitud")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha solicitud", help_text="Fecha y hora en que se creó la solicitud")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha revisión", help_text="Fecha y hora en que la solicitud fue revisada (aprobada o rechazada)")

    class Meta:
        abstract = True

    def _validate_lot_has_valve4(self):
        from iot.models import IoTDevice, VALVE_4_ID
        device = IoTDevice.objects.filter(id_lot=self.lot, device_type__device_id=VALVE_4_ID).first()
        if not device:
            raise ValueError('El lote no tiene una válvula 4" asociada.')
        return device

    def clean(self):
        # Validar que el lote no sea vacío
        if not self.lot:
            raise ValueError("El lote es obligatorio para la solicitud.")
        # Asignar plot automáticamente desde el lote si es posible
        if self.lot and hasattr(self.lot, 'plot'):
            self.plot = self.lot.plot

    def save(self, *args, **kwargs):
        # Asignar plot automáticamente desde el lote
        if self.lot and hasattr(self.lot, 'plot'):
            self.plot = self.lot.plot

        # Control de revisión
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if old.status == 'pendiente' and self.status in ['aprobada', 'rechazada']:
                self.reviewed_at = timezone.now()
            elif old.status in ['aprobada', 'rechazada'] and self.status != old.status:
                raise ValueError("No se puede cambiar el estado una vez que la solicitud ha sido revisada.")
        else:
            if self.status == 'pendiente':
                self.reviewed_at = None
            elif self.status in ['aprobada', 'rechazada']:
                self.reviewed_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} para {self.lot} ({self.status})"