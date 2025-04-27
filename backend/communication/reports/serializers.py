from communication.serializers import BaseFlowRequestSerializer, BaseRequestStatusSerializer
from .models import WaterSupplyFailureReport
from rest_framework import serializers

class WaterSupplyFailureReportSerializer(BaseFlowRequestSerializer):
    """Serializer para crear reportes de fallos en suministro de agua."""

    class Meta(BaseFlowRequestSerializer.Meta):
        model = WaterSupplyFailureReport
        fields = '__all__'
        read_only_fields = ['user', 'plot', 'status', 'created_at', 'reviewed_at']

    def validate_observations(self, value):
        if not value or len(value) > 200:
            raise serializers.ValidationError("Las observaciones son obligatorias y no pueden exceder los 200 caracteres.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        return attrs

class WaterSupplyFailureReportStatusSerializer(BaseRequestStatusSerializer):
    """Serializer para actualizar el estado de un reporte de fallo de suministro de agua."""

    class Meta(BaseRequestStatusSerializer.Meta):
        model = WaterSupplyFailureReport
