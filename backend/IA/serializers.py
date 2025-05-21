
from rest_framework import serializers
from .models import ClimateRecord, ConsuptionPredictionLot

class ClimateRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClimateRecord
        fields = '__all__'
        read_only_fields = ['luminiscencia', 'final_date']  # Estos campos se calculan automáticamente

class ConsuptionPredictionLotSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    plot = serializers.SerializerMethodField()
    class Meta:
        model = ConsuptionPredictionLot
        fields = [
            'id',
            'lot',
            'plot',            
            'owner',
            'period_time',
            'date_prediction',
            'consumption_prediction',
            'code_prediction',
            'created_at',
            'final_date'
        ]
        read_only_fields = ['created_at', 'final_date','consumption_prediction','code_prediction', 'plot','owner','date_prediction',]
    def get_plot(self, obj):
        # Verifica si obj es una instancia de modelo o un diccionario
        if isinstance(obj, ConsuptionPredictionLot):
            return obj.lot.plot.id_plot
        elif isinstance(obj, dict):
            # Cuando obj es un diccionario (de validated_data), 'lot' será la instancia de Lot
            lot_instance = obj.get('lot')
            if lot_instance and hasattr(lot_instance, 'plot') and lot_instance.plot:
                return lot_instance.plot.id_plot
        return None # O maneja según sea apropiado si lot/plot no existen

    def get_owner(self, obj):
        owner_obj = None
        if isinstance(obj, ConsuptionPredictionLot):
            if hasattr(obj, 'lot') and obj.lot and hasattr(obj.lot, 'plot') and obj.lot.plot and hasattr(obj.lot.plot, 'owner'):
                owner_obj = obj.lot.plot.owner
        elif isinstance(obj, dict):
            lot_instance = obj.get('lot')
            if lot_instance and hasattr(lot_instance, 'plot') and lot_instance.plot and hasattr(lot_instance.plot, 'owner'):
                owner_obj = lot_instance.plot.owner

        if owner_obj:
            # Combina first_name y last_name para obtener el nombre completo
            # Puedes usar .strip() para eliminar espacios extra si un nombre está vacío
            full_name = f"{owner_obj.first_name} {owner_obj.last_name}".strip()
            return full_name if full_name else owner_obj.username # Fallback a username si el nombre completo está vacío
        return None # O un valor por defecto si no se encuentra el propietario

    def validate_period_time(self, value):
        if value not in ['1', '3', '6']:
            raise serializers.ValidationError("El tiempo debe ser 1, 3 o 6 meses.")
        return value
    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        lot = validated_data['lot']
        

        return ConsuptionPredictionLot.objects.create(
            user=user,
            lot=lot,            
            **validated_data
        )
        