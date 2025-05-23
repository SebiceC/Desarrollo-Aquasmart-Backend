from django.utils import timezone
from rest_framework import serializers
from .models import FlowChangeRequest, FlowCancelRequest
from ..serializers import BaseFlowRequestSerializer, BaseRequestStatusSerializer
from iot.models import IoTDevice, VALVE_4_ID

class FlowChangeRequestSerializer(BaseFlowRequestSerializer):
    """Serializer para crear solicitudes de cambio de caudal."""

    class Meta (BaseFlowRequestSerializer.Meta):
        model = FlowChangeRequest
        fields = '__all__'
        read_only_fields = ['user', 'device', 'plot', 'status', 'created_at', 'reviewed_at']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        lot = attrs.get('lot')
        requested_flow = attrs.get('requested_flow')
        user = self.context['request'].user

        # Validar dueño del predio
        if lot and lot.plot.owner != user:
            raise serializers.ValidationError("Solo el dueño del predio puede solicitar el cambio de caudal para este lote.")

        # Buscar el dispositivo IoT de tipo válvula 4" asociado al lote
        device = IoTDevice.objects.filter(id_lot=lot, device_type__device_id=VALVE_4_ID).first()
        if not device:
            raise serializers.ValidationError("El lote no tiene una válvula 4\" asociada.")

        # Validar caudal igual al actual
        if requested_flow is not None and device.actual_flow == requested_flow:
            raise serializers.ValidationError(
                {"requested_flow": "Ya tienes un caudal activo con ese valor. Debes solicitar un valor diferente."}
            )

        attrs['device'] = device
        return attrs


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

    def validate(self, attrs):
        attrs = super().validate(attrs)
        lot = attrs.get('lot')
        user = self.context['request'].user
        cancel_type = attrs.get('cancel_type')

        # Validar dueño del predio
        if lot.plot.owner != user:
            raise serializers.ValidationError(
                {"owner": "Solo el dueño del predio puede solicitar la cancelación para este lote."}
            )

        # Restricción: No permitir temporal si ya existe definitiva pendiente/aprobada
        if cancel_type == 'temporal':
            if FlowCancelRequest.objects.filter(
                lot=lot, cancel_type='definitiva', status__in=['pendiente', 'aprobada']
            ).exists():
                raise serializers.ValidationError(
                    {"error": "No puedes solicitar una cancelación temporal si ya existe una definitiva pendiente o aprobada para este lote."}
                )

        return attrs


class FlowCancelRequestStatusSerializer(BaseRequestStatusSerializer):
    """Serializer para actualizar el estado de la solicitud de cancelación de caudal."""

    class Meta(BaseRequestStatusSerializer.Meta):
        model = FlowCancelRequest