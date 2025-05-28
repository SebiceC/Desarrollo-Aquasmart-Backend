from rest_framework import serializers, viewsets
from .models import FlowMeasurement, FlowMeasurementPredio, FlowMeasurementLote,FlowInconsistency
from iot.models import IoTDevice

class FlowMeasurementSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source="device.name", read_only=True)  # Nombre del dispositivo
    device_type = serializers.CharField(source="device.device_type.name", read_only=True)  # Tipo de dispositivo

    class Meta:
        model = FlowMeasurement
        fields = ['id', 'device', 'device_name', 'device_type', 'timestamp', 'flow_rate']
        read_only_fields = ['timestamp']

class FlowMeasurementPredioSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowMeasurementPredio
        fields = '__all__'



class FlowMeasurementLoteSerializer(serializers.ModelSerializer):
    device = serializers.SlugRelatedField(
        slug_field='iot_id',
        queryset=IoTDevice.objects.all()
    )

    class Meta:
        model = FlowMeasurementLote
        fields = ['device', 'flow_rate', 'timestamp']

    def create(self, validated_data):
        device = validated_data.get('device')
        lote = getattr(device, 'id_lot', None)  # <- Aquí usas el nombre correcto del campo en IoTDevice

        if lote is None:
            raise serializers.ValidationError("El dispositivo no está vinculado a ningún lote")

        validated_data['lot'] = lote  # asignas el lote al campo 'lot' de FlowMeasurementLote
        return super().create(validated_data)

    
class FlowInconsistencySerializer(serializers.ModelSerializer):
    class Meta:
        model = FlowInconsistency
        fields = '__all__'