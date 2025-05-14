from rest_framework import serializers
from .models import FlowRequest, FlowRequestType
from iot.models import IoTDevice, VALVE_4_ID

class FlowRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowRequest
        fields = [
            'id',
            'type',
            'created_by',
            'lot',
            'flow_request_type',
            'requested_flow',
            'is_approved',
            'requires_delegation',
            'status',
            'observations',
            'created_at',
            'finalized_at',
        ]
        read_only_fields = ['id', 'status', 'created_by', 'requires_delegation', 'created_at', 'finalized_at']
        extra_kwargs = {
            'lot': {'required': True, 'allow_null': False},
            'observations': {'required': False, 'allow_null': False},
        }

    def _validate_owner(self, lot, user):
        ''' Valida que el usuario creador sea dueño del predio o del lote. '''
        if lot and user != lot.plot.owner:
            raise serializers.ValidationError(
                "Solo el dueño del predio puede realizar una solicitud para este lote."
            )

    def _validate_requested_flow(self, flow_request_type, requested_flow):
        ''' Asegura que el caudal solicitado sea válido '''
        if flow_request_type in {FlowRequestType.FLOW_CHANGE, FlowRequestType.FLOW_ACTIVATION}:
            if requested_flow is None:
                raise serializers.ValidationError("El caudal es obligatorio para la solicitud.")
            if requested_flow < 1 or requested_flow >= 11.7:
                raise serializers.ValidationError(
                    "El caudal solicitado debe estar dentro del rango de 1 L/seg a 11.7 L/seg."
                )

    def _get_device_valve4(self, lot):
        ''' Obtener el dispositivo válvula 4" vinculado al lote '''
        if not lot:
            return None
        device = IoTDevice.objects.filter(id_lot=lot, device_type__device_id=VALVE_4_ID).first()
        if not device:
            raise serializers.ValidationError("El lote no tiene una válvula 4\" asociada.")
        return device

    def _check_caudal_flow_inactive(self, device, flow_request_type, status):
        ''' Verifica que el lote tenga un caudal activo '''
        if device.actual_flow in (0, None):
            if flow_request_type == FlowRequestType.FLOW_CHANGE:
                raise serializers.ValidationError(
                    "El caudal del lote está inactivo. Debes solicitar activarlo primero."
                )
            # Se verifica que el status sea != 'Finalizado', para que la instancia
            # que se actualiza en el método _auto_reject_temporary_cancel_request
            # no choque con esta validación
            elif status != 'Finalizado' and flow_request_type == FlowRequestType.FLOW_TEMPORARY_CANCEL:
                raise serializers.ValidationError(
                    "El caudal del lote está inactivo. No es necesario solicitar cancelación temporal."
                )

    def _validate_pending_change_request(self, lot, instance_pk):
        ''' Valida que no existan solicitudes de cambio de caudal pendientes para el lote. '''
        if FlowRequest.objects.filter(lot=lot).exclude(status='Finalizado').exclude(pk=instance_pk).exists():
            raise serializers.ValidationError(
                "El lote elegido ya cuenta con una solicitud de cambio de caudal en curso."
            )

    def _validate_pending_cancel_request(self, lot):
        ''' Valida que no existan solicitudes pendientes de cancelación temporal para el mismo lote. '''
        if FlowRequest.objects.filter(
            lot=lot,
            flow_request_type__in=[
                FlowRequestType.FLOW_TEMPORARY_CANCEL,
                FlowRequestType.FLOW_DEFINITIVE_CANCEL
            ]
        ).exclude(status='Finalizado').exists():
            raise serializers.ValidationError(
                "El lote elegido cuenta con una solicitud de cancelación de caudal en curso."
            )

    def _validate_requested_flow_uniqueness(self, flow_request_type, device, requested_flow, status):
        ''' Valida que el caudal solicitado no sea igual al actual '''
        if (flow_request_type == FlowRequestType.FLOW_CHANGE and 
            status == 'Pendiente' and 
            requested_flow is not None and 
            device.actual_flow == requested_flow):
            raise serializers.ValidationError(
                "El caudal solicitado es el mismo que se encuentra disponible. Intente con un valor diferente."
            )

    def _validate_pending_temporary_request(self, flow_request_type, lot, instance_pk):
        """Valida que no existan solicitudes pendientes de cancelación temporal para el mismo lote."""
        if flow_request_type == FlowRequestType.FLOW_TEMPORARY_CANCEL:
            if FlowRequest.objects.filter(
                lot=lot,
                flow_request_type=FlowRequestType.FLOW_TEMPORARY_CANCEL
            ).exclude(status='Finalizado').exclude(pk=instance_pk).exists():
                raise serializers.ValidationError(
                    "El lote elegido cuenta con una solicitud de cancelación temporal de caudal en curso."
                )

    def _validate_pending_definitive_request(self, flow_request_type, lot, status, instance_pk):
        """Valida que no existan solicitudes pendientes de cancelación definitiva para el mismo lote."""
        if flow_request_type in {FlowRequestType.FLOW_TEMPORARY_CANCEL, FlowRequestType.FLOW_DEFINITIVE_CANCEL}:
            if status != 'Finalizado' and FlowRequest.objects.filter(
                lot=lot,
                flow_request_type=FlowRequestType.FLOW_DEFINITIVE_CANCEL
            ).exclude(status='Finalizado').exclude(pk=instance_pk).exists():
                raise serializers.ValidationError(
                    "El lote elegido cuenta con una solicitud de cancelación definitiva de caudal en curso."
                )

    def _validate_cancellation_flow_not_editable(self, flow_request_type, requested_flow):
        """Valida que no se permita modificar el caudal solicitado en una solicitud de cancelación."""
        if flow_request_type in {FlowRequestType.FLOW_TEMPORARY_CANCEL, FlowRequestType.FLOW_DEFINITIVE_CANCEL}:
            if requested_flow:
                raise serializers.ValidationError(
                    "No se puede modificar el caudal solicitado en una solicitud de cancelación de caudal."
                )

    def _validate_pending_activation_request(self, flow_request_type, lot, instance_pk):
        """Valida que no existan solicitudes pendientes de activación para el mismo lote."""
        if flow_request_type == FlowRequestType.FLOW_ACTIVATION:
            if FlowRequest.objects.filter(
                lot=lot,
                status='Pendiente'
            ).exclude(pk=instance_pk).exists():
                raise serializers.ValidationError(
                    "El lote elegido cuenta con una solicitud de activación de caudal en curso."
                )

    def _validate_actual_flow_activated(self, flow_request_type, device):
        """Valida que el caudal actual del lote esté activo."""
        if flow_request_type == FlowRequestType.FLOW_ACTIVATION:
            if device and device.actual_flow > 0:
                raise serializers.ValidationError(
                    "El caudal del lote ya está activo. No es necesario solicitar activación."
                )

    def _validate_approved_transition(self):
        """Valida que no se rechace una solicitud una vez fue aprobada."""
        if self.instance and self.instance.pk:
            old = FlowRequest.objects.get(pk=self.instance.pk)
            if old.is_approved and self.instance.is_approved != old.is_approved:
                raise serializers.ValidationError(
                    "Si la solicitud ya fue aprobada, no se puede revertir dicha acción."
                )

    def _validate_observations(self, flow_request_type, observations):
        if flow_request_type in {FlowRequestType.FLOW_TEMPORARY_CANCEL, FlowRequestType.FLOW_DEFINITIVE_CANCEL, FlowRequestType.FLOW_ACTIVATION}:
            if not observations:
                raise serializers.ValidationError("El campo 'observations' es obligatorio.")
            if flow_request_type in {FlowRequestType.FLOW_TEMPORARY_CANCEL, FlowRequestType.FLOW_DEFINITIVE_CANCEL}:
                if len(observations) < 5 and len(observations) > 200:
                    raise serializers.ValidationError("Las observaciones deben estar entre los 5 y 200 caracteres.")
            elif flow_request_type == FlowRequestType.FLOW_ACTIVATION:
                if len(observations) > 300:
                    raise serializers.ValidationError("Las observaciones no pueden xceder los 300 caracteres.")

    def validate_requires_delegation(self, value):
        if self.flow_request_type != FlowRequestType.FLOW_DEFINITIVE_CANCEL:
            if value == True:
                raise serializers.ValidationError("Solo la solicitud de cancelación definitiva de caudal requiere ser delegada.")

    def validate(self, attrs):
        user = self.context['request'].user
        lot = attrs.get('lot')
        flow_request_type = attrs.get('flow_request_type')
        requested_flow = attrs.get('requested_flow')
        observations = attrs.get('observations')
        status = getattr(self.instance, 'status', 'Pendiente')
        instance_pk = getattr(self.instance, 'pk', None)

        if not lot:
            raise serializers.ValidationError({"lot": "El lote es obligatorio para la solicitud."})

        device = self._get_device_valve4(lot)

        self._validate_owner(lot, user)
        self._validate_requested_flow(flow_request_type, requested_flow)
        self._check_caudal_flow_inactive(device, flow_request_type, status)

        if flow_request_type == FlowRequestType.FLOW_CHANGE:
            self._validate_pending_change_request(lot, instance_pk)
            self._validate_pending_cancel_request(lot)
            self._validate_requested_flow_uniqueness(flow_request_type, device, requested_flow, status)

        self._validate_pending_temporary_request(flow_request_type, lot, instance_pk)
        self._validate_pending_definitive_request(flow_request_type, lot, status, instance_pk)
        self._validate_cancellation_flow_not_editable(flow_request_type, requested_flow)
        self._validate_pending_activation_request(flow_request_type, lot, instance_pk)
        self._validate_actual_flow_activated(flow_request_type, device)
        self._validate_approved_transition()
        self._validate_observations(flow_request_type, observations)

        return attrs

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['type'] = 'Solicitud'
        return super().create(validated_data)