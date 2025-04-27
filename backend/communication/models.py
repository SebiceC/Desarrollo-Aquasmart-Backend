from django.db import models
from django.utils import timezone
from users.models import CustomUser
from plots_lots.models import Lot, Plot
from iot.models import IoTDevice, VALVE_4_ID

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

    def __str__(self):
        return f"{self.user} para {self.lot} ({self.status})"

    def validate_lot(self):
        ''' Valida que el lote se envíe en la solicitud '''
        if not self.lot:
            raise ValueError("El lote es obligatorio para la solicitud.")

    def _validate_owner(self):
        ''' Valida que el usuario solicitante sea dueño del predio '''
        if self.user != self.lot.plot.owner:
            raise ValueError("Solo el dueño del predio puede realizar una solicitud para el caudal de este lote.")

    def _validate_lot_is_activate(self):
        ''' Valida que el lote en cuya solicitud está presente, esté habilitado '''
        if self.lot.is_activate != True:
            raise ValueError("No se puede realizar solicitud de caudal de un lote inhabilitado.")

    def _validate_lot_has_valve4(self):
        ''' Validar que el lote tenga asignada una válvula de 4" '''
        device = IoTDevice.objects.filter(id_lot=self.lot, device_type__device_id=VALVE_4_ID).first()
        if not device:
            raise ValueError("El lote no tiene una válvula 4\" asociada.")
        return device

    def _validate_requested_flow(self):
        ''' Asegura que el caudal solicitado sea válido '''
        if self.requested_flow is None:
            raise ValueError("El caudal es obligatorio para la solicitud.")
        # Validar rango de caudal solicitado
        if self.requested_flow < 1 or self.requested_flow >= 11.7:
            raise ValueError("El caudal solicitado debe estar dentro del rango de 1 L/seg a 11.7 L/seg.")

    def _validate_status_transition(self):
        ''' Valida que no se cambie el estado de la solicitud una vez fue revisada '''
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if old.status == 'pendiente' and self.status in ['aprobada', 'rechazada']:
                self.reviewed_at = timezone.now()
            elif old.status in ['aprobada', 'rechazada'] and self.status != old.status:
                raise ValueError("No se puede cambiar el estado una vez que la solicitud ha sido revisada.")

    def _assign_plot_from_lot(self):
        ''' Asigna el predio automáticamente desde el lote '''
        if self.lot and hasattr(self.lot, 'plot'):
            self.plot = self.lot.plot

    def _apply_requested_flow_to_device(self):
        ''' Aplica el caudal solicitado al dispositivo (válvula) asociado '''
        device = IoTDevice.objects.filter(id_lot=self.lot, device_type__device_id=VALVE_4_ID).first()
        if self.status == 'aprobada':
            device.actual_flow = self.requested_flow
            device.save()

    def clean(self):
        self.validate_lot()
        self._validate_owner()
        self._validate_lot_is_activate()
        self._validate_lot_has_valve4()
        self._validate_status_transition()

    def save(self, *args, **kwargs):
        self.full_clean()
        self._assign_plot_from_lot()

        # Asignar valores por defecto en la creación del objeto
        if not self.pk:
            self.status = 'pendiente'
            self.reviewed_at = None

        super().save(*args, **kwargs)