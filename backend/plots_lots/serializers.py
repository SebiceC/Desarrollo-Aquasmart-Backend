from rest_framework import serializers
from .models import Plot, Lot, SoilType, CropType
from users.models import CustomUser

class PlotSerializer(serializers.ModelSerializer):
    """Serializer base para predios con campos básicos."""
    owner = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        error_messages={'does_not_exist': "El usuario asignado no está registrado"}
    )

    class Meta:
        model = Plot
        fields = ['id_plot', 'owner', 'plot_name', 'latitud', 'longitud', 'plot_extension', 'registration_date', 'is_activate']
        read_only_fields = ['id_plot', 'registration_date']

    def validate(self, data):
        """Validación personalizada para evitar duplicados en la georeferenciación."""
        latitud = data.get('latitud')
        longitud = data.get('longitud')

        instance = self.instance
        if Plot.objects.exclude(id_plot=instance.id_plot if instance else None).filter(latitud=latitud, longitud=longitud).exists():
            raise serializers.ValidationError("La georeferenciación ya está asignada a otro predio.")
        return data

class LotSerializer(serializers.ModelSerializer):
    """Serializer base para lotes con campos básicos."""
    plot = serializers.PrimaryKeyRelatedField(
        queryset=Plot.objects.all(),
        error_messages={
            'does_not_exist': 'El predio asignado no está registrado.',
            'incorrect_type': 'Dato inválido para el predio.'
        }
    )

    def validate_is_activate(self, value):
        ''' Valida que no se pueda activar un lote si su predio está desactivado '''
        if self.plot.is_activate == False:
            if value == True:
                raise serializers.ValidationError("No se puede habilitar el lote si el predio al cual pertenece está deshabilitado.")

    class Meta:
        model = Lot
        fields = ['id_lot', 'plot', 'crop_name', 'crop_type', 'crop_variety', 'soil_type', 'is_activate', 'registration_date']
        read_only_fields = ['id_lot', 'registration_date']

    def validate_plot(self, value):
        """Valida que el predio esté activo."""
        if not value.is_activate:
            raise serializers.ValidationError("El predio asociado se encuentra inactivo.")
        return value

    def validate_soil_type(self, value):
        """Valida que el tipo de suelo exista."""
        if not SoilType.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("El tipo de suelo no existe.")
        return value

class PlotDetailSerializer(PlotSerializer):
    """Serializer extendido para ver detalles de predios, incluyendo sus lotes."""
    lotes = LotSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)

    class Meta(PlotSerializer.Meta):
        fields = PlotSerializer.Meta.fields + ['lotes', 'owner_name']

class LotDetailSerializer(LotSerializer):
    """Serializer extendido para ver detalles de lotes, incluyendo información del predio."""
    plot_name = serializers.CharField(source='plot.plot_name', read_only=True)
    plot_owner = serializers.CharField(source='plot.owner.get_full_name', read_only=True)
    soil_type_name = serializers.CharField(source='soil_type.name', read_only=True)

    class Meta(LotSerializer.Meta):
        fields = LotSerializer.Meta.fields + ['plot_name', 'plot_owner', 'soil_type_name', 'crop_name']

class SoilTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoilType
        fields = '__all__'

# Serializar para el tipo de cultivo
class CropTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CropType
        fields = '__all__'