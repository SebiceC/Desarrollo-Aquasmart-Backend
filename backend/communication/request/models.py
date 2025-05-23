from django.db import models
from communication.models import BaseFlowRequest
from iot.models import IoTDevice, VALVE_4_ID

class FlowChangeRequest(BaseFlowRequest):
    """Modelo para almacenar las solicitudes de cambio de caudal."""

    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, verbose_name="Dispositivo", help_text="Dispositivo IoT (válvula) asociado a la solicitud")
    requested_flow = models.FloatField(verbose_name="Caudal solicitado (L/s)", help_text="Valor del caudal solicitado en litros por segundo")

    class Meta(BaseFlowRequest.Meta):
        verbose_name = "Solicitud de cambio de caudal"
        verbose_name_plural = "Solicitudes de cambio de caudal"

    def __str__(self):
        return f"Solicitud de {self.user.get_full_name()} para {self.lot} ({self.requested_flow} L/s) - {self.status}"

    def clean(self):
        super().clean()
        device = self._validate_lot_has_valve4()
        # Validar caudal igual al actual
        if self.requested_flow is not None and device.actual_flow == self.requested_flow:
            raise ValueError("Ya tienes un caudal activo con ese valor. Debes solicitar un valor diferente.")

    def save(self, *args, **kwargs):
        # Asignar device automáticamente desde el lote
        if self.lot:
            device = IoTDevice.objects.filter(id_lot=self.lot, device_type__device_id=VALVE_4_ID).first()
            if not device:
                raise ValueError("El lote no tiene una válvula 4\" asociada.")
            self.device = device

        super().save(*args, **kwargs)

        # Lógica específica: actualizar caudal si se aprueba
        if self.status == 'aprobada':
            self.device.actual_flow = self.requested_flow
            self.device.save()


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

    # Validar que el lote tenga un dispositivo IoT de tipo válvula 4"
    def clean(self):
        super().clean()
        self._validate_lot_has_valve4()

    def __str__(self):
        return f"{self.user} solicita cancelación {self.cancel_type} para {self.lot} ({self.status})"