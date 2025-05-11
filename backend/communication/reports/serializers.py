from rest_framework import serializers
from .models import TypeReport, FailureReport

class FailureReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FailureReport
        fields = [
            'id',
            'type',
            'created_by',
            'lot',
            'plot',  # opcional
            'failure_type',
            'status',
            'observations',
            'created_at',
            'finalized_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'finalized_at','created_by']
        

    def validate(self, data):
        user = self.context['request'].user
        lot = data.get('lot')
        plot = data.get('plot')
        failure_type = data.get('failure_type')

        if failure_type == TypeReport.WATER_SUPPLY_FAILURE:
         if not lot and not plot:
             raise serializers.ValidationError("Debe proporcionar al menos un lote o un predio para este tipo de reporte.")

        # Validación si solo se envía plot
         if plot and not lot:
                if plot.owner != user:
                   raise serializers.ValidationError("Solo el dueño del predio puede hacer el reporte para este predio.")
                if not plot.is_activate:
                    raise serializers.ValidationError("No se puede reportar un predio inhabilitado.")
                data['lot'] = None  # dejar explícito que no hay lote

        # Validación si solo se envía lot
         elif lot and not plot:
            if not hasattr(lot, 'plot') or not lot.plot:
                raise serializers.ValidationError("El lote no está asociado a ningún predio.")
            if lot.plot.owner != user:
                raise serializers.ValidationError("Solo el dueño del predio puede hacer el reporte para este lote.")
            if not lot.plot.is_activate:
                raise serializers.ValidationError("No se puede reportar un lote de un predio inhabilitado.")
            data['plot'] = lot.plot  # autocompletar plot

        # Validación si se envían ambos
         elif lot and plot:
            if lot.plot != plot:
                raise serializers.ValidationError("El lote no pertenece al predio especificado.")
            if plot.owner != user:
                raise serializers.ValidationError("Solo el dueño del predio puede hacer el reporte.")
            if not plot.is_activate:
                raise serializers.ValidationError("No se puede reportar un predio inhabilitado.")

        return data   
            
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        instance = FailureReport(**validated_data)
        instance.save()  # El .save() ya llama a full_clean y asigna el ID
        return instance
