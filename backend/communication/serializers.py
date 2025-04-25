from django.utils import timezone
from rest_framework import serializers
from .request.models import BaseFlowRequest
from iot.models import IoTDevice, VALVE_4_ID

class BaseFlowRequestSerializer(serializers.ModelSerializer):
    """Serializer base para solicitudes de caudal."""

    class Meta:
        model = BaseFlowRequest
        fields = '__all__'
        read_only_fields = 'status'
        extra_kwargs = {
        'lot': {'required': True, 'allow_null': False}
    }

    def validate_lot(self, value):
        # Validar que el lote no tenga una válvula de 4" asociada
        valve = IoTDevice.objects.filter(id_lot=value, device_type__device_id=VALVE_4_ID).first()
        if not valve:
            raise serializers.ValidationError("El lote no tiene una válvula 4\" asociada.")
        return value

    def validate_requested_flow(self, value):
        # Validar que el caudal solicitado sea válido
        if value is None or value <= 0:
            raise serializers.ValidationError("Debe ingresar un caudal válido en L/s.")
        # Validar rango de caudal solicitado
        if value < 1 or value >= 11.7:
            raise serializers.ValidationError("El caudal solicitado debe estar dentro del rango de 1 L/seg a 11.7 L/seg.")
        return value

    def _validate_requested_flow_uniqueness(self, lot, requested_flow):
        # Validar caudal igual al actual
        device = IoTDevice.objects.filter(id_lot=lot, device_type__device_id=VALVE_4_ID).first()
        if requested_flow is not None and device and device.actual_flow == requested_flow:
            raise serializers.ValidationError(
                {"requested_flow": "Ya tienes un caudal activo con ese valor. Debes solicitar un valor diferente."}
            )

    # def _validate_pending_request(self, lot):
    #     ''' Valida que no existan solicitudes pendientes para el mismo lote '''
    #     model = self.Meta.model
    #     if model.objects.filter(lot=lot, status='pendiente').exists():
    #         raise serializers.ValidationError(
    #             {"error": "Ya existe una solicitud (cambio, cancelación o activación) pendiente para este lote. "
    #             "Espere a que el administrador apruebe o rechace la solicitud pendiente, e inténtelo más tarde."}
    #         )

    def validate(self, attrs):
        user = self.context['request'].user
        lot = attrs.get('lot')
        # requested_flow = attrs.get('requested_flow')

        # Validar que el usuario (solicitante) sea dueño del predio
        if user != lot.plot.owner:
            raise serializers.ValidationError(
                {"owner": "Solo el dueño del predio puede realizar una solicitud para el caudal de este lote."}
            )

        # elif lot:
        #     self._validate_pending_request(lot)
        #     if requested_flow is not None:
        #         self._validate_requested_flow_uniqueness(lot, requested_flow)

        return attrs

    def create(self, validated_data):
        # Asignar el usuario (solicitante) automáticamente
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Verificar si solicita un 'status' que ya fue asignada
        if instance.status == validated_data['status']:
            raise serializers.ValidationError(
                {"status": f"La solicitud ya fue {validated_data['status']}."}
            )
        # Impedir que se pueda cambiar el estado una vez revisada la solicitud
        elif instance.status in ['aprobada', 'rechazada']:
            raise serializers.ValidationError(
                {"status": "No se puede cambiar el estado una vez revisada la solicitud."}
            )

        validated_data['reviewed_at'] = timezone.now()


class BaseRequestStatusSerializer(serializers.ModelSerializer):
    """Serializer base para actualizar el estado de solicitudes de caudal."""

    class Meta:
        model = BaseFlowRequest
        fields = ['status', 'reviewed_at']
        read_only_fields = ['reviewed_at']

    def validate_lot(self, value):
        # Validar que el lote no tenga una válvula de 4" asociada
        valve = IoTDevice.objects.filter(id_lot=value, device_type__device_id=VALVE_4_ID).first()
        if not valve:
            raise serializers.ValidationError("El lote no tiene una válvula 4\" asociada.")
        return value

    def validate_status(self, value):
        if value not in ['aprobada', 'rechazada']:
            raise serializers.ValidationError("Solo se permite aprobar o rechazar la solicitud.")
        return value

    def create(self, validated_data):
        # Asignar el usuario (solicitante) automáticamente
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Verificar si solicita un 'status' que ya fue asignada
        if instance.status == validated_data['status']:
            raise serializers.ValidationError(
                {"status": f"La solicitud ya fue {validated_data['status']}."}
            )
        # Impedir que se pueda cambiar el estado una vez revisada la solicitud
        elif instance.status in ['aprobada', 'rechazada']:
            raise serializers.ValidationError(
                {"status": "No se puede cambiar el estado una vez revisada la solicitud."}
            )

        validated_data['reviewed_at'] = timezone.now()

        return super().update(instance, validated_data)