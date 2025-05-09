from django.db import models
from functools import cached_property
from communication.models import BaseRequestReport
from iot.models import IoTDevice, VALVE_4_ID
from communication.utils import generate_unique_id

class FlowRequestType(models.TextChoices):
    FLOW_CHANGE = 'Solicitud de Cambio de Caudal', 'Solicitud de Cambio de Caudal'
    FLOW_TEMPORARY_CANCEL = 'Solicitud de Cancelación Temporal de Caudal', 'Solicitud de Cancelación Temporal de Caudal'
    FLOW_DEFINITIVE_CANCEL = 'Solicitud de Cancelación Definitiva de Caudal', 'Solicitud de Cancelación Definitiva de Caudal'
    FLOW_ACTIVATION = 'Solicitud de Activación de Caudal', 'Solicitud de Activación de Caudal'

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
        return f"{self.flow_request_type} de {self.created_by.get_full_name()} para {self.lot} - {self.status}"

    @cached_property
    def _get_device(self):
        if not self.lot:
            return None
        return IoTDevice.objects.filter(id_lot=self.lot, device_type__device_id=VALVE_4_ID).first()

    def _validate_owner(self):
        if self.lot and self.created_by != self.lot.plot.owner:
            raise ValueError("Solo el dueño del predio puede realizar una petición para este lote.")

    def _validate_requested_flow(self):
        if self.flow_request_type in {FlowRequestType.FLOW_CHANGE, FlowRequestType.FLOW_ACTIVATION}:
            if self.requested_flow is None:
                raise ValueError("El caudal es obligatorio para la solicitud.")
            if self.requested_flow < 1 or self.requested_flow >= 11.7:
                raise ValueError("El caudal solicitado debe estar dentro del rango de 1 L/seg a 11.7 L/seg.")

    def _check_caudal_flow_inactive(self):
        device = self._get_device
        if device.actual_flow in (0, None):
            if self.flow_request_type == FlowRequestType.FLOW_CHANGE:
                raise ValueError("El caudal del lote está inactivo. Debes solicitar activarlo primero.")
            elif self.flow_request_type == FlowRequestType.FLOW_TEMPORARY_CANCEL:
                raise ValueError("El caudal del lote está inactivo. No es necesario solicitar cancelación temporal.")

    def _validate_pending_change_request(self):
        if self.flow_request_type == FlowRequestType.FLOW_CHANGE:
            if FlowRequest.objects.filter(lot=self.lot).exclude(status='Finalizado').exclude(pk=self.pk).exists():
                raise ValueError("El lote elegido ya cuenta con una solicitud de cambio de caudal en curso.")

    def _validate_pending_cancel_request(self):
        if self.flow_request_type == FlowRequestType.FLOW_CHANGE:
            if FlowRequest.objects.filter(lot=self.lot, flow_request_type__in=[FlowRequestType.FLOW_TEMPORARY_CANCEL, FlowRequestType.FLOW_DEFINITIVE_CANCEL]).exclude(status='Finalizado').exists():
                raise ValueError("El lote elegido cuenta con una solicitud de cancelación de caudal en curso.")

    def _validate_requested_flow_uniqueness(self):
        if self.flow_request_type == FlowRequestType.FLOW_CHANGE:
            device = self._get_device
            if self.requested_flow is not None and device.actual_flow == self.requested_flow:
                raise ValueError("El caudal solicitado es el mismo que se encuentra disponible. Intente con un valor diferente.")

    def _validate_pending_temporary_request(self):
        if self.flow_request_type == FlowRequestType.FLOW_TEMPORARY_CANCEL:
            if FlowRequest.objects.filter(lot=self.lot, flow_request_type=FlowRequestType.FLOW_TEMPORARY_CANCEL).exclude(status='Finalizado').exclude(pk=self.pk).exists():
                raise ValueError("El lote elegido cuenta con una solicitud de cancelación temporal de caudal en curso.")

    def _validate_pending_definitive_request(self):
        if self.flow_request_type in {FlowRequestType.FLOW_TEMPORARY_CANCEL, FlowRequestType.FLOW_DEFINITIVE_CANCEL}:
            if self.status != 'Finalizado' and FlowRequest.objects.filter(lot=self.lot, flow_request_type=FlowRequestType.FLOW_DEFINITIVE_CANCEL).exclude(status='Finalizado').exclude(pk=self.pk).exists():
                raise ValueError("El lote elegido cuenta con una solicitud de cancelación definitiva de caudal en curso.")

    def _validate_cancellation_flow_not_editable(self):
        if self.flow_request_type in {FlowRequestType.FLOW_TEMPORARY_CANCEL, FlowRequestType.FLOW_DEFINITIVE_CANCEL}:
            if self.requested_flow:
                raise ValueError("No se puede modificar el caudal solicitado en una solicitud de cancelación de caudal.")

    def _validate_pending_activation_request(self):
        if FlowRequest.objects.filter(lot=self.lot, status='Pendiente').exclude(pk=self.pk).exists():
            raise ValueError("El lote elegido cuenta con una solicitud de activación de caudal en curso.")

    def _validate_actual_flow_activated(self):
        device = self._get_device
        if device.actual_flow > 0:
            raise ValueError("El caudal del lote ya está activo. No es necesario solicitar activación.")

    def _apply_requested_flow_to_device(self):
        if self.flow_request_type in {FlowRequestType.FLOW_CHANGE, FlowRequestType.FLOW_TEMPORARY_CANCEL, FlowRequestType.FLOW_ACTIVATION}:
            device = self._get_device
            if self.is_approved == True:
                device.actual_flow = self.requested_flow
                device.save()
                self.status = 'Finalizado'

    def _auto_reject_temporary_cancel_request(self):
        if self.flow_request_type == FlowRequestType.FLOW_DEFINITIVE_CANCEL:
            flow_cancel_request = FlowRequest.objects.filter(lot=self.lot, flow_request_type=FlowRequestType.FLOW_TEMPORARY_CANCEL).exclude(status='Finalizado').exclude(pk=self.pk).first()
            if flow_cancel_request:
                flow_cancel_request.is_approved = False
                flow_cancel_request.status = 'Finalizado'
                flow_cancel_request.observations = 'Finalizado de forma automática: El usuario ha solicitado una cancelación definitiva.'
                flow_cancel_request.save()

    def _apply_cancel_flow_to_device(self):
        device = self._get_device
        if self.flow_request_type == FlowRequestType.FLOW_TEMPORARY_CANCEL and self.is_approved == True:
            device.actual_flow = 0
            device.save()
            self.status = 'Finalizado'
        elif self.flow_request_type == FlowRequestType.FLOW_DEFINITIVE_CANCEL:
            device.actual_flow = 0
            device.id_lot.is_activate = False
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
        is_new = not self.pk
        old_is_approved = self.is_approved if not is_new else None

        if not self.id:
            self.id = generate_unique_id(FlowRequest,"10")

        if self.flow_request_type == FlowRequestType.FLOW_DEFINITIVE_CANCEL:
            self.requires_delegation = True

        self.type = 'Solicitud'

        super().save(*args, **kwargs)

        self._apply_requested_flow_to_device()
        self._auto_reject_temporary_cancel_request()
        self._apply_cancel_flow_to_device()
        
        if is_new or (not is_new and old_is_approved != self.is_approved and self.status == 'Finalizado'):
            from communication.notifications import (
                send_flow_request_created_notification,
                send_flow_request_decision_notification
            )
            try:
                if is_new:
                    send_flow_request_created_notification(self)
                elif old_is_approved != self.is_approved and self.status == 'Finalizado':
                    send_flow_request_decision_notification(self)
            except Exception as e:
                print(f"Error al enviar notificación de solicitud: {e}")