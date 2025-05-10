from django.db import models
from functools import cached_property
from communication.models import BaseRequestReport
from iot.models import IoTDevice, VALVE_4_ID
from communication.utils import generate_unique_id


class FlowRequestType(models.TextChoices):
    FLOW_CHANGE = 'Cambio de Caudal', 'Cambio de Caudal'
    FLOW_TEMPORARY_CANCEL = 'Cancelación Temporal de Caudal', 'Cancelación Temporal de Caudal'
    FLOW_DEFINITIVE_CANCEL = 'Cancelación Definitiva de Caudal', 'Cancelación Definitiva de Caudal'
    FLOW_ACTIVATION = 'Activación de Caudal', 'Activación de Caudal'

class FlowRequest(BaseRequestReport):
    """Modelo para solicitudes de caudal."""
    id = models.IntegerField(primary_key=True, verbose_name="ID", help_text="Identificador único de la solicitud")
    flow_request_type = models.CharField(max_length=80, choices=FlowRequestType.choices, verbose_name="Tipo de solicitud", help_text="Tipo de solicitud de caudal")
    requested_flow = models.FloatField(null=True, blank=True, verbose_name="Caudal solicitado (L/s)", help_text="Valor del caudal solicitado en litros por segundo")
    is_approved = models.BooleanField(default=False, verbose_name="Fue aprobada", help_text="Indica si la solicitud fue aprobada o no")
    requires_delegation = models.BooleanField(default=False, verbose_name="Requiere delegación", help_text="Indica si la solicitud requiere delegación")

    class Meta(BaseRequestReport.Meta):
        verbose_name = "Solicitud de caudal"
        verbose_name_plural = "Solicitudes de caudal"

    def __str__(self):
        return f"Solicitud de {self.flow_request_type} hecha por {self.created_by.get_full_name()} para {self.lot} - {self.status}"

    # --- Propiedades Cacheadas ---
    @cached_property
    def _get_device(self):
        if not self.lot:
            return None
        return IoTDevice.objects.filter(id_lot=self.lot, device_type__device_id=VALVE_4_ID).first()

    def _validate_owner(self):
        ''' Valida que el usuario solicitante sea dueño del predio '''
        if self.lot:
            if self.created_by != self.lot.plot.owner:
                raise ValueError("Solo el dueño del predio puede realizar una petición para este lote.")

    def _validate_requested_flow(self): # PENDIENTE
        ''' Asegura que el caudal solicitado sea válido '''
        if self.flow_request_type in {FlowRequestType.FLOW_CHANGE, FlowRequestType.FLOW_ACTIVATION}:
            if self.requested_flow is None:
                raise ValueError("El caudal es obligatorio para la solicitud.")
            # Validar rango de caudal solicitado
            if self.requested_flow < 1 or self.requested_flow >= 11.7:
                raise ValueError("El caudal solicitado debe estar dentro del rango de 1 L/seg a 11.7 L/seg.")

    def _check_caudal_flow_inactive(self): # PENDIENTE
        ''' Verifica que el lote tenga un caudal activo '''
        device = self._get_device
        if device.actual_flow in (0, None):
            if self.flow_request_type == FlowRequestType.FLOW_CHANGE:
                raise ValueError("El caudal del lote está inactivo. Debes solicitar activarlo primero.")
            elif self.status != 'Finalizado' and self.flow_request_type == FlowRequestType.FLOW_TEMPORARY_CANCEL:
                raise ValueError("El caudal del lote está inactivo. No es necesario solicitar cancelación temporal.")

    def _validate_pending_change_request(self): # PENDIENTE
        ''' Valida que no existan solicitudes de cambio de caudal pendientes para el lote. '''
        if self.flow_request_type == FlowRequestType.FLOW_CHANGE:
            if FlowRequest.objects.filter(lot=self.lot).exclude(status='Finalizado').exclude(pk=self.pk).exists():
                raise ValueError("El lote elegido ya cuenta con una solicitud de cambio de caudal en curso.")

    def _validate_pending_cancel_request(self): # PENDIENTE
        ''' Valida que no existan solicitudes pendientes de cancelación temporal para el mismo lote. '''
        if self.flow_request_type == FlowRequestType.FLOW_CHANGE:
            if FlowRequest.objects.filter(lot=self.lot, flow_request_type__in=[FlowRequestType.FLOW_TEMPORARY_CANCEL, FlowRequestType.FLOW_DEFINITIVE_CANCEL]).exclude(status='Finalizado').exists():
                raise ValueError("El lote elegido cuenta con una solicitud de cancelación de caudal en curso.")

    def _validate_requested_flow_uniqueness(self): # PENDIENTE
        ''' Valida que el caudal solicitado no sea igual al actual '''
        if self.flow_request_type == FlowRequestType.FLOW_CHANGE:
            device = self._get_device
            if self.status != 'Finalizado' and self.requested_flow is not None and device.actual_flow == self.requested_flow:
                raise ValueError("El caudal solicitado es el mismo que se encuentra disponible. Intente con un valor diferente.")

    def _validate_pending_temporary_request(self): # PENDIENTE
        ''' Valida que no existan solicitudes pendientes de cancelación temporal para el mismo lote. '''
        if self.flow_request_type == FlowRequestType.FLOW_TEMPORARY_CANCEL:
            if FlowRequest.objects.filter(lot=self.lot, flow_request_type=FlowRequestType.FLOW_TEMPORARY_CANCEL).exclude(status='Finalizado').exclude(pk=self.pk).exists():
                raise ValueError("El lote elegido cuenta con una solicitud de cancelación temporal de caudal en curso.")

    def _validate_pending_definitive_request(self): # PENDIENTE
        ''' Valida que no existan solicitudes pendientes de cancelación definitiva para el mismo lote. '''
        if self.flow_request_type in {FlowRequestType.FLOW_TEMPORARY_CANCEL, FlowRequestType.FLOW_DEFINITIVE_CANCEL}:
            if self.status != 'Finalizado' and FlowRequest.objects.filter(lot=self.lot, flow_request_type=FlowRequestType.FLOW_DEFINITIVE_CANCEL).exclude(status='Finalizado').exclude(pk=self.pk).exists():
                raise ValueError("El lote elegido cuenta con una solicitud de cancelación definitiva de caudal en curso.")

    def _validate_cancellation_flow_not_editable(self): # PENDIENTE
        ''' Valida que no se permita modificar el caudal solicitado en una solicitud de cancelación '''
        if self.flow_request_type in {FlowRequestType.FLOW_TEMPORARY_CANCEL, FlowRequestType.FLOW_DEFINITIVE_CANCEL}:
            if self.requested_flow:
                raise ValueError("No se puede modificar el caudal solicitado en una solicitud de cancelación de caudal.")

    def _validate_pending_activation_request(self):
        ''' Valida que no existan solicitudes pendientes de activación para el mismo lote. '''
        if FlowRequest.objects.filter(lot=self.lot, status='Pendiente').exclude(pk=self.pk).exists():
            raise ValueError("El lote elegido cuenta con una solicitud de activación de caudal en curso.")

    def _validate_actual_flow_activated(self):
        ''' Valida que el caudal actual del lote esté activo '''
        device = self._get_device
        if device.actual_flow > 0:
            raise ValueError("El caudal del lote ya está activo. No es necesario solicitar activación.")

    def _apply_requested_flow_to_device(self): # PENDIENTE
        ''' Aplica el caudal solicitado al dispositivo (válvula) asociado '''
        if self.flow_request_type in {FlowRequestType.FLOW_CHANGE, FlowRequestType.FLOW_TEMPORARY_CANCEL, FlowRequestType.FLOW_ACTIVATION}:
            device = self._get_device
            if self.is_approved == True:
                device.actual_flow = self.requested_flow
                device.save()
                self.status = 'Finalizado' # Marcar como 'Finalizado' la solicitud

    def _auto_reject_temporary_cancel_request(self): # PENDIENTE
        ''' Cambia el estado de una solicitud de cancelación temporal (de 'Pendiente' a 'Finalizado') si se crea una solicitud de cancelación definitiva '''
        if self.flow_request_type == FlowRequestType.FLOW_DEFINITIVE_CANCEL:
            flow_cancel_request = FlowRequest.objects.filter(lot=self.lot, flow_request_type=FlowRequestType.FLOW_TEMPORARY_CANCEL).exclude(status='Finalizado').exclude(pk=self.pk).first()
            if flow_cancel_request:
                flow_cancel_request.is_approved = False # Marcar como 'False' la aprobación de la solicitud temporal
                flow_cancel_request.status = 'Finalizado' # Marcar como 'Finalizado' la solicitud temporal
                flow_cancel_request.observations = 'Finalizado de forma automática: El usuario ha solicitado una cancelación definitiva.'
                flow_cancel_request.save()

    def apply_cancel_flow_to_device(self): # PENDIENTE
        ''' Aplica la cancelación de caudal al dispositivo (válvula) asociado, y al lote (si es definitiva) '''
        device = self._get_device
        # Si es cancelación temporal
        if self.flow_request_type == FlowRequestType.FLOW_TEMPORARY_CANCEL:
            if self.is_approved == True:
                device.actual_flow = 0 # Desactivar el caudal del lote
                device.save()
                self.status = 'Finalizado'
        # Si es cancelación definitiva
        if self.flow_request_type == FlowRequestType.FLOW_DEFINITIVE_CANCEL:
            if self.is_approved == True:
                device.actual_flow = 0 # Desactivar el caudal del lote
                device.id_lot.is_activate = False # Desactivar el lote
                device.save()
                device.id_lot.save()
                self.status = 'Finalizado'

    def clean(self):
        super().clean()
        self._validate_owner()
        self._validate_requested_flow()
        self._check_caudal_flow_inactive()
        self._validate_pending_change_request()
        self._validate_pending_cancel_request()
        self._validate_requested_flow_uniqueness()
        self._validate_pending_temporary_request()
        self._validate_pending_definitive_request()

    def save(self, *args, **kwargs):
        # Generar ID único para la solicitud
        if not self.id:
            self.id = generate_unique_id(FlowRequest,"10")

            self.type = 'Solicitud'

        if self.flow_request_type == FlowRequestType.FLOW_DEFINITIVE_CANCEL:
            self.requires_delegation = True

        self._apply_requested_flow_to_device()
        self._auto_reject_temporary_cancel_request()
        self.apply_cancel_flow_to_device()

        super().save(*args, **kwargs)