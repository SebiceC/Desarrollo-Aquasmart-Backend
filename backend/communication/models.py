from django.db import models
from django.utils import timezone
from django.conf import settings
from plots_lots.models import Lot, Plot
from iot.models import IoTDevice, VALVE_4_ID



class StatusRequestReport(models.TextChoices):
    PENDING = 'Pendiente', 'Pendiente' # Cuando se crea la solicitud/reporte
    IN_PROGRESS = 'En proceso', 'En proceso' # Cuando se creó la asignación para la solicitud/reporte
    REJECTED = 'A espera de aprobación', 'A espera de aprobación' # Cuando se creó el informe de la asignación para la solicitud/reporte
    FINISHED = 'Finalizado', 'Finalizado' # Cuando el informe ha sido aprobado

class BaseRequestReport(models.Model):
    ''' Modelo base para solicitudes de caudal y reportes de fallos '''
    type = models.CharField(max_length=50, choices=[('Solicitud', 'Solicitud'), ('Reporte', 'Reporte')], verbose_name="Tipo de la petición", help_text="Tipo de la petición (solicitud o reporte)")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuario", help_text="Usuario que realiza la solicitud/reporte")
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Lote", help_text="Lote al que se le realiza la solicitud/reporte")
    status = models.CharField(max_length=50, choices=StatusRequestReport.choices, default='Pendiente', verbose_name="Estado", help_text="Estado actual de la solicitud/reporte")
    observations = models.CharField(max_length=300, null=True, blank=True, verbose_name="Observaciones", help_text="Motivo o detalles de la solicitud/reporte")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha solicitud/reporte", help_text="Fecha y hora en que se creó la solicitud/reporte")
    finalized_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha finalizado", help_text="Fecha y hora en que la solicitud/reporte fue finalizado")

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.created_by} para {self.lot} ({self.status})"

    def _validate_lot_is_activate(self):
        ''' Valida que el lote en cuya solicitud está presente, esté habilitado '''
        if self.lot and self.lot.is_activate != True:
            raise ValueError("No se puede realizar una solicitud o un reporte de un lote inhabilitado.")

    def _validate_lot_has_valve4(self):
        ''' Validar que el lote tenga asignada una válvula de 4" '''
        if self.lot:
            device = IoTDevice.objects.filter(id_lot=self.lot, device_type__device_id=VALVE_4_ID).first()
            if not device:
                raise ValueError("El lote no tiene una válvula 4\" asociada.")
            return device

    def _validate_status_transition(self):
        ''' Valida que no se cambie el estado de la solicitud una vez fue finalizada '''
        if self.pk:
            try:
                old = type(self).objects.get(pk=self.pk)
                if old.status == StatusRequestReport.FINISHED and self.status != old.status:
                    raise ValueError("No se puede cambiar el estado una vez que la solicitud ha sido revisada.")
            except type(self).DoesNotExist:
                pass

    def clean(self):
        self._validate_lot_is_activate()
        self._validate_lot_has_valve4()
        self._validate_status_transition()

    def save(self, *args, **kwargs):
        self.full_clean()

        # Asignar valores por defecto en la creación del objeto
        if not self.pk:
            self.status = 'Pendiente'
            self.finalized_at = None

        if self.status == StatusRequestReport.FINISHED:
            self.finalized_at = timezone.now()

        super().save(*args, **kwargs)



