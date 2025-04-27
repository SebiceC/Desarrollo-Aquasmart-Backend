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

    def _check_caudal_flow_inactive(self):
        ''' Verifica que el lote tenga un caudal activo '''
        device = IoTDevice.objects.filter(id_lot=self.lot, device_type__device_id=VALVE_4_ID).first()
        if device.actual_flow in (0, None):
            raise ValueError("El caudal del lote está inactivo. Debes solicitar activarlo primero.")

    def _validate_pending_change_request(self):
        ''' Valida que no existan solicitudes de cambio de caudal pendientes para el lote. '''
        if FlowChangeRequest.objects.filter(lot=self.lot, status='pendiente').exclude(pk=self.pk).exists():
            raise ValueError("El lote elegido ya cuenta con una solicitud de cambio de caudal en curso.")

    def _validate_requested_flow_uniqueness(self):
        ''' Valida que el caudal solicitado no sea igual al actual '''
        device = IoTDevice.objects.filter(id_lot=self.lot, device_type__device_id=VALVE_4_ID).first()
        if self.requested_flow is not None and device.actual_flow == self.requested_flow:
            raise ValueError("El caudal solicitado es el mismo que se encuentra disponible. Intente con un valor diferente.")

    def clean(self):
        super().clean()
        self._check_caudal_flow_inactive()
        self._validate_pending_change_request()
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

    def _validate_pending_temporary_request(self):
        ''' Valida que no existan solicitudes pendientes de cancelación temporal para el mismo lote. '''
        if self.cancel_type != 'definitiva' and FlowCancelRequest.objects.filter(lot=self.lot, status='pendiente', cancel_type='temporal').exclude(pk=self.pk).exists():
            raise ValueError("El lote elegido cuenta con una solicitud de cancelación temporal de caudal en curso.")

    def _validate_pending_definitive_request(self):
        ''' Valida que no existan solicitudes pendientes de cancelación definitiva para el mismo lote. '''
        if FlowCancelRequest.objects.filter(lot=self.lot, status='pendiente', cancel_type='definitiva').exclude(pk=self.pk).exists():
            raise ValueError("El lote elegido cuenta con una solicitud de cancelación definitiva de caudal en curso.")

    def _change_flow_cancel_request(self):
        ''' Permite que el usuario cambie el tipo de cancelación (de temporal a definitiva) de caudal para el lote '''
        flow_cancel_request = FlowCancelRequest.objects.filter(lot=self.lot, status='pendiente', cancel_type='temporal').exclude(pk=self.pk).first()
        # print("flow_cancel_request", flow_cancel_request)
        # print("self.cancel_type", self.cancel_type)
        if self.cancel_type == 'definitiva' and flow_cancel_request:
            # print("flow_cancel_request.status ANTES", flow_cancel_request.status)
            flow_cancel_request.status = 'rechazada'
            # print("flow_cancel_request.status DESPUÉS", flow_cancel_request.status)
            flow_cancel_request.observations = 'Rechazada de forma automática: El usuario ha solicitado una cancelación definitiva.'
            flow_cancel_request.save()

    def _apply_cancel_flow_to_device(self):
        ''' Aplica la cancelación de caudal al dispositivo (válvula) asociado, y al lote (si es definitiva) '''
        device = IoTDevice.objects.filter(id_lot=self.lot, device_type__device_id=VALVE_4_ID).first()
        if self.status == 'aprobada':
            device.actual_flow = 0 # Desactivar el caudal del lote
            device.save()
            if self.cancel_type == 'definitiva':
                device.id_lot.is_activate = False # Desactivar el lote
                device.id_lot.save()

    def clean(self):
        super().clean()
        self._validate_pending_definitive_request()
        self._validate_pending_temporary_request()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._change_flow_cancel_request()
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

    def _validate_pending_activation_request(self):
        ''' Valida que no existan solicitudes pendientes para el mismo lote. '''
        if FlowActivationRequest.objects.filter(lot=self.lot, status='pendiente').exclude(pk=self.pk).exists():
            raise ValueError("El lote elegido cuenta con una solicitud de activación de caudal en curso.")

    def _validate_actual_flow_activated(self):
        ''' Valida que el caudal actual del lote esté activo '''
        device = IoTDevice.objects.filter(id_lot=self.lot, device_type__device_id=VALVE_4_ID).first()
        if device.actual_flow > 0:
            raise ValueError("El caudal del lote ya está activo. No es necesario solicitar activación.")

    def clean(self):
        super().clean()
        self._validate_pending_activation_request()
        self._validate_requested_flow()
        self._validate_actual_flow_activated()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._apply_requested_flow_to_device()