from rest_framework import serializers
from .models import FlowChangeRequest, FlowCancelRequest, FlowActivationRequest
from iot.models import IoTDevice, VALVE_4_ID
from ..serializers import BaseFlowRequestSerializer, BaseRequestStatusSerializer

class FlowChangeRequestSerializer(BaseFlowRequestSerializer):
    """Serializer para crear solicitudes de cambio de caudal."""

    class Meta (BaseFlowRequestSerializer.Meta):
        model = FlowChangeRequest
        fields = '__all__'
        read_only_fields = ['user', 'device', 'plot', 'status', 'created_at', 'reviewed_at']

    def validate_lot(self, value):
        value = super().validate_lot(value)
        device = IoTDevice.objects.filter(id_lot=value, device_type__device_id=VALVE_4_ID).first()
        if device.actual_flow == 0 or device.actual_flow == None:
            raise serializers.ValidationError("El caudal del lote está inactivo. Debes solicitar activarlo primero.")
        return value

    def _validate_pending_change_request(self, lot):
        ''' Valida que no existan solicitudes de cambio de caudal pendientes para el lote. '''
        instance_pk = getattr(self.instance, 'pk', None)
        if FlowChangeRequest.objects.filter(lot=lot, status='pendiente').exclude(pk=instance_pk).exists():
            raise serializers.ValidationError(
                {"error": "El lote elegido ya cuenta con una solicitud de cambio de caudal en curso."}
            )

    def _validate_requested_flow_uniqueness(self, lot, requested_flow):
        ''' Valida que el caudal solicitado no sea igual al actual '''
        device = IoTDevice.objects.filter(id_lot=lot, device_type__device_id=VALVE_4_ID).first()
        if requested_flow is not None and device and device.actual_flow == requested_flow:
            raise serializers.ValidationError(
                {"error": "El caudal solicitado es el mismo que se encuentra disponible. Intente con un valor diferente."}
            )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        lot = attrs.get('lot')
        requested_flow = attrs.get('requested_flow')

        # Ejecutar validadores personalizados solo si los datos están presentes
        if lot:
            self._validate_pending_change_request(lot)
            if requested_flow is not None:
                self._validate_requested_flow_uniqueness(lot, requested_flow)

        return attrs

    def create(self, validated_data):
        # Si es definitiva, rechaza la temporal pendiente ANTES de crear la definitiva
        if validated_data.get('cancel_type') == 'definitiva':
            lot = validated_data.get('lot')
            temporal = FlowCancelRequest.objects.filter(
                lot=lot, status='pendiente', cancel_type='temporal'
            ).first()
            if temporal:
                temporal.status = 'rechazada'
                temporal.observations = 'Rechazada de forma automática: El usuario ha solicitado una cancelación definitiva.'
                temporal.save()
        # Ahora sí, crea la definitiva normalmente
        return super().create(validated_data)


class FlowChangeRequestStatusSerializer(BaseRequestStatusSerializer):
    """Serializer para actualizar el estado de la solicitud de cambio de caudal."""

    class Meta(BaseRequestStatusSerializer.Meta):
        model = FlowChangeRequest


