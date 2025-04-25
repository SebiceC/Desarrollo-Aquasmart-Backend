from django.utils import timezone
from rest_framework import serializers
from .models import FlowChangeRequest, FlowCancelRequest, FlowActivationRequest
from ..serializers import BaseFlowRequestSerializer, BaseRequestStatusSerializer

class FlowChangeRequestSerializer(BaseFlowRequestSerializer):
    """Serializer para crear solicitudes de cambio de caudal."""

    class Meta (BaseFlowRequestSerializer.Meta):
        model = FlowChangeRequest
        fields = '__all__'
        read_only_fields = ['user', 'device', 'plot', 'status', 'created_at', 'reviewed_at']


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
        cancel_type = attrs.get('cancel_type')

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


class FlowActivationRequestStatusSerializer(BaseRequestStatusSerializer):
    """Serializer para actualizar el estado de la solicitud de activación de caudal."""

    class Meta(BaseRequestStatusSerializer.Meta):
        model = FlowActivationRequest