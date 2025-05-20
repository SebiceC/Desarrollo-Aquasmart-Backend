from rest_framework import serializers
from .models import TypeReport, FailureReport
from iot.models import IoTDevice, VALVE_4_ID

class FailureReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FailureReport
        fields = [
            'id',
            'type',
            'created_by',
            'lot',
            'plot',
            'failure_type',
            'status',
            'observations',
            'created_at',
            'finalized_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'finalized_at','created_by']
        extra_kwargs = {
            'observations': {'required': True, 'allow_null': False},
        }

    def validate(self, data):
        user = self.context['request'].user
        lot = data.get('lot')
        plot = data.get('plot')
        failure_type = data.get('failure_type')
        status = data.get('status')
        observations = data.get('observations')
        print(observations)

        # Validaciones heredadas de BaseRequestReport
        if lot:
            # Validar que el lote esté activo
            if lot.is_activate != True:
                raise serializers.ValidationError("No se puede realizar una solicitud o un reporte de un lote inhabilitado.")
            
            # Validar válvula 4"
            device = IoTDevice.objects.filter(id_lot=lot, device_type__device_id=VALVE_4_ID).first()
            if not device:
                raise serializers.ValidationError("El lote no tiene una válvula 4\" asociada.")

        # Validaciones de estado
        instance = self.instance
        if instance and instance.status == 'Finalizado' and status != instance.status:
            raise serializers.ValidationError("No se puede cambiar el estado una vez que el reporte ha sido finalizado.")

        # Validaciones específicas de WATER_SUPPLY_FAILURE
        if failure_type == TypeReport.WATER_SUPPLY_FAILURE:
            if not lot and not plot:
                raise serializers.ValidationError("Debe proporcionar al menos un lote o un predio para este tipo de reporte.")

        # Validaciones específicas de APPLICATION_FAILURE
        if failure_type == TypeReport.APPLICATION_FAILURE:
            if len(observations) < 10 or len(observations) > 200:
                raise serializers.ValidationError("Las observaciones deben estar entre los 10 y 200 caracteres.")

        # Validar predio activo
        if plot and not plot.is_activate:
            raise serializers.ValidationError("No se puede realizar un reporte de un predio inhabilitado.")

        # Validar reportes pendientes
        if plot or lot:
            plot_pending = FailureReport.objects.filter(plot=plot).exclude(status='Finalizado')
            lot_pending = FailureReport.objects.filter(lot=lot).exclude(status='Finalizado')

            if instance:
                plot_pending = plot_pending.exclude(pk=instance.pk)
                lot_pending = lot_pending.exclude(pk=instance.pk)

            if lot_pending.exists() or (plot_pending.exists() and lot_pending.exists()):
                raise serializers.ValidationError(
                    "No se puede crear el reporte porque ya existe uno pendiente para el predio o el lote seleccionado."
                )

        # Validación si se envían ambos
        if lot and plot:
            if lot.plot != plot:
                raise serializers.ValidationError("El lote no pertenece al predio especificado.")

        # Validar propietario
        if lot and lot.plot and lot.plot.owner != user:
            raise serializers.ValidationError("Solo el dueño del predio puede crear un reporte para este lote.")
        if plot and plot.owner != user:
            raise serializers.ValidationError("Solo el dueño del predio puede crear un reporte para este predio.")

        # Asignar predio desde lote
        if lot and hasattr(lot, 'plot'):
            data['plot'] = lot.plot

        return data   
            
    def create(self, validated_data):
        validated_data['type'] = 'Reporte'
        validated_data['created_by'] = self.context['request'].user
        instance = FailureReport(**validated_data)
        instance.save()
        return instance