class FlowCancelRequestSerializer(BaseFlowRequestSerializer):
    """Serializer para crear solicitudes de cancelación de caudal."""
    class Meta(BaseFlowRequestSerializer.Meta):
        model = FlowCancelRequest
        fields = '__all__'
        read_only_fields = ['user', 'plot', 'status', 'created_at', 'reviewed_at']

    # Validar observaciones
    def validate_observations(self, value):
        if not value or not (5 <= len(value) <= 200):
            raise serializers.ValidationError("Las observaciones deben tener entre 5 y 200 caracteres.")
        return value

    def _validate_pending_temporary_request(self, cancel_type, lot):
        ''' Valida que no existan solicitudes pendientes de cancelación temporal para el mismo lote. '''
        instance_pk = getattr(self.instance, 'pk', None)
        if cancel_type != 'definitiva' and FlowCancelRequest.objects.filter(lot=lot, status='pendiente', cancel_type='temporal').exclude(pk=instance_pk).exists():
            raise serializers.ValidationError(
                {"error": "El lote elegido cuenta con una solicitud de cancelación temporal de caudal en curso."}
            )

    def _validate_pending_definitive_request(self, lot):
        ''' Valida que no existan solicitudes pendientes de cancelación definitiva para el mismo lote. '''
        instance_pk = getattr(self.instance, 'pk', None)
        if FlowCancelRequest.objects.filter(lot=lot, status='pendiente', cancel_type='definitiva').exclude(pk=instance_pk).exists():
            raise serializers.ValidationError(
                {"error": "El lote elegido cuenta con una solicitud de cancelación definitiva de caudal en curso."}
            )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        lot = attrs.get('lot')
        cancel_type = attrs.get('cancel_type')

        if lot:
            self._validate_pending_temporary_request(cancel_type, lot)
            self._validate_pending_definitive_request(lot)

        if cancel_type == 'temporal':
            # No permitir temporal si ya existe definitiva pendiente
            if FlowCancelRequest.objects.filter(
                lot=lot, cancel_type='definitiva', status='pendiente'
            ).exists():
                raise serializers.ValidationError(
                    {"error": "No puedes solicitar una cancelación temporal si ya existe una definitiva pendiente para este lote."}
                )
            # No permitir dos temporales pendientes
            if FlowCancelRequest.objects.filter(
                lot=lot, cancel_type='temporal', status='pendiente'
            ).exists():
                raise serializers.ValidationError(
                    {"error": "No puedes solicitar una cancelación temporal si ya existe una pendiente para este lote."}
                )
        elif cancel_type == 'definitiva':
            # No permitir definitiva si ya existe definitiva pendiente
            if FlowCancelRequest.objects.filter(
                lot=lot, cancel_type='definitiva', status='pendiente'
            ).exists():
                raise serializers.ValidationError(
                    {"error": "No puedes solicitar una cancelación definitiva si ya existe una definitiva pendiente para este lote."}
                )

        return attrs


class FlowCancelRequestStatusSerializer(BaseRequestStatusSerializer):
    """Serializer para actualizar el estado de la solicitud de cancelación de caudal."""

    class Meta(BaseRequestStatusSerializer.Meta):
        model = FlowCancelRequest


class FlowActivationRequestSerializer(BaseFlowRequestSerializer):
    """Serializer para crear solicitudes de activación de caudal."""

    class Meta(BaseFlowRequestSerializer.Meta):
        model = FlowActivationRequest
        fields = '__all__'
        read_only_fields = ['user', 'plot', 'status', 'created_at', 'reviewed_at']

    def _validate_pending_activation_request(self, lot):
        ''' Valida que no existan solicitudes de activación de caudal pendientes para el lote. '''
        instance_pk = getattr(self.instance, 'pk', None)
        if FlowActivationRequest.objects.filter(lot=lot, status='pendiente').exclude(pk=instance_pk).exists():
            raise serializers.ValidationError(
                {"error": "El lote elegido ya cuenta con una solicitud de activación de caudal en curso."}
            )

    def _validate_actual_flow_activated(self, lot):
        ''' Valida que el caudal actual del lote esté activo '''
        device = IoTDevice.objects.filter(id_lot=lot, device_type__device_id=VALVE_4_ID).first()
        if device.actual_flow > 0:
            raise serializers.ValidationError(
                {"error": "El caudal del lote ya está activo. No es necesario solicitar activación."}
            )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        lot = attrs.get('lot')

        if lot:
            self._validate_pending_activation_request(lot)
            self._validate_actual_flow_activated(lot)
        
        return attrs


class FlowActivationRequestStatusSerializer(BaseRequestStatusSerializer):
    """Serializer para actualizar el estado de la solicitud de activación de caudal."""

    class Meta(BaseRequestStatusSerializer.Meta):
        model = FlowActivationRequest