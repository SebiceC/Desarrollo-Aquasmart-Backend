from rest_framework import serializers
from .models import Plot,Lot,SoilType
from users.models import CustomUser
from rest_framework.exceptions import NotFound
class PlotSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        error_messages={'does_not_exist': "El usuario asignado no está registrado"}
    )

    class Meta:
        model = Plot
        fields = ['id_plot', 'owner', 'plot_name', 'latitud', 'longitud', 'plot_extension', 'registration_date','is_activate']
        read_only_fields = ['id_plot', 'registration_date','is_activate']

    
    def validate(self, data):
        """Validación personalizada para evitar duplicados en la georeferenciación."""
        latitud = data.get('latitud')
        longitud = data.get('longitud')

           # Obtener la instancia actual si está disponible
        instance = self.instance  

        # Verificar si la geolocalización ya está asignada a otro predio (excluyendo el actual)
        if Plot.objects.exclude(id_plot=instance.id_plot if instance else None).filter(latitud=latitud, longitud=longitud).exists():
            raise serializers.ValidationError("La georeferenciación ya está asignada a otro predio.")

        return data
    
class LotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lot
        fields = ['id_lot', 'plot', 'crop_type', 'crop_variety', 'soil_type', 'is_activate','registration_date']
        read_only_fields = ['id_lot']  # id_lot se genera automáticamente, no debe ser enviado por el usuario

    def validate_plot(self, value):
        """
        Validación personalizada para el campo 'plot'.
        Asegura que el predio exista en la base de datos.
        """
        if not Plot.objects.filter(id_plot=value.id_plot).exists():
            raise serializers.ValidationError("El predio no existe.")
        return value

    def validate_soil_type(self, value):
        """
        Validación personalizada para el campo 'soil_type'.
        Asegura que el tipo de suelo exista en la base de datos.
        """
        if not SoilType.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("El tipo de suelo no existe.")
        return value

class LotActivationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lot
        fields = ['is_activate']  # Solo permitimos actualizar este campo    

class PlotDetailSerializer(serializers.ModelSerializer):
    lotes = LotSerializer(many=True, read_only=True)  # Incluye los lotes relacionados

    class Meta:
        model = Plot
        fields = [
            'id_plot', 'owner', 'plot_name', 'latitud', 'longitud', 'plot_extension',
            'registration_date', 'is_activate', 'lotes'
        ]        
        