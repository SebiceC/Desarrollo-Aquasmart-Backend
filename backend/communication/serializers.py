from django.utils import timezone
from rest_framework import serializers
from iot.models import IoTDevice, VALVE_4_ID

class BaseFlowRequestSerializer(serializers.ModelSerializer):
    """Serializer base para solicitudes de caudal."""

    class Meta:
        fields = '__all__'
        extra_kwargs = {
            'lot': {'required': True, 'allow_null': False}
        }

    def validate_lot(self, value):
        if not value:
            raise serializers.ValidationError("El lote es obligatorio para la solicitud.")
        return value
    

    def validate(self, attrs):
        lot = attrs.get('lot')
        if not lot:
            raise serializers.ValidationError({"lot": "El lote es obligatorio para la solicitud."})

        # Validar que el lote tenga una válvula 4"
        device = IoTDevice.objects.filter(id_lot=lot, device_type__device_id=VALVE_4_ID).first()
        if not device:
            raise serializers.ValidationError({"device_type": "El lote no tiene una válvula 4\" asociada."})

        # Asignar plot automáticamente
        if hasattr(lot, 'plot'):
            attrs['plot'] = lot.plot

        return attrs
    
    def create(self, validated_data):
        # Asignar usuario automáticamente
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BaseRequestStatusSerializer(serializers.ModelSerializer):
    """Serializer base para actualizar el estado de solicitudes de caudal."""

    class Meta:
        fields = ['status', 'reviewed_at']
        read_only_fields = ['reviewed_at']

    def validate_lot(self, value):
        if not value:
            raise serializers.ValidationError("El lote es obligatorio para la solicitud.")
        return value

    def validate_status(self, value):
        if value not in ['aprobada', 'rechazada']:
            raise serializers.ValidationError("Solo se permite aprobar o rechazar la solicitud.")
        return value
    
    def validate(self, attrs):
        lot = attrs.get('lot')
        if lot and hasattr(lot, 'plot'):
            attrs['plot'] = lot.plot
        return super().validate(attrs)
    
    # Asignar el usuario (solicitante) automáticamente
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if instance.status in ['aprobada', 'rechazada']:
            raise serializers.ValidationError(
                {"status": "No se puede cambiar el estado una vez revisada la solicitud."}
            )
        validated_data['reviewed_at'] = timezone.now()
        return super().update(instance, validated_data)