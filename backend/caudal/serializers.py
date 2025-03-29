from rest_framework import serializers, viewsets
from .models import (
    FlowMeasurement,
    FlowMeasurementPredio,
    FlowMeasurementLote,
    FlowInconsistency,
)


class FlowMeasurementSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(
        source="device.name", read_only=True
    )  # Nombre del dispositivo
    device_type = serializers.CharField(
        source="device.device_type.name", read_only=True
    )  # Tipo de dispositivo

    class Meta:
        model = FlowMeasurement
        fields = [
            "id",
            "device",
            "device_name",
            "device_type",
            "timestamp",
            "flow_rate",
        ]
        read_only_fields = ["timestamp"]


class FlowMeasurementPredioSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowMeasurementPredio
        fields = "__all__"


class FlowMeasurementLoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowMeasurementLote
        fields = "__all__"


class FlowInconsistencySerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowInconsistency
        fields = "__all__"
