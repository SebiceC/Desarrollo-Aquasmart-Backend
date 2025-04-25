from django.db import models
from communication.models import BaseFlowRequest
from iot.models import IoTDevice, VALVE_4_ID

class FlowChangeRequest(BaseFlowRequest):
    """Modelo para almacenar las solicitudes de cambio de caudal."""
    requested_flow = models.FloatField(verbose_name="Caudal solicitado (L/s)", help_text="Valor del caudal solicitado en litros por segundo")

    class Meta(BaseFlowRequest.Meta):
        verbose_name = "Solicitud de cambio de caudal"
        verbose_name_plural = "Solicitudes de cambio de caudal"

    def __str__(self):
        return f"Solicitud de {self.user.get_full_name()} para {self.lot} ({self.requested_flow} L/s) - {self.status}"

    def clean(self):
        super().clean()
        self._validate_pending_request()
        self._validate_requested_flow()
        self._validate_requested_flow_uniqueness()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._apply_requested_flow_to_device()


class FlowCancelRequest(BaseFlowRequest):
    """Modelo para almacenar las solicitudes de cancelación de caudal."""

    CANCEL_TYPE_CHOICES = [
        ('temporal', 'Temporal'),
        ('definitiva', 'Definitiva'),
    ]
    cancel_type = models.CharField(max_length=10, choices=CANCEL_TYPE_CHOICES, verbose_name="Tipo de cancelación", help_text="Indica si la cancelación es temporal o definitiva")
    observations = models.CharField(max_length=200, verbose_name="Observaciones", help_text="Motivo o detalles de la solicitud de cancelación (5 a 200 caracteres)")

    class Meta(BaseFlowRequest.Meta):
        verbose_name = "Solicitud de cancelación de caudal"
        verbose_name_plural = "Solicitudes de cancelación de caudal"

    def __str__(self):
        return f"{self.user} solicita cancelación {self.cancel_type} de caudal para {self.lot} ({self.status})"

    def _apply_cancel_flow_to_device(self):
        ''' Aplica la cancelación de caudal al dispositivo (válvula) asociado '''
        device = IoTDevice.objects.filter(id_lot=self.lot, device_type__device_id=VALVE_4_ID).first()
        if self.status == 'aprobada':
            device.actual_flow = 0
            device.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._apply_cancel_flow_to_device()


class FlowActivationRequest(BaseFlowRequest):
    """Modelo para solicitudes de activación de caudal."""
    requested_flow = models.FloatField(verbose_name="Caudal solicitado (L/s)", help_text="Valor del caudal solicitado en litros por segundo")
    observations = models.CharField(max_length=300, blank=True, null=True, verbose_name="Observaciones", help_text="Observaciones del usuario (opcional, hasta 300 caracteres)")

    class Meta(BaseFlowRequest.Meta):
        verbose_name = "Solicitud de activación de caudal"
        verbose_name_plural = "Solicitudes de activación de caudal"

    def __str__(self):
        return f"{self.user} solicita activación de caudal para {self.lot} ({self.status})"

    def clean(self):
        super().clean()
        self._validate_pending_request()
        self._validate_requested_flow()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._apply_requested_flow_to_device()
